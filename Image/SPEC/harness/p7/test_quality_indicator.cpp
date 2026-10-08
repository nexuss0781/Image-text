#include "../../p4/raster_admission.hpp"
#include "../../p5/canonical_raster.hpp"
#include "../../p6/forward_difference.hpp"
#include "../../p7/quality_indicator.hpp"

#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <span>
#include <stop_token>
#include <string_view>
#include <vector>

using agi::image::p4::AdmissionControl;
using agi::image::p4::AdmissionLimits;
using agi::image::p4::ChannelOrder;
using agi::image::p4::InputKind;
using agi::image::p4::Layout;
using agi::image::p4::RasterDescriptor;
using agi::image::p4::SampleType;
using agi::image::p5::CanonicalRasterView;
using agi::image::p5::PixelFormat;
using agi::image::p7::ErrorCode;
using agi::image::p7::Limits;
using agi::image::p7::Options;
using agi::image::p7::Result;
using agi::image::p7::measure_endpoint_code_fraction_v1;
using agi::image::p7::measure_endpoint_code_fraction_v1_with_test_fault;

namespace {

constexpr Limits kLimits{64U, 4U, 24U, 256U};
const AdmissionControl kNoControl{};
constexpr AdmissionLimits kAdmissionLimits{8U, 8U, 64U, 4U, 256U, 256U};
constexpr agi::image::p5::Limits kCanonicalLimits{8U, 8U, 64U, 256U, 256U};
constexpr agi::image::p6::Limits kDifferenceLimits{64U, 4U, 128U, 256U, 128U};

[[nodiscard]] CanonicalRasterView make_view(
    std::uint64_t width, std::uint64_t height, std::uint32_t channels,
    ChannelOrder order, std::span<const std::uint8_t> samples) noexcept {
    CanonicalRasterView view{};
    view.samples = samples;
    view.width = width;
    view.height = height;
    view.pixel_count = width * height;
    view.channels = channels;
    view.channel_order = order;
    view.pixel_format = order == ChannelOrder::gray ? PixelFormat::gray_u8 :
                        order == ChannelOrder::rgb ? PixelFormat::rgb_u8 :
                        order == ChannelOrder::rgba ? PixelFormat::rgba_u8 : PixelFormat::unknown;
    view.color_profile_id = "source-declared-or-unknown-v1";
    view.alpha_policy = agi::image::p5::AlphaAction::preserve;
    view.orientation_action = agi::image::p5::OrientationAction::decoded_raster_only;
    view.transform.transform_id = "identity-test-v1";
    view.transform.source_frame_id = "source-test-frame";
    view.transform.target_frame_id = "canonical-test-frame";
    view.transform.source_width = width;
    view.transform.source_height = height;
    view.transform.target_width = width;
    view.transform.target_height = height;
    view.transform.matrix_3x3 = {1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0};
    view.transform.inverse_matrix_3x3 = view.transform.matrix_3x3;
    view.transform.source_to_target = true;
    view.transform.invertible = true;
    return view;
}

[[nodiscard]] bool failed_closed(const Result& result, ErrorCode expected) noexcept {
    return !result.has_value() && result.error_code == expected && !result.quality.has_value() &&
           !result.uncertainty.has_value() && !result.retryable() && !result.state_changed();
}

[[nodiscard]] bool exact(
    std::uint64_t width, std::uint64_t height, std::uint32_t channels,
    ChannelOrder order, const std::vector<std::uint8_t>& samples,
    std::uint64_t numerator, std::uint64_t denominator, double value) noexcept {
    const auto view = make_view(width, height, channels, order, samples);
    const Result result = measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl);
    return result.has_value() && result.quality.has_value() &&
           !result.uncertainty.has_value() && result.quality->numerator == numerator &&
           result.quality->denominator == denominator && result.quality->value == value &&
           result.quality->work_units == denominator &&
           result.quality->output_payload_bytes == 24U;
}

[[nodiscard]] bool gray_literal_ratio_is_exact() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U, 255U, 128U};
    return exact(2U, 2U, 1U, ChannelOrder::gray, samples, 2U, 4U, 0.5);
}

[[nodiscard]] bool rgb_literal_counts_all_three_color_channels() noexcept {
    const std::vector<std::uint8_t> samples{0U, 7U, 128U, 128U, 255U, 4U};
    return exact(2U, 1U, 3U, ChannelOrder::rgb, samples, 2U, 6U, 1.0 / 3.0);
}

[[nodiscard]] bool rgba_literal_excludes_alpha_from_both_counts() noexcept {
    const std::vector<std::uint8_t> samples{
        0U, 10U, 11U, 0U,
        250U, 255U, 255U, 255U,
    };
    return exact(2U, 1U, 4U, ChannelOrder::rgba, samples, 3U, 6U, 0.5);
}

[[nodiscard]] bool controlled_change_has_literal_delta() noexcept {
    const std::vector<std::uint8_t> before{10U, 20U, 30U, 40U};
    const std::vector<std::uint8_t> after{10U, 20U, 255U, 40U};
    return exact(4U, 1U, 1U, ChannelOrder::gray, before, 0U, 4U, 0.0) &&
           exact(4U, 1U, 1U, ChannelOrder::gray, after, 1U, 4U, 0.25);
}

[[nodiscard]] bool exact_range_includes_zero_and_one() noexcept {
    const std::vector<std::uint8_t> all_endpoints{0U, 255U, 0U, 255U};
    const std::vector<std::uint8_t> no_endpoints{1U, 127U, 128U, 254U};
    return exact(4U, 1U, 1U, ChannelOrder::gray, all_endpoints, 4U, 4U, 1.0) &&
           exact(4U, 1U, 1U, ChannelOrder::gray, no_endpoints, 0U, 4U, 0.0);
}

[[nodiscard]] bool method_metadata_is_descriptive_and_versioned() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U};
    const auto view = make_view(2U, 1U, 1U, ChannelOrder::gray, samples);
    const Result result = measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl);
    if (!result.has_value() || !result.quality.has_value()) return false;
    const auto& q = *result.quality;
    return q.name == "endpoint_code_fraction" &&
           q.method_id == "uint8-endpoint-code-fraction" && q.method_version == "1" &&
           q.units == "fraction" && q.scope == "image" &&
           q.acceptance_effect == "descriptive_only" && q.numerator == 1U &&
           q.denominator == 2U && q.value == 0.5 && std::isfinite(q.value) &&
           q.value >= 0.0 && q.value <= 1.0;
}

[[nodiscard]] bool limits_and_output_bound_fail_atomically() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U, 255U, 128U};
    const auto view = make_view(2U, 2U, 1U, ChannelOrder::gray, samples);
    Limits limits = kLimits;
    limits.max_pixels = 3U;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, limits, {}, kNoControl),
                       ErrorCode::resource_limit)) return false;
    limits = kLimits; limits.max_channels = 0U;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, limits, {}, kNoControl),
                       ErrorCode::resource_limit)) return false;
    limits = kLimits; limits.max_channels = 5U;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, limits, {}, kNoControl),
                       ErrorCode::resource_limit)) return false;
    limits = kLimits; limits.max_work_units = 3U;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, limits, {}, kNoControl),
                       ErrorCode::resource_limit)) return false;
    limits = kLimits; limits.max_output_bytes = 23U;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, limits, {}, kNoControl),
                       ErrorCode::resource_limit)) return false;
    limits = kLimits; limits.max_output_bytes = 0U;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, limits, {}, kNoControl),
                       ErrorCode::resource_limit)) return false;
    auto overflow = view;
    overflow.width = std::numeric_limits<std::uint64_t>::max();
    overflow.height = 2U;
    overflow.pixel_count = 0U;
    overflow.transform.source_width = overflow.width;
    overflow.transform.target_width = overflow.width;
    overflow.transform.source_height = overflow.height;
    overflow.transform.target_height = overflow.height;
    if (!failed_closed(measure_endpoint_code_fraction_v1(overflow, kLimits, {}, kNoControl),
                       ErrorCode::resource_limit)) return false;
    return samples == std::vector<std::uint8_t>{0U, 128U, 255U, 128U};
}

[[nodiscard]] bool malformed_dimensions_layout_and_metadata_fail_closed() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U, 255U, 128U};
    auto view = make_view(2U, 2U, 1U, ChannelOrder::gray, samples);
    view.pixel_count = 3U;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl),
                       ErrorCode::invalid_descriptor)) return false;
    view = make_view(2U, 2U, 1U, ChannelOrder::gray,
                     std::span<const std::uint8_t>(samples.data(), 3U));
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl),
                       ErrorCode::invalid_descriptor)) return false;
    view = make_view(2U, 2U, 3U, ChannelOrder::bgr, samples);
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl),
                       ErrorCode::unsupported_format)) return false;
    view = make_view(2U, 2U, 1U, ChannelOrder::gray, samples);
    view.transform.matrix_3x3[0] = 2.0;
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl),
                       ErrorCode::invalid_descriptor)) return false;
    view = make_view(2U, 2U, 1U, ChannelOrder::gray, samples);
    view.color_profile_id = "mismatched-profile";
    return failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl),
                         ErrorCode::profile_mismatch);
}

[[nodiscard]] bool nonfinite_transform_metadata_is_typed() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U};
    auto view = make_view(2U, 1U, 1U, ChannelOrder::gray, samples);
    view.transform.inverse_matrix_3x3[4] = std::numeric_limits<double>::quiet_NaN();
    return failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl),
                         ErrorCode::nonfinite_input);
}

[[nodiscard]] bool cancellation_and_expired_deadline_are_atomic() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U, 255U, 128U};
    const auto view = make_view(2U, 2U, 1U, ChannelOrder::gray, samples);
    std::stop_source stop;
    stop.request_stop();
    AdmissionControl cancelled{};
    cancelled.cancellation = stop.get_token();
    if (!failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, cancelled),
                       ErrorCode::cancelled)) return false;
    AdmissionControl expired{};
    expired.has_deadline = true;
    expired.deadline = std::chrono::steady_clock::now() - std::chrono::seconds(1);
    return failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, {}, expired),
                         ErrorCode::deadline_exceeded);
}

[[nodiscard]] bool uncertainty_is_omitted_or_rejected_when_required() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U};
    const auto view = make_view(2U, 1U, 1U, ChannelOrder::gray, samples);
    const Result default_result = measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl);
    if (!default_result.has_value() || !default_result.quality.has_value() ||
        default_result.uncertainty.has_value()) return false;
    Options required{};
    required.require_uncertainty = true;
    return failed_closed(measure_endpoint_code_fraction_v1(view, kLimits, required, kNoControl),
                         ErrorCode::uncertainty_unavailable);
}

[[nodiscard]] bool error_messages_are_allowlisted_and_never_echo_secret_marker() noexcept {
    constexpr std::string_view marker{"SECRET_MARKER_private/path"};
    const std::vector<std::uint8_t> samples{1U, 2U};
    auto view = make_view(2U, 1U, 1U, ChannelOrder::gray, samples);
    view.transform.transform_id = marker;
    view.transform.matrix_3x3[0] = 3.0;
    const Result result = measure_endpoint_code_fraction_v1(view, kLimits, {}, kNoControl);
    if (!failed_closed(result, ErrorCode::invalid_descriptor)) return false;
    const std::string_view message{agi::image::p7::error_message(result.error_code)};
    if (message.empty() || message.size() > 512U || message.find(marker) != std::string_view::npos ||
        message != "Input does not satisfy the canonical raster contract." ||
        std::string_view{agi::image::p7::error_code_name(result.error_code)} != "INVALID_DESCRIPTOR") {
        return false;
    }
    constexpr std::array<ErrorCode, 9> codes{
        ErrorCode::none, ErrorCode::invalid_descriptor, ErrorCode::unsupported_format,
        ErrorCode::profile_mismatch, ErrorCode::resource_limit, ErrorCode::nonfinite_input,
        ErrorCode::uncertainty_unavailable, ErrorCode::cancelled, ErrorCode::deadline_exceeded,
    };
    for (const ErrorCode code : codes) {
        const std::string_view text{agi::image::p7::error_message(code)};
        if (text.size() > 512U || text.find(marker) != std::string_view::npos) return false;
    }
    const std::string_view internal{agi::image::p7::error_message(ErrorCode::internal_error)};
    return internal == "Quality analysis could not be completed." && internal.size() <= 512U &&
           internal.find(marker) == std::string_view::npos && !result.retryable() &&
           !result.state_changed();
}

[[nodiscard]] bool injected_failure_after_partial_scan_returns_nothing() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U, 255U, 128U};
    const auto before = samples;
    const auto view = make_view(2U, 2U, 1U, ChannelOrder::gray, samples);
    const Result result = measure_endpoint_code_fraction_v1_with_test_fault(
        view, kLimits, {}, kNoControl, agi::image::p7::testing::FaultPoint::after_first_sample);
    return failed_closed(result, ErrorCode::internal_error) && samples == before;
}

[[nodiscard]] bool injected_failure_before_publish_discards_candidate() noexcept {
    const std::vector<std::uint8_t> samples{0U, 128U, 255U, 128U};
    const auto before = samples;
    const auto view = make_view(2U, 2U, 1U, ChannelOrder::gray, samples);
    const Result result = measure_endpoint_code_fraction_v1_with_test_fault(
        view, kLimits, {}, kNoControl, agi::image::p7::testing::FaultPoint::before_publish);
    return failed_closed(result, ErrorCode::internal_error) && samples == before;
}

[[nodiscard]] RasterDescriptor gray_descriptor(std::uint64_t width,
                                               std::uint64_t height) noexcept {
    return {width, height, 1U, Layout::hwc, ChannelOrder::gray, SampleType::uint8,
            0U, 255U, width, 1U, 1U, width * height};
}

[[nodiscard]] agi::image::p5::Request identity_request() noexcept {
    return {"source-frame", "canonical-frame", "identity-p7-v1",
            "source-declared-or-unknown-v1"};
}

[[nodiscard]] bool p4_admission_boundary_failure_is_atomic() noexcept {
    std::vector<std::uint8_t> samples{0U};
    const auto before = samples;
    RasterDescriptor descriptor = gray_descriptor(2U, 1U);
    const auto result = agi::image::p4::admit(InputKind::decoded_raster, descriptor,
                                               samples, kAdmissionLimits);
    return !result.has_value() && result.error_code() == agi::image::p4::ErrorCode::invalid_descriptor &&
           result.value() == nullptr && !result.retryable() && !result.state_changed() &&
           samples == before;
}

[[nodiscard]] bool p5_canonicalization_boundary_failure_is_atomic() noexcept {
    std::vector<std::uint8_t> samples{0U, 128U};
    const auto before = samples;
    const auto descriptor = gray_descriptor(2U, 1U);
    const auto admitted = agi::image::p4::admit(InputKind::decoded_raster, descriptor,
                                                samples, kAdmissionLimits);
    if (!admitted.has_value()) return false;
    auto request = identity_request();
    request.geometry_operation = agi::image::p5::GeometryOperation::resize;
    const auto result = agi::image::p5::canonicalize_identity(
        *admitted.value(), request, kCanonicalLimits);
    return !result.has_value() && result.error_code == agi::image::p5::ErrorCode::unsupported_policy &&
           result.raster.samples.empty() && result.raster.width == 0U &&
           !result.retryable() && !result.state_changed() && samples == before;
}

[[nodiscard]] bool p6_operator_boundary_failure_is_atomic() noexcept {
    std::vector<std::uint8_t> samples{0U, 128U};
    const auto before = samples;
    auto view = make_view(2U, 1U, 1U, ChannelOrder::gray, samples);
    agi::image::p6::Limits limits = kDifferenceLimits;
    limits.max_output_bytes = 7U;
    const auto result = agi::image::p6::forward_difference_xy_v1(view, limits, kNoControl);
    return !result.has_value() && result.error_code == agi::image::p6::ErrorCode::resource_limit &&
           result.planes.dx.empty() && result.planes.dy.empty() &&
           result.planes.output_elements == 0U && !result.retryable() &&
           !result.state_changed() && samples == before;
}

[[nodiscard]] bool p4_to_p7_supported_pipeline_is_exact_and_read_only() noexcept {
    std::vector<std::uint8_t> samples{0U, 64U, 255U, 128U};
    const auto before = samples;
    const auto descriptor = gray_descriptor(2U, 2U);
    const auto admitted = agi::image::p4::admit(InputKind::decoded_raster, descriptor,
                                                samples, kAdmissionLimits);
    if (!admitted.has_value()) return false;
    const auto canonical = agi::image::p5::canonicalize_identity(
        *admitted.value(), identity_request(), kCanonicalLimits);
    if (!canonical.has_value()) return false;
    const auto difference = agi::image::p6::forward_difference_xy_v1(
        canonical.raster, kDifferenceLimits, kNoControl);
    if (!difference.has_value()) return false;
    const Result quality = measure_endpoint_code_fraction_v1(
        canonical.raster, kLimits, {}, kNoControl);
    return quality.has_value() && quality.quality.has_value() &&
           !quality.uncertainty.has_value() && quality.quality->numerator == 2U &&
           quality.quality->denominator == 4U && quality.quality->value == 0.5 &&
           difference.planes.work_units == 8U && samples == before;
}

struct TestCase final {
    const char* id;
    const char* catalog;
    const char* label;
    bool (*run)() noexcept;
};

constexpr std::array<TestCase, 18> kTests{{
    {"P7-TEST-001", "QUAL-001", "GRAY endpoint fraction exact literal", gray_literal_ratio_is_exact},
    {"P7-TEST-002", "QUAL-001", "RGB numerator denominator include all color channels", rgb_literal_counts_all_three_color_channels},
    {"P7-TEST-003", "QUAL-001", "RGBA excludes alpha from numerator and denominator", rgba_literal_excludes_alpha_from_both_counts},
    {"P7-TEST-004", "QUAL-001", "controlled one-sample change has exact literal delta", controlled_change_has_literal_delta},
    {"P7-TEST-005", "QUAL-001", "fraction bounds include exact zero and one", exact_range_includes_zero_and_one},
    {"P7-TEST-006", "QUAL-001", "method version units scope and descriptive tag are exact", method_metadata_is_descriptive_and_versioned},
    {"P7-TEST-007", "ERR-003", "caller limits and 24-byte scalar output bound reject atomically", limits_and_output_bound_fail_atomically},
    {"P7-TEST-008", "ERR-003", "malformed dimensions layout and profile metadata reject", malformed_dimensions_layout_and_metadata_fail_closed},
    {"P7-TEST-009", "UNC-002", "non-finite transform metadata is typed and atomic", nonfinite_transform_metadata_is_typed},
    {"P7-TEST-010", "ERR-003", "cancellation and expired deadline reject atomically", cancellation_and_expired_deadline_are_atomic},
    {"P7-TEST-011", "UNC-005", "disabled uncertainty is omitted; required uncertainty fails", uncertainty_is_omitted_or_rejected_when_required},
    {"P7-TEST-012", "ERR-004", "stable allowlisted messages do not disclose secret markers", error_messages_are_allowlisted_and_never_echo_secret_marker},
    {"P7-TEST-013", "ERR-002", "injected post-sample failure returns no partial metric", injected_failure_after_partial_scan_returns_nothing},
    {"P7-TEST-014", "ERR-002", "injected pre-publication failure discards candidate", injected_failure_before_publish_discards_candidate},
    {"P7-TEST-015", "ERR-002", "P4 admission failure has no view or input mutation", p4_admission_boundary_failure_is_atomic},
    {"P7-TEST-016", "ERR-002", "P5 canonicalization failure has no view or input mutation", p5_canonicalization_boundary_failure_is_atomic},
    {"P7-TEST-017", "ERR-002", "P6 operator failure has no planes or input mutation", p6_operator_boundary_failure_is_atomic},
    {"P7-TEST-018", "QUAL-001", "P4-to-P7 supported path is exact and read-only", p4_to_p7_supported_pipeline_is_exact_and_read_only},
}};

}  // namespace

int main() {
    std::size_t passed = 0U;
    for (const auto& test : kTests) {
        const bool ok = test.run();
        if (ok) ++passed;
        std::printf("CASE\t%s\t%s\t%s\t%s\n", test.id, ok ? "pass" : "fail",
                    test.catalog, test.label);
    }
    std::printf("SUMMARY\t%zu\t%zu\n", passed, kTests.size());
    return passed == kTests.size() ? 0 : 1;
}
