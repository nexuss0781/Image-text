#include "../../p4/raster_admission.hpp"
#include "../../p8/request_runtime.hpp"

#include <array>
#include <barrier>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <optional>
#include <stop_token>
#include <thread>
#include <utility>

using agi::image::p4::AdmissionLimits;
using agi::image::p4::ChannelOrder;
using P4ErrorCode = agi::image::p4::ErrorCode;
using agi::image::p4::InputKind;
using agi::image::p4::Layout;
using agi::image::p4::RasterDescriptor;
using agi::image::p4::SampleType;
using agi::image::p4::admit;
using agi::image::p8::CloseMode;
using agi::image::p8::CompletionStatus;
using P8ErrorCode = agi::image::p8::ErrorCode;
using agi::image::p8::Limits;
using agi::image::p8::RequestOptions;
using agi::image::p8::Runtime;
using agi::image::p8::StartResult;

namespace {

constexpr Limits kProposalCeilings{1U, 0U, 10000U, 1024U};
constexpr AdmissionLimits kAdmissionLimits{4U, 4U, 16U, 4U, 64U, 64U};
constexpr std::size_t kConcurrentCallers = 16U;

void report(const char* id, const char* case_id, const char* label, bool passed,
            int& pass_count, int& fail_count) noexcept {
    std::printf("CASE\t%s\t%s\t%s\t%s\n", id, passed ? "pass" : "fail", case_id, label);
    if (passed) ++pass_count;
    else ++fail_count;
}

[[nodiscard]] RasterDescriptor one_pixel_descriptor() noexcept {
    return {1U, 1U, 1U, Layout::hwc, ChannelOrder::gray, SampleType::uint8,
            0U, 255U, 1U, 1U, 1U, 1U};
}

[[nodiscard]] bool p4_rejects(const agi::image::p4::AdmissionResult& result,
                              P4ErrorCode expected) noexcept {
    return !result.has_value() && result.error_code() == expected &&
           result.value() == nullptr && !result.retryable() && !result.state_changed();
}

[[nodiscard]] bool configured_limits_are_fail_closed() noexcept {
    Runtime valid{kProposalCeilings};
    if (!valid.try_begin_request().has_value()) return false;

    Limits limits = kProposalCeilings;
    limits.max_in_flight_requests = 2U;
    Runtime too_many_active{limits};
    if (too_many_active.try_begin_request().error_code != P8ErrorCode::invalid_limits) return false;

    limits = kProposalCeilings;
    limits.max_queue_depth = 1U;
    Runtime queued{limits};
    if (queued.try_begin_request().error_code != P8ErrorCode::invalid_limits) return false;

    limits = kProposalCeilings;
    limits.deadline_ms = 10001U;
    Runtime long_deadline{limits};
    if (long_deadline.try_begin_request().error_code != P8ErrorCode::resource_limit) return false;

    limits = kProposalCeilings;
    limits.max_diagnostic_bytes = 1025U;
    Runtime verbose{limits};
    return verbose.try_begin_request().error_code == P8ErrorCode::resource_limit;
}

[[nodiscard]] bool accepted_lease_forwards_bounded_deadline() noexcept {
    Runtime runtime{kProposalCeilings};
    auto started = runtime.try_begin_request();
    if (!started.has_value()) return false;
    const auto control = started.lease.control();
    const auto now = std::chrono::steady_clock::now();
    const auto ceiling = now + std::chrono::milliseconds{10000};
    if (!control.has_deadline || control.cancellation.stop_requested() ||
        control.deadline <= now || control.deadline > ceiling) return false;
    return started.lease.finish() == CompletionStatus::completed;
}

[[nodiscard]] bool zero_queue_returns_immediate_backpressure() noexcept {
    Runtime runtime{kProposalCeilings};
    auto first = runtime.try_begin_request();
    if (!first.has_value()) return false;
    auto second = runtime.try_begin_request();
    if (second.error_code != P8ErrorCode::backpressure || second.lease.valid()) return false;
    const auto while_busy = runtime.snapshot();
    if (while_busy.active_requests != 1U || while_busy.admitted_requests != 1U ||
        while_busy.backpressure_rejections != 1U) return false;
    if (first.lease.finish() != CompletionStatus::completed) return false;
    auto retry = runtime.try_begin_request();
    if (!retry.has_value()) return false;
    const auto snapshot = runtime.snapshot();
    return snapshot.active_requests == 1U && snapshot.admitted_requests == 2U &&
           snapshot.backpressure_rejections == 1U &&
           retry.lease.finish() == CompletionStatus::completed;
}

[[nodiscard]] bool concurrent_burst_admits_exactly_one() noexcept {
    Runtime runtime{kProposalCeilings};
    std::array<P8ErrorCode, kConcurrentCallers> outcomes{};
    std::array<std::optional<agi::image::p8::RequestLease>, kConcurrentCallers> leases{};
    std::barrier start_line{static_cast<std::ptrdiff_t>(kConcurrentCallers)};
    std::array<std::thread, kConcurrentCallers> callers{};
    for (std::size_t index = 0; index < kConcurrentCallers; ++index) {
        callers[index] = std::thread([&, index] {
            start_line.arrive_and_wait();
            StartResult result = runtime.try_begin_request();
            outcomes[index] = result.error_code;
            if (result.has_value()) leases[index].emplace(std::move(result.lease));
        });
    }
    for (auto& caller : callers) caller.join();

    std::size_t admitted = 0U;
    std::size_t backpressured = 0U;
    for (std::size_t index = 0; index < kConcurrentCallers; ++index) {
        if (outcomes[index] == P8ErrorCode::none && leases[index].has_value()) ++admitted;
        if (outcomes[index] == P8ErrorCode::backpressure && !leases[index].has_value()) ++backpressured;
    }
    if (admitted != 1U || backpressured != kConcurrentCallers - 1U) return false;
    for (auto& lease : leases) {
        if (lease && lease->finish() != CompletionStatus::completed) return false;
    }
    const auto snapshot = runtime.snapshot();
    return snapshot.admitted_requests == 1U &&
           snapshot.backpressure_rejections == kConcurrentCallers - 1U &&
           snapshot.active_requests == 0U;
}

[[nodiscard]] bool cancellation_reaches_existing_p4_boundary() noexcept {
    Runtime runtime{kProposalCeilings};
    auto started = runtime.try_begin_request();
    if (!started.has_value()) return false;
    const auto cancel = started.lease.cancellation_handle();
    if (!cancel.request_cancel()) return false;
    std::array<std::uint8_t, 1> pixel{42U};
    const auto result = admit(InputKind::decoded_raster, one_pixel_descriptor(), pixel,
                              kAdmissionLimits, started.lease.control());
    return p4_rejects(result, P4ErrorCode::cancelled) &&
           started.lease.finish() == CompletionStatus::cancelled &&
           !cancel.request_cancel();
}

[[nodiscard]] bool earlier_caller_deadline_reaches_p4_boundary() noexcept {
    Runtime runtime{kProposalCeilings};
    RequestOptions options{};
    options.caller_deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds{50};
    auto started = runtime.try_begin_request(options);
    if (!started.has_value()) return false;
    const auto control = started.lease.control();
    if (!control.has_deadline || control.deadline > *options.caller_deadline) return false;
    std::this_thread::sleep_until(control.deadline + std::chrono::milliseconds{1});
    std::array<std::uint8_t, 1> pixel{42U};
    const auto result = admit(InputKind::decoded_raster, one_pixel_descriptor(), pixel,
                              kAdmissionLimits, control);
    return p4_rejects(result, P4ErrorCode::deadline_exceeded) &&
           started.lease.finish() == CompletionStatus::deadline_exceeded;
}

[[nodiscard]] bool drain_close_blocks_new_admission_and_waits() noexcept {
    Runtime runtime{kProposalCeilings};
    auto started = runtime.try_begin_request();
    if (!started.has_value()) return false;
    std::atomic<bool> closed{false};
    std::thread closer([&] {
        runtime.close(CloseMode::drain);
        closed.store(true, std::memory_order_release);
    });

    bool observed_closed = false;
    for (std::size_t attempt = 0; attempt < 1000U; ++attempt) {
        const auto snapshot = runtime.snapshot();
        if (!snapshot.accepting_requests) {
            observed_closed = true;
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds{1});
    }
    const bool still_draining = observed_closed && !closed.load(std::memory_order_acquire) &&
        !started.lease.control().cancellation.stop_requested() &&
        runtime.try_begin_request().error_code == P8ErrorCode::runtime_closed;
    const auto completion = started.lease.finish();
    closer.join();
    return still_draining && completion == CompletionStatus::completed &&
           closed.load(std::memory_order_acquire) && !runtime.snapshot().accepting_requests;
}

[[nodiscard]] bool cancel_and_drain_stops_active_then_waits() noexcept {
    Runtime runtime{kProposalCeilings};
    auto started = runtime.try_begin_request();
    if (!started.has_value()) return false;
    std::atomic<bool> closed{false};
    std::thread closer([&] {
        runtime.close(CloseMode::cancel_active_and_drain);
        closed.store(true, std::memory_order_release);
    });

    const auto control = started.lease.control();
    bool observed_cancel = false;
    for (std::size_t attempt = 0; attempt < 1000U; ++attempt) {
        if (control.cancellation.stop_requested()) {
            observed_cancel = true;
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds{1});
    }
    const bool still_draining = observed_cancel && !closed.load(std::memory_order_acquire) &&
        runtime.snapshot().active_requests == 1U;
    const auto completion = started.lease.finish();
    closer.join();
    return still_draining && completion == CompletionStatus::cancelled &&
           closed.load(std::memory_order_acquire) &&
           runtime.snapshot().cancelled_requests == 1U;
}

[[nodiscard]] bool close_is_idempotent_and_reopen_uses_new_runtime() noexcept {
    Runtime runtime{kProposalCeilings};
    runtime.close(CloseMode::drain);
    runtime.close(CloseMode::drain);
    if (runtime.try_begin_request().error_code != P8ErrorCode::runtime_closed) return false;
    Runtime reopened{kProposalCeilings};
    auto started = reopened.try_begin_request();
    return started.has_value() && started.lease.finish() == CompletionStatus::completed;
}

[[nodiscard]] bool destructor_cancels_without_dangling_active_state() noexcept {
    std::optional<agi::image::p8::RequestLease> outstanding;
    {
        Runtime runtime{kProposalCeilings};
        auto started = runtime.try_begin_request();
        if (!started.has_value()) return false;
        outstanding.emplace(std::move(started.lease));
    }
    if (!outstanding || !outstanding->control().cancellation.stop_requested()) return false;
    return outstanding->finish() == CompletionStatus::cancelled;
}

[[nodiscard]] bool telemetry_snapshot_is_aggregate_and_read_only() noexcept {
    Runtime runtime{kProposalCeilings};
    auto started = runtime.try_begin_request();
    if (!started.has_value()) return false;
    const auto before = runtime.snapshot();
    const auto copied = before;
    const bool private_free = before.diagnostic_bytes_emitted == 0U &&
        before.admitted_requests == 1U && before.active_requests == 1U;
    if (started.lease.finish() != CompletionStatus::completed) return false;
    const auto after = runtime.snapshot();
    return private_free && copied.active_requests == 1U &&
           after.active_requests == 0U && after.completed_requests == 1U &&
           after.diagnostic_bytes_emitted == 0U && after.accepting_requests;
}

[[nodiscard]] bool completed_lease_cannot_be_cancelled_or_reused() noexcept {
    Runtime runtime{kProposalCeilings};
    auto started = runtime.try_begin_request();
    if (!started.has_value()) return false;
    const auto cancel = started.lease.cancellation_handle();
    if (started.lease.finish() != CompletionStatus::completed || cancel.request_cancel()) return false;
    if (started.lease.finish() != CompletionStatus::invalid_lease) return false;
    auto next = runtime.try_begin_request();
    return next.has_value() && next.lease.finish() == CompletionStatus::completed;
}

}  // namespace

int main() {
    int passed = 0;
    int failed = 0;
    report("P8-TEST-001", "RES-001", "proposal_limit_ceiling_rejection", configured_limits_are_fail_closed(), passed, failed);
    report("P8-TEST-002", "RES-001", "effective_deadline_forwarded", accepted_lease_forwards_bounded_deadline(), passed, failed);
    report("P8-TEST-003", "RES-003", "zero_depth_backpressure_and_retry_after_release", zero_queue_returns_immediate_backpressure(), passed, failed);
    report("P8-TEST-004", "RES-003", "concurrent_burst_admits_one_without_queue", concurrent_burst_admits_exactly_one(), passed, failed);
    report("P8-TEST-005", "ADM-007", "cancellation_propagates_to_p4", cancellation_reaches_existing_p4_boundary(), passed, failed);
    report("P8-TEST-006", "ADM-007", "caller_deadline_propagates_to_p4", earlier_caller_deadline_reaches_p4_boundary(), passed, failed);
    report("P8-TEST-007", "STR-002", "drain_close_waits_and_refuses_new_work", drain_close_blocks_new_admission_and_waits(), passed, failed);
    report("P8-TEST-008", "STR-002", "cancel_close_stops_then_drains", cancel_and_drain_stops_active_then_waits(), passed, failed);
    report("P8-TEST-009", "STR-002", "close_idempotence_terminal_state_and_new_instance", close_is_idempotent_and_reopen_uses_new_runtime(), passed, failed);
    report("P8-TEST-010", "TEL-001", "aggregate_snapshot_privacy_and_read_only_copy", telemetry_snapshot_is_aggregate_and_read_only(), passed, failed);
    report("P8-TEST-011", "STR-002", "late_cancellation_is_ignored_and_slot_reusable", completed_lease_cannot_be_cancelled_or_reused(), passed, failed);
    report("P8-TEST-012", "STR-002", "destructor_requests_stop_without_use_after_free", destructor_cancels_without_dangling_active_state(), passed, failed);
    std::printf("SUMMARY\t%d\t%d\n", passed, passed + failed);
    return failed == 0 ? 0 : 1;
}
