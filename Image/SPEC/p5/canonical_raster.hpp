#pragma once

#include "../p4/raster_admission.hpp"

#include <array>
#include <cstdint>
#include <span>
#include <string_view>

namespace agi::image::p5 {

enum class ColorAction : std::uint8_t { preserve_source_samples, convert, infer };
enum class AlphaAction : std::uint8_t { preserve, composite, discard };
enum class OrientationAction : std::uint8_t { decoded_raster_only, apply, infer };
enum class GeometryOperation : std::uint8_t { identity, resize, crop, pad, other };
enum class ChannelAction : std::uint8_t { preserve_order, reorder };
enum class PixelFormat : std::uint8_t { gray_u8, rgb_u8, rgba_u8, unknown };
enum class ErrorCode : std::uint8_t {
    none, invalid_input, unsupported_policy, profile_mismatch, resource_limit
};

struct Limits final {
    std::uint64_t max_width;
    std::uint64_t max_height;
    std::uint64_t max_pixels;
    std::uint64_t max_output_bytes;
    std::uint64_t max_work_units;
};

struct Request final {
    std::string_view source_frame_id;
    std::string_view target_frame_id;
    std::string_view transform_id;
    std::string_view color_profile_id;
    ColorAction color_action{ColorAction::preserve_source_samples};
    AlphaAction alpha_action{AlphaAction::preserve};
    OrientationAction orientation_action{OrientationAction::decoded_raster_only};
    GeometryOperation geometry_operation{GeometryOperation::identity};
    ChannelAction channel_action{ChannelAction::preserve_order};
};

struct TransformRecord final {
    static constexpr std::string_view transform_version{"identity-v1"};
    static constexpr std::string_view coordinate_frame{
        "upper_left_origin_x_right_y_down_pixel_centers"};
    std::string_view transform_id;
    std::string_view source_frame_id;
    std::string_view target_frame_id;
    std::uint64_t source_width{0};
    std::uint64_t source_height{0};
    std::uint64_t target_width{0};
    std::uint64_t target_height{0};
    std::array<double, 9> matrix_3x3{};
    std::array<double, 9> inverse_matrix_3x3{};
    bool source_to_target{false};
    bool invertible{false};
};

struct CanonicalRasterView final {
    std::span<const std::uint8_t> samples{};
    std::uint64_t width{0};
    std::uint64_t height{0};
    std::uint64_t pixel_count{0};
    std::uint32_t channels{0};
    agi::image::p4::ChannelOrder channel_order{agi::image::p4::ChannelOrder::unknown};
    PixelFormat pixel_format{PixelFormat::unknown};
    std::string_view color_profile_id{};
    AlphaAction alpha_policy{AlphaAction::preserve};
    OrientationAction orientation_action{OrientationAction::decoded_raster_only};
    TransformRecord transform{};
};

struct Result final {
    ErrorCode error_code{ErrorCode::invalid_input};
    CanonicalRasterView raster{};

    [[nodiscard]] bool has_value() const noexcept { return error_code == ErrorCode::none; }
    [[nodiscard]] bool retryable() const noexcept { return false; }
    [[nodiscard]] bool state_changed() const noexcept { return false; }
};

// Accepts only an already admitted P4 tightly packed HWC uint8 GRAY/RGB/RGBA view.
// The result aliases the immutable input bytes: no sample is visited, copied,
// reordered, normalized, composited, color-converted, or spatially transformed.
// Identity source-center coordinates map exactly to the same target coordinates.
[[nodiscard]] Result canonicalize_identity(
    const agi::image::p4::RasterView& source,
    const Request& request,
    const Limits& limits) noexcept;

// Maps continuous coordinates within the closed pixel-center extent
// [0.5, width-0.5] × [0.5, height-0.5]. Degenerate extents remain valid;
// canonicalization rejects dimensions above 2^52 for exact binary64 centers.
[[nodiscard]] bool map_source_pixel_center(const TransformRecord& transform,
                                           double x_source,
                                           double y_source,
                                           double& x_target,
                                           double& y_target) noexcept;

[[nodiscard]] const char* error_code_name(ErrorCode code) noexcept;

}  // namespace agi::image::p5
