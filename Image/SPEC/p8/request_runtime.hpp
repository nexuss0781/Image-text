#pragma once

#include "../p4/raster_admission.hpp"

#include <chrono>
#include <cstdint>
#include <memory>
#include <optional>

namespace agi::image::p8 {

enum class ErrorCode : std::uint8_t {
    none,
    invalid_limits,
    resource_limit,
    backpressure,
    runtime_closed,
    deadline_exceeded,
    allocation_failure,
};

enum class CompletionStatus : std::uint8_t {
    completed,
    cancelled,
    deadline_exceeded,
    invalid_lease,
};

enum class CloseMode : std::uint8_t {
    drain,
    cancel_active_and_drain,
};

// All values are explicit per-runtime inputs. These are proposal-derived
// engineering ceilings only, not production defaults or approved SLOs.
struct Limits final {
    std::uint32_t max_in_flight_requests;
    std::uint32_t max_queue_depth;
    std::uint64_t deadline_ms;
    std::uint64_t max_diagnostic_bytes;
};

struct RequestOptions final {
    // When supplied, this absolute steady-clock deadline can shorten, but never
    // extend, the runtime's configured maximum request duration.
    std::optional<std::chrono::steady_clock::time_point> caller_deadline{};
};

struct RuntimeSnapshot final {
    bool accepting_requests{false};
    std::uint32_t active_requests{0};
    std::uint64_t admitted_requests{0};
    std::uint64_t completed_requests{0};
    std::uint64_t backpressure_rejections{0};
    std::uint64_t cancelled_requests{0};
    std::uint64_t deadline_exceeded_requests{0};
    std::uint64_t closed_runtime_rejections{0};
    std::uint64_t diagnostic_bytes_emitted{0};
};

class RuntimeState;
class RequestState;

class CancellationHandle final {
public:
    CancellationHandle() noexcept = default;

    // Returns true only when cancellation is accepted for the currently active
    // lease. A cancellation racing after completion is a no-op.
    [[nodiscard]] bool request_cancel() const noexcept;

private:
    CancellationHandle(std::weak_ptr<RuntimeState> runtime,
                       std::weak_ptr<RequestState> request) noexcept;

    std::weak_ptr<RuntimeState> runtime_{};
    std::weak_ptr<RequestState> request_{};

    friend class RequestLease;
};

class RequestLease final {
public:
    RequestLease() noexcept = default;
    RequestLease(const RequestLease&) = delete;
    RequestLease& operator=(const RequestLease&) = delete;
    RequestLease(RequestLease&& other) noexcept = default;
    RequestLease& operator=(RequestLease&& other) noexcept;
    ~RequestLease();

    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] agi::image::p4::AdmissionControl control() const noexcept;
    [[nodiscard]] CancellationHandle cancellation_handle() const noexcept;

    // Finalizes exactly once and releases the active slot. Cancellation wins
    // over deadline only when requested before this method linearizes.
    [[nodiscard]] CompletionStatus finish() noexcept;

private:
    RequestLease(std::shared_ptr<RuntimeState> runtime,
                 std::shared_ptr<RequestState> request) noexcept;

    std::shared_ptr<RuntimeState> runtime_{};
    std::shared_ptr<RequestState> request_{};

    friend class Runtime;
};

struct StartResult final {
    ErrorCode error_code{ErrorCode::invalid_limits};
    RequestLease lease{};

    [[nodiscard]] bool has_value() const noexcept {
        return error_code == ErrorCode::none && lease.valid();
    }
};

class Runtime final {
public:
    explicit Runtime(Limits limits);
    Runtime(const Runtime&) = delete;
    Runtime& operator=(const Runtime&) = delete;
    Runtime(Runtime&&) = delete;
    Runtime& operator=(Runtime&&) = delete;
    ~Runtime();

    // Never waits for capacity: with one active request and a zero-depth queue,
    // the next caller receives BACKPRESSURE immediately.
    [[nodiscard]] StartResult try_begin_request(const RequestOptions& options = {}) noexcept;
    [[nodiscard]] RuntimeSnapshot snapshot() const noexcept;

    // Close is terminal and blocks until any accepted lease is finished. The
    // cancel mode requests cooperative stop before waiting. Do not call this
    // synchronously from the thread that must finish the active lease.
    void close(CloseMode mode);

private:
    void close_without_wait() noexcept;
    std::shared_ptr<RuntimeState> state_{};
};

[[nodiscard]] const char* error_code_name(ErrorCode code) noexcept;
[[nodiscard]] const char* completion_status_name(CompletionStatus status) noexcept;

}  // namespace agi::image::p8
