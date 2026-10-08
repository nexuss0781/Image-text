#include "quality_indicator.hpp"

#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string_view>
#include <utility>

namespace agi::image::p7 {
namespace {

constexpr std::uint64_t kMaxExactPixelCenterDimension = std::uint64_t{1} << 52U;
constexpr std::uint64_t kOutputPayloadBytes =
    sizeof(std::uint64_t) * 2U + sizeof(double);
constexpr std::array<double, 9> kIdentity{
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0,
};

static_assert(sizeof(std::uint64_t) == 8U);
static_assert(sizeof(double) == 8U);
static_assert(std::numeric_limits<double>::is_iec559 &&
              std::numeric_limits<double>::digits == 53);

[[nodiscard]] bool checked_multiply(std::uint64_t left, std::uint64_t right,
                                    std::uint64_t& output) noexcept {
    if (left != 0U && right > std::numeric_limits<std::uint64_t>::max() / left) {
        return false;
    }
    output = left * right;
    return true;
}

[[nodiscard]] bool valid_identifier(std::string_view value) noexcept {
    if (value.empty() || value.size() > 128U) return false;
    const auto first = static_cast<unsigned char>(value.front());
    const bool first_ok = (first >= 'A' && first <= 'Z') ||
                          (first >= 'a' && first <= 'z') ||
                          (first >= '0' && first <= '9');
    if (!first_ok) return false;
    for (const char character : value) {
        const auto byte = static_cast<unsigned char>(character);
        if (!((byte >= 'A' && byte <= 'Z') || (byte >= 'a' && byte <= 'z') ||
              (byte >= '0' && byte <= '9') || byte == '.' || byte == '_' ||
              byte == ':' || byte == '/' || byte == '-')) {
            return false;
        }
    }
    return true;
}

[[nodiscard]] ErrorCode check_control(
    const agi::image::p4::AdmissionControl& control) noexcept {
    if (control.cancellation.stop_requested()) return ErrorCode::cancelled;
    if (control.has_deadline && std::chrono::steady_clock::now() >= control.deadline) {
        return ErrorCode::deadline_exceeded;
    }
    return ErrorCode::none;
}

[[nodiscard]] Result failure(ErrorCode code) noexcept {
    return {code, std::nullopt, std::nullopt};
}

[[nodiscard]] Result measure_impl(
    const agi::image::p5::CanonicalRasterView& source,
    const Limits& limits,
    const Options& options,
    const agi::image::p4::AdmissionControl& control,
    bool inject_after_first_sample,
    bool inject_before_publish) noexcept {
    using agi::image::p4::ChannelOrder;
    using agi::image::p5::PixelFormat;

    const ErrorCode initial_control = check_control(control);
    if (initial_control != ErrorCode::none) return failure(initial_control);

    if (limits.max_pixels == 0U || limits.max_channels == 0U ||
        limits.max_channels > 4U || limits.max_output_bytes == 0U ||
        limits.max_work_units == 0U) {
        return failure(ErrorCode::resource_limit);
    }

    const std::uint32_t color_channels =
        source.channel_order == ChannelOrder::gray ? 1U :
        (source.channel_order == ChannelOrder::rgb ||
         source.channel_order == ChannelOrder::rgba) ? 3U : 0U;
    const std::uint32_t expected_channels =
        source.channel_order == ChannelOrder::gray ? 1U :
        source.channel_order == ChannelOrder::rgb ? 3U :
        source.channel_order == ChannelOrder::rgba ? 4U : 0U;
    const PixelFormat expected_format =
        source.channel_order == ChannelOrder::gray ? PixelFormat::gray_u8 :
        source.channel_order == ChannelOrder::rgb ? PixelFormat::rgb_u8 :
        source.channel_order == ChannelOrder::rgba ? PixelFormat::rgba_u8 : PixelFormat::unknown;
    if (expected_channels == 0U || source.channels != expected_channels ||
        source.pixel_format != expected_format) {
        return failure(ErrorCode::unsupported_format);
    }
    if (source.color_profile_id != "source-declared-or-unknown-v1" ||
        source.alpha_policy != agi::image::p5::AlphaAction::preserve ||
        source.orientation_action != agi::image::p5::OrientationAction::decoded_raster_only) {
        return failure(ErrorCode::profile_mismatch);
    }

    if (source.width == 0U || source.height == 0U || source.samples.data() == nullptr ||
        source.samples.empty() || !valid_identifier(source.transform.transform_id) ||
        !valid_identifier(source.transform.source_frame_id) ||
        !valid_identifier(source.transform.target_frame_id) ||
        source.transform.source_width != source.width ||
        source.transform.source_height != source.height ||
        source.transform.target_width != source.width ||
        source.transform.target_height != source.height ||
        !source.transform.source_to_target || !source.transform.invertible) {
        return failure(ErrorCode::invalid_descriptor);
    }
    for (const double value : source.transform.matrix_3x3) {
        if (!std::isfinite(value)) return failure(ErrorCode::nonfinite_input);
    }
    for (const double value : source.transform.inverse_matrix_3x3) {
        if (!std::isfinite(value)) return failure(ErrorCode::nonfinite_input);
    }
    if (source.transform.matrix_3x3 != kIdentity ||
        source.transform.inverse_matrix_3x3 != kIdentity) {
        return failure(ErrorCode::invalid_descriptor);
    }

    std::uint64_t pixels = 0U;
    std::uint64_t input_samples = 0U;
    std::uint64_t denominator = 0U;
    if (!checked_multiply(source.width, source.height, pixels) ||
        !checked_multiply(pixels, expected_channels, input_samples) ||
        !checked_multiply(pixels, color_channels, denominator)) {
        return failure(ErrorCode::resource_limit);
    }
    if (pixels != source.pixel_count || !std::cmp_equal(input_samples, source.samples.size())) {
        return failure(ErrorCode::invalid_descriptor);
    }
    if (source.width > kMaxExactPixelCenterDimension ||
        source.height > kMaxExactPixelCenterDimension ||
        pixels > limits.max_pixels || expected_channels > limits.max_channels ||
        denominator > limits.max_work_units || kOutputPayloadBytes > limits.max_output_bytes ||
        std::cmp_greater(input_samples, std::numeric_limits<std::size_t>::max()) ||
        std::cmp_greater(input_samples, std::numeric_limits<std::ptrdiff_t>::max()) ||
        denominator == 0U) {
        return failure(ErrorCode::resource_limit);
    }

    if (options.require_uncertainty) {
        return failure(ErrorCode::uncertainty_unavailable);
    }

    const ErrorCode pre_scan_control = check_control(control);
    if (pre_scan_control != ErrorCode::none) return failure(pre_scan_control);

    const auto width = static_cast<std::size_t>(source.width);
    const auto height = static_cast<std::size_t>(source.height);
    const auto channels = static_cast<std::size_t>(expected_channels);
    const auto colors = static_cast<std::size_t>(color_channels);
    std::uint64_t numerator = 0U;
    std::uint64_t completed_work = 0U;
    for (std::size_t y = 0U; y < height; ++y) {
        const ErrorCode row_control = check_control(control);
        if (row_control != ErrorCode::none) return failure(row_control);
        const std::size_t row_base = y * width * channels;
        for (std::size_t x = 0U; x < width; ++x) {
            const std::size_t pixel_base = row_base + x * channels;
            for (std::size_t channel = 0U; channel < colors; ++channel) {
                const std::uint8_t sample = source.samples[pixel_base + channel];
                if (sample == 0U || sample == 255U) ++numerator;
                ++completed_work;
                if (inject_after_first_sample && completed_work == 1U) {
                    return failure(ErrorCode::internal_error);
                }
                if ((completed_work & 1023U) == 0U) {
                    const ErrorCode periodic_control = check_control(control);
                    if (periodic_control != ErrorCode::none) return failure(periodic_control);
                }
            }
        }
    }

    const ErrorCode final_control = check_control(control);
    if (final_control != ErrorCode::none) return failure(final_control);
    if (completed_work != denominator || numerator > denominator) {
        return failure(ErrorCode::internal_error);
    }
    const double value = static_cast<double>(numerator) / static_cast<double>(denominator);
    if (!std::isfinite(value) || value < 0.0 || value > 1.0) {
        return failure(ErrorCode::nonfinite_input);
    }
    if (inject_before_publish) return failure(ErrorCode::internal_error);

    QualityIndicator indicator{};
    indicator.numerator = numerator;
    indicator.denominator = denominator;
    indicator.value = value;
    indicator.work_units = completed_work;
    indicator.output_payload_bytes = kOutputPayloadBytes;
    Result result{};
    result.error_code = ErrorCode::none;
    result.quality = indicator;
    // Uncertainty remains absent: no uncertainty producer exists in this slice.
    return result;
}

}  // namespace

Result measure_endpoint_code_fraction_v1(
    const agi::image::p5::CanonicalRasterView& source,
    const Limits& limits,
    const Options& options,
    const agi::image::p4::AdmissionControl& control) noexcept {
    return measure_impl(source, limits, options, control, false, false);
}

#ifdef AGI_IMAGE_P7_TESTING
Result measure_endpoint_code_fraction_v1_with_test_fault(
    const agi::image::p5::CanonicalRasterView& source,
    const Limits& limits,
    const Options& options,
    const agi::image::p4::AdmissionControl& control,
    testing::FaultPoint fault) noexcept {
    return measure_impl(source, limits, options, control,
                        fault == testing::FaultPoint::after_first_sample,
                        fault == testing::FaultPoint::before_publish);
}
#endif

const char* error_code_name(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::none: return "NONE";
        case ErrorCode::invalid_descriptor: return "INVALID_DESCRIPTOR";
        case ErrorCode::unsupported_format: return "UNSUPPORTED_FORMAT";
        case ErrorCode::profile_mismatch: return "PROFILE_MISMATCH";
        case ErrorCode::resource_limit: return "RESOURCE_LIMIT";
        case ErrorCode::nonfinite_input: return "NONFINITE_INPUT";
        case ErrorCode::uncertainty_unavailable: return "UNCERTAINTY_UNAVAILABLE";
        case ErrorCode::cancelled: return "CANCELLED";
        case ErrorCode::deadline_exceeded: return "DEADLINE_EXCEEDED";
        case ErrorCode::internal_error: return "INTERNAL_ERROR";
    }
    return "INTERNAL_ERROR";
}

const char* error_message(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::none: return "";
        case ErrorCode::invalid_descriptor:
            return "Input does not satisfy the canonical raster contract.";
        case ErrorCode::unsupported_format:
            return "Raster layout is not supported by the quality method.";
        case ErrorCode::resource_limit:
            return "Caller-supplied quality limits are exceeded.";
        case ErrorCode::nonfinite_input:
            return "Input metadata contains a non-finite numeric value.";
        case ErrorCode::uncertainty_unavailable:
            return "Required uncertainty is unavailable under this profile.";
        case ErrorCode::cancelled:
            return "Request was cancelled before quality completion.";
        case ErrorCode::deadline_exceeded:
            return "Request deadline elapsed before quality completion.";
        case ErrorCode::internal_error:
            return "Quality analysis could not be completed.";
        case ErrorCode::profile_mismatch:
            return "Raster policy does not match the selected profile.";
    }
    return "Quality analysis could not be completed.";
}

}  // namespace agi::image::p7
