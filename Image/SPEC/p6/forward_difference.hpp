#pragma once

#include "../p5/canonical_raster.hpp"

#include <cstdint>
#include <string_view>
#include <vector>

namespace agi::image::p6 {

enum class ErrorCode : std::uint8_t {
    none,
    invalid_input,
    unsupported_layout,
    invalid_limits,
    resource_limit,
    cancelled,
    deadline_exceeded,
    allocation_failure,
};

// There are intentionally no implicit or profile-derived defaults. Every limit
// is supplied by the caller and is checked before output allocation.
struct Limits final {
    std::uint64_t max_pixels;
    std::uint32_t max_channels;
    std::uint64_t max_output_elements;
    std::uint64_t max_output_bytes;
    std::uint64_t max_work_units;
};

struct DifferencePlanes final {
    static constexpr std::string_view operator_version{"forward-difference-xy-v1"};
    static constexpr std::string_view coordinate_rule{"same_hwc_pixel_index_as_canonical_input"};

    std::uint64_t width{0};
    std::uint64_t height{0};
    std::uint64_t pixel_count{0};
    std::uint32_t channels{0};
    agi::image::p4::ChannelOrder channel_order{agi::image::p4::ChannelOrder::unknown};
    std::uint64_t output_elements{0};
    std::uint64_t output_bytes{0};
    std::uint64_t work_units{0};
    agi::image::p5::TransformRecord source_transform{};
    std::vector<std::int16_t> dx{};
    std::vector<std::int16_t> dy{};
};

struct Result final {
    ErrorCode error_code{ErrorCode::invalid_input};
    DifferencePlanes planes{};

    [[nodiscard]] bool has_value() const noexcept { return error_code == ErrorCode::none; }
    [[nodiscard]] bool retryable() const noexcept { return false; }
    [[nodiscard]] bool state_changed() const noexcept { return false; }
};

// Computes exactly two HWC int16 planes from an identity-canonical HWC uint8
// GRAY/RGB/RGBA raster. On any failure, both output vectors are empty.
[[nodiscard]] Result forward_difference_xy_v1(
    const agi::image::p5::CanonicalRasterView& source,
    const Limits& limits,
    const agi::image::p4::AdmissionControl& control) noexcept;

[[nodiscard]] const char* error_code_name(ErrorCode code) noexcept;

}  // namespace agi::image::p6
