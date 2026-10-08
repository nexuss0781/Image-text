#include "canonical_raster.hpp"

#include <cmath>
#include <cstddef>
#include <limits>
#include <string_view>
#include <utility>

namespace agi::image::p5 {
namespace {

static_assert(std::numeric_limits<double>::is_iec559 &&
              std::numeric_limits<double>::digits == 53,
              "P5 pixel-center coordinates require IEEE-754 binary64");
constexpr std::uint64_t kMaxExactPixelCenterDimension = std::uint64_t{1} << 52U;

[[nodiscard]] bool checked_multiply(std::uint64_t a, std::uint64_t b,
                                    std::uint64_t& out) noexcept {
    if (a != 0 && b > std::numeric_limits<std::uint64_t>::max() / a) return false;
    out = a * b;
    return true;
}

[[nodiscard]] bool valid_identifier(std::string_view value) noexcept {
    if (value.empty() || value.size() > 128) return false;
    const auto first = static_cast<unsigned char>(value.front());
    const bool first_ok = (first >= 'A' && first <= 'Z') ||
                          (first >= 'a' && first <= 'z') ||
                          (first >= '0' && first <= '9');
    if (!first_ok) return false;
    for (const char character : value) {
        const auto byte = static_cast<unsigned char>(character);
        if (!((byte >= 'A' && byte <= 'Z') || (byte >= 'a' && byte <= 'z') ||
              (byte >= '0' && byte <= '9') || byte == '.' || byte == '_' ||
              byte == ':' || byte == '/' || byte == '-')) return false;
    }
    return true;
}

[[nodiscard]] Result failure(ErrorCode code) noexcept { return {code, {}}; }

}  // namespace

Result canonicalize_identity(const agi::image::p4::RasterView& source,
                             const Request& request,
                             const Limits& limits) noexcept {
    using agi::image::p4::ChannelOrder;
    if (request.color_action != ColorAction::preserve_source_samples ||
        request.alpha_action != AlphaAction::preserve ||
        request.orientation_action != OrientationAction::decoded_raster_only ||
        request.geometry_operation != GeometryOperation::identity ||
        request.channel_action != ChannelAction::preserve_order) {
        return failure(ErrorCode::unsupported_policy);
    }
    if (request.color_profile_id != "source-declared-or-unknown-v1" ||
        !valid_identifier(request.color_profile_id)) {
        return failure(ErrorCode::profile_mismatch);
    }
    if (!valid_identifier(request.source_frame_id) ||
        !valid_identifier(request.target_frame_id) ||
        !valid_identifier(request.transform_id)) {
        return failure(ErrorCode::invalid_input);
    }
    const std::uint64_t width = source.width();
    const std::uint64_t height = source.height();
    const std::uint32_t channels = source.channels();
    const auto order = source.channel_order();
    const std::uint32_t expected_channels =
        order == ChannelOrder::gray ? 1U :
        order == ChannelOrder::rgb ? 3U :
        order == ChannelOrder::rgba ? 4U : 0U;
    if (width == 0 || height == 0 || expected_channels == 0 || channels != expected_channels ||
        source.samples().data() == nullptr || source.samples().empty()) {
        return failure(ErrorCode::invalid_input);
    }
    if (limits.max_width == 0 || limits.max_height == 0 || limits.max_pixels == 0 ||
        limits.max_output_bytes == 0 || limits.max_work_units == 0) {
        return failure(ErrorCode::profile_mismatch);
    }
    if (width > limits.max_width || height > limits.max_height) {
        return failure(ErrorCode::resource_limit);
    }
    if (width > kMaxExactPixelCenterDimension || height > kMaxExactPixelCenterDimension) {
        return failure(ErrorCode::resource_limit);
    }
    std::uint64_t pixels = 0;
    std::uint64_t samples = 0;
    if (!checked_multiply(width, height, pixels) ||
        !checked_multiply(pixels, channels, samples) ||
        pixels > limits.max_pixels || samples > limits.max_output_bytes ||
        samples != source.samples().size() ||
        std::cmp_greater(samples, std::numeric_limits<std::size_t>::max()) ||
        std::cmp_greater(samples, std::numeric_limits<std::ptrdiff_t>::max())) {
        return failure(ErrorCode::resource_limit);
    }
    // The operation performs bounded metadata validation only; it never scans pixels.
    constexpr std::uint64_t metadata_work = 1;
    if (metadata_work > limits.max_work_units) return failure(ErrorCode::resource_limit);

    CanonicalRasterView output{};
    output.samples = source.samples();
    output.width = width;
    output.height = height;
    output.pixel_count = pixels;
    output.channels = channels;
    output.channel_order = order;
    output.pixel_format = order == ChannelOrder::gray ? PixelFormat::gray_u8 :
                          order == ChannelOrder::rgb ? PixelFormat::rgb_u8 :
                          PixelFormat::rgba_u8;
    output.color_profile_id = request.color_profile_id;
    output.alpha_policy = request.alpha_action;
    output.orientation_action = request.orientation_action;
    output.transform.transform_id = request.transform_id;
    output.transform.source_frame_id = request.source_frame_id;
    output.transform.target_frame_id = request.target_frame_id;
    output.transform.source_width = width;
    output.transform.source_height = height;
    output.transform.target_width = width;
    output.transform.target_height = height;
    output.transform.matrix_3x3 = {1.0, 0.0, 0.0,
                                   0.0, 1.0, 0.0,
                                   0.0, 0.0, 1.0};
    output.transform.inverse_matrix_3x3 = output.transform.matrix_3x3;
    output.transform.source_to_target = true;
    output.transform.invertible = true;
    return {ErrorCode::none, output};
}

bool map_source_pixel_center(const TransformRecord& transform,
                             double x_source,
                             double y_source,
                             double& x_target,
                             double& y_target) noexcept {
    constexpr std::array<double, 9> identity{1.0, 0.0, 0.0,
                                             0.0, 1.0, 0.0,
                                             0.0, 0.0, 1.0};
    if (!transform.source_to_target || !transform.invertible ||
        !valid_identifier(transform.transform_id) ||
        !valid_identifier(transform.source_frame_id) ||
        !valid_identifier(transform.target_frame_id) ||
        transform.source_width == 0 || transform.source_height == 0 ||
        transform.source_width > kMaxExactPixelCenterDimension ||
        transform.source_height > kMaxExactPixelCenterDimension ||
        transform.source_width != transform.target_width ||
        transform.source_height != transform.target_height ||
        transform.matrix_3x3 != identity || transform.inverse_matrix_3x3 != identity ||
        !std::isfinite(x_source) || !std::isfinite(y_source)) return false;
    const double min_x = 0.5;
    const double min_y = 0.5;
    const double max_x = static_cast<double>(transform.source_width) - 0.5;
    const double max_y = static_cast<double>(transform.source_height) - 0.5;
    if (x_source < min_x || x_source > max_x || y_source < min_y || y_source > max_y) {
        return false;
    }
    x_target = x_source;
    y_target = y_source;
    return true;
}

const char* error_code_name(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::none: return "NONE";
        case ErrorCode::invalid_input: return "INVALID_INPUT";
        case ErrorCode::unsupported_policy: return "UNSUPPORTED_POLICY";
        case ErrorCode::profile_mismatch: return "PROFILE_MISMATCH";
        case ErrorCode::resource_limit: return "RESOURCE_LIMIT";
    }
    return "INVALID_INPUT";
}

}  // namespace agi::image::p5
