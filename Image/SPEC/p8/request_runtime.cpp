#include "request_runtime.hpp"

#include <algorithm>
#include <condition_variable>
#include <limits>
#include <mutex>
#include <new>
#include <stop_token>
#include <utility>

namespace agi::image::p8 {

class RequestState final {
public:
    explicit RequestState(std::chrono::steady_clock::time_point value) noexcept
        : deadline(value) {}

    std::chrono::steady_clock::time_point deadline;
    std::stop_source stop_source{};
    bool cancel_requested{false};
    bool finished{false};
};

class RuntimeState final {
public:
    explicit RuntimeState(Limits value) noexcept : limits(value) {}

    Limits limits;
    mutable std::mutex mutex{};
    std::condition_variable changed{};
    std::shared_ptr<RequestState> active{};
    bool accepting{true};
    RuntimeSnapshot counters{true, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U};
};

namespace {

constexpr std::uint64_t kMaxDeadlineMs = 10000U;
constexpr std::uint64_t kMaxDiagnosticBytes = 1024U;

[[nodiscard]] ErrorCode validate_limits(const Limits& limits) noexcept {
    if (limits.max_in_flight_requests != 1U || limits.max_queue_depth != 0U ||
        limits.deadline_ms == 0U) return ErrorCode::invalid_limits;
    if (limits.deadline_ms > kMaxDeadlineMs ||
        limits.max_diagnostic_bytes > kMaxDiagnosticBytes) return ErrorCode::resource_limit;
    return ErrorCode::none;
}

void saturating_increment(std::uint64_t& value) noexcept {
    if (value != std::numeric_limits<std::uint64_t>::max()) ++value;
}

[[nodiscard]] std::chrono::steady_clock::time_point capped_deadline(
    std::chrono::steady_clock::time_point admitted_at,
    std::uint64_t duration_ms) noexcept {
    using Clock = std::chrono::steady_clock;
    const auto duration = std::chrono::milliseconds{static_cast<std::int64_t>(duration_ms)};
    const auto available = Clock::time_point::max() - admitted_at;
    if (duration >= available) return Clock::time_point::max();
    return admitted_at + duration;
}

}  // namespace

CancellationHandle::CancellationHandle(std::weak_ptr<RuntimeState> runtime,
                                       std::weak_ptr<RequestState> request) noexcept
    : runtime_(std::move(runtime)), request_(std::move(request)) {}

bool CancellationHandle::request_cancel() const noexcept {
    const std::shared_ptr<RuntimeState> runtime = runtime_.lock();
    const std::shared_ptr<RequestState> request = request_.lock();
    if (!runtime || !request) return false;

    std::stop_source stop_source;
    {
        std::lock_guard lock(runtime->mutex);
        if (runtime->active != request || request->finished) return false;
        request->cancel_requested = true;
        stop_source = request->stop_source;
    }
    static_cast<void>(stop_source.request_stop());
    return true;
}

RequestLease::RequestLease(std::shared_ptr<RuntimeState> runtime,
                           std::shared_ptr<RequestState> request) noexcept
    : runtime_(std::move(runtime)), request_(std::move(request)) {}

RequestLease& RequestLease::operator=(RequestLease&& other) noexcept {
    if (this != &other) {
        static_cast<void>(finish());
        runtime_ = std::move(other.runtime_);
        request_ = std::move(other.request_);
    }
    return *this;
}

RequestLease::~RequestLease() {
    static_cast<void>(finish());
}

bool RequestLease::valid() const noexcept {
    return runtime_ != nullptr && request_ != nullptr;
}

agi::image::p4::AdmissionControl RequestLease::control() const noexcept {
    if (!valid()) return {};
    return agi::image::p4::AdmissionControl{
        request_->stop_source.get_token(), true, request_->deadline};
}

CancellationHandle RequestLease::cancellation_handle() const noexcept {
    if (!valid()) return {};
    return CancellationHandle{runtime_, request_};
}

CompletionStatus RequestLease::finish() noexcept {
    if (!valid()) return CompletionStatus::invalid_lease;

    CompletionStatus status = CompletionStatus::invalid_lease;
    {
        std::lock_guard lock(runtime_->mutex);
        if (runtime_->active == request_ && !request_->finished) {
            if (request_->cancel_requested) {
                status = CompletionStatus::cancelled;
                saturating_increment(runtime_->counters.cancelled_requests);
            } else if (std::chrono::steady_clock::now() >= request_->deadline) {
                status = CompletionStatus::deadline_exceeded;
                saturating_increment(runtime_->counters.deadline_exceeded_requests);
            } else {
                status = CompletionStatus::completed;
                saturating_increment(runtime_->counters.completed_requests);
            }
            request_->finished = true;
            runtime_->active.reset();
            runtime_->counters.active_requests = 0U;
        }
    }
    runtime_->changed.notify_all();
    request_.reset();
    runtime_.reset();
    return status;
}

Runtime::Runtime(Limits limits)
    : state_(std::make_shared<RuntimeState>(limits)) {}

Runtime::~Runtime() {
    close_without_wait();
}

StartResult Runtime::try_begin_request(const RequestOptions& options) noexcept {
    if (!state_) return {ErrorCode::allocation_failure, {}};
    const ErrorCode limits_status = validate_limits(state_->limits);
    if (limits_status != ErrorCode::none) return {limits_status, {}};

    using Clock = std::chrono::steady_clock;
    const auto first_now = Clock::now();
    if (options.caller_deadline && *options.caller_deadline <= first_now) {
        std::lock_guard lock(state_->mutex);
        saturating_increment(state_->counters.deadline_exceeded_requests);
        return {ErrorCode::deadline_exceeded, {}};
    }

    const auto runtime_deadline = capped_deadline(first_now, state_->limits.deadline_ms);
    const auto deadline = options.caller_deadline
        ? std::min(runtime_deadline, *options.caller_deadline)
        : runtime_deadline;

    std::lock_guard lock(state_->mutex);
    if (!state_->accepting) {
        saturating_increment(state_->counters.closed_runtime_rejections);
        return {ErrorCode::runtime_closed, {}};
    }
    if (Clock::now() >= deadline) {
        saturating_increment(state_->counters.deadline_exceeded_requests);
        return {ErrorCode::deadline_exceeded, {}};
    }
    if (state_->active) {
        saturating_increment(state_->counters.backpressure_rejections);
        return {ErrorCode::backpressure, {}};
    }

    try {
        auto request = std::make_shared<RequestState>(deadline);
        state_->active = request;
        state_->counters.accepting_requests = true;
        state_->counters.active_requests = 1U;
        saturating_increment(state_->counters.admitted_requests);
        return {ErrorCode::none, RequestLease{state_, std::move(request)}};
    } catch (const std::bad_alloc&) {
        return {ErrorCode::allocation_failure, {}};
    } catch (...) {
        return {ErrorCode::allocation_failure, {}};
    }
}

RuntimeSnapshot Runtime::snapshot() const noexcept {
    if (!state_) return {};
    std::lock_guard lock(state_->mutex);
    RuntimeSnapshot result = state_->counters;
    result.accepting_requests = state_->accepting;
    result.active_requests = state_->active ? 1U : 0U;
    result.diagnostic_bytes_emitted = 0U;
    return result;
}

void Runtime::close(CloseMode mode) {
    if (!state_) return;

    std::shared_ptr<RequestState> active;
    std::stop_source stop_source;
    {
        std::lock_guard lock(state_->mutex);
        state_->accepting = false;
        state_->counters.accepting_requests = false;
        active = state_->active;
        if (mode == CloseMode::cancel_active_and_drain && active && !active->finished) {
            active->cancel_requested = true;
            stop_source = active->stop_source;
        }
    }
    if (mode == CloseMode::cancel_active_and_drain && active) {
        static_cast<void>(stop_source.request_stop());
    }

    std::unique_lock lock(state_->mutex);
    state_->changed.wait(lock, [this] { return !state_->active; });
}

void Runtime::close_without_wait() noexcept {
    if (!state_) return;

    std::shared_ptr<RequestState> active;
    std::stop_source stop_source;
    {
        std::lock_guard lock(state_->mutex);
        state_->accepting = false;
        state_->counters.accepting_requests = false;
        active = state_->active;
        if (active && !active->finished) {
            active->cancel_requested = true;
            stop_source = active->stop_source;
        }
    }
    if (active) static_cast<void>(stop_source.request_stop());
}

const char* error_code_name(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::none: return "NONE";
        case ErrorCode::invalid_limits: return "INVALID_LIMITS";
        case ErrorCode::resource_limit: return "RESOURCE_LIMIT";
        case ErrorCode::backpressure: return "BACKPRESSURE";
        case ErrorCode::runtime_closed: return "RUNTIME_CLOSED";
        case ErrorCode::deadline_exceeded: return "DEADLINE_EXCEEDED";
        case ErrorCode::allocation_failure: return "ALLOCATION_FAILURE";
    }
    return "ALLOCATION_FAILURE";
}

const char* completion_status_name(CompletionStatus status) noexcept {
    switch (status) {
        case CompletionStatus::completed: return "COMPLETED";
        case CompletionStatus::cancelled: return "CANCELLED";
        case CompletionStatus::deadline_exceeded: return "DEADLINE_EXCEEDED";
        case CompletionStatus::invalid_lease: return "INVALID_LEASE";
    }
    return "INVALID_LEASE";
}

}  // namespace agi::image::p8
