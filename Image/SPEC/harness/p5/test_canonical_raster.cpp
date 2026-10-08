#include "../../p4/raster_admission.hpp"
#include "../../p5/canonical_raster.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <span>
#include <string_view>
#include <vector>

using agi::image::p4::AdmissionLimits;
using agi::image::p4::ChannelOrder;
using agi::image::p4::InputKind;
using agi::image::p4::Layout;
using agi::image::p4::RasterDescriptor;
using agi::image::p4::SampleType;
using agi::image::p4::admit;
using agi::image::p5::AlphaAction;
using agi::image::p5::ChannelAction;
using agi::image::p5::ColorAction;
using agi::image::p5::ErrorCode;
using agi::image::p5::GeometryOperation;
using agi::image::p5::Limits;
using agi::image::p5::OrientationAction;
using agi::image::p5::Request;
using agi::image::p5::Result;
using agi::image::p5::canonicalize_identity;
using agi::image::p5::map_source_pixel_center;

namespace {
constexpr AdmissionLimits kAdmission{64, 64, 4096, 4, 16384, 16384};
constexpr Limits kLimits{64, 64, 4096, 16384, 1};

[[nodiscard]] RasterDescriptor make_descriptor(std::uint64_t width, std::uint64_t height,
                                               std::uint32_t channels,
                                               ChannelOrder order) noexcept {
    const std::uint64_t pixel_stride = channels;
    const std::uint64_t row_stride = width * pixel_stride;
    return {width, height, channels, Layout::hwc, order, SampleType::uint8,
            0, 255, row_stride, pixel_stride, 1, row_stride * height};
}

[[nodiscard]] Request request() noexcept {
    return {"source-frame", "canonical-frame", "identity-main-v1",
            "source-declared-or-unknown-v1"};
}

[[nodiscard]] bool failed_closed(const Result& result, ErrorCode expected) noexcept {
    return !result.has_value() && result.error_code == expected &&
           result.raster.samples.empty() && result.raster.width == 0 &&
           result.raster.height == 0 && result.raster.pixel_count == 0 &&
           result.raster.channels == 0 && !result.state_changed();
}

[[nodiscard]] bool exact_identity(std::uint64_t width, std::uint64_t height,
                                  std::uint32_t channels, ChannelOrder order,
                                  const std::vector<std::uint8_t>& input,
                                  const std::vector<std::uint8_t>& oracle) noexcept {
    if (input != oracle) return false;
    const auto descriptor = make_descriptor(width, height, channels, order);
    const auto admission = admit(InputKind::decoded_raster, descriptor, input, kAdmission);
    if (!admission.has_value()) return false;
    const auto result = canonicalize_identity(*admission.value(), request(), kLimits);
    return result.has_value() && result.raster.samples.data() == input.data() &&
           result.raster.samples.size() == oracle.size() &&
           std::equal(oracle.begin(), oracle.end(), result.raster.samples.begin()) &&
           result.raster.width == width && result.raster.height == height &&
           result.raster.channels == channels && result.raster.channel_order == order;
}

[[nodiscard]] bool one_pixel_gray() noexcept {
    const std::vector<std::uint8_t> values{173};
    const std::vector<std::uint8_t> oracle{173};
    const auto descriptor = make_descriptor(1, 1, 1, ChannelOrder::gray);
    const auto admitted = admit(InputKind::decoded_raster, descriptor, values, kAdmission);
    if (!admitted.has_value()) return false;
    const auto result = canonicalize_identity(*admitted.value(), request(), kLimits);
    return result.has_value() && result.raster.pixel_format == agi::image::p5::PixelFormat::gray_u8 &&
           result.raster.pixel_count == 1 && result.raster.samples.data() == values.data() &&
           std::equal(oracle.begin(), oracle.end(), result.raster.samples.begin());
}

[[nodiscard]] bool one_row_rgba_alpha_exact() noexcept {
    const std::vector<std::uint8_t> values{255, 0, 0, 0, 0, 255, 0, 128,
                                           0, 0, 255, 255, 23, 45, 67, 1};
    const std::vector<std::uint8_t> oracle{255, 0, 0, 0, 0, 255, 0, 128,
                                           0, 0, 255, 255, 23, 45, 67, 1};
    if (!exact_identity(4, 1, 4, ChannelOrder::rgba, values, oracle)) return false;
    const auto admitted = admit(InputKind::decoded_raster,
        make_descriptor(4, 1, 4, ChannelOrder::rgba), values, kAdmission);
    if (!admitted.has_value()) return false;
    const auto result = canonicalize_identity(*admitted.value(), request(), kLimits);
    return result.raster.pixel_format == agi::image::p5::PixelFormat::rgba_u8 &&
           result.raster.alpha_policy == AlphaAction::preserve;
}

[[nodiscard]] bool one_column_rgb() noexcept {
    const std::vector<std::uint8_t> values{1, 23, 240, 88, 129, 5, 255, 127, 0};
    const std::vector<std::uint8_t> oracle{1, 23, 240, 88, 129, 5, 255, 127, 0};
    return exact_identity(1, 3, 3, ChannelOrder::rgb, values, oracle);
}

[[nodiscard]] bool odd_gray_exact() noexcept {
    const std::vector<std::uint8_t> values{0, 7, 63, 127, 128, 254, 255, 19, 211, 42, 99, 3, 180, 240, 61};
    const std::vector<std::uint8_t> oracle{0, 7, 63, 127, 128, 254, 255, 19, 211, 42, 99, 3, 180, 240, 61};
    return exact_identity(3, 5, 1, ChannelOrder::gray, values, oracle);
}

[[nodiscard]] bool odd_rgb_exact() noexcept {
    const std::vector<std::uint8_t> values{0,1,2, 30,40,50, 250,240,230,
                                           7,17,27, 80,90,100, 130,140,150,
                                           255,128,0, 1,128,255, 66,77,88};
    const std::vector<std::uint8_t> oracle{0,1,2, 30,40,50, 250,240,230,
                                           7,17,27, 80,90,100, 130,140,150,
                                           255,128,0, 1,128,255, 66,77,88};
    return exact_identity(3, 3, 3, ChannelOrder::rgb, values, oracle);
}

[[nodiscard]] bool odd_rgba_exact_alpha() noexcept {
    const std::vector<std::uint8_t> values{11,22,33,0, 44,55,66,64,
                                           77,88,99,128, 100,110,120,192,
                                           130,140,150,255, 201,202,203,17};
    const std::vector<std::uint8_t> oracle{11,22,33,0, 44,55,66,64,
                                           77,88,99,128, 100,110,120,192,
                                           130,140,150,255, 201,202,203,17};
    return exact_identity(2, 3, 4, ChannelOrder::rgba, values, oracle);
}

[[nodiscard]] bool identity_pixel_center_map() noexcept {
    const std::vector<std::uint8_t> values{8, 9, 10, 11, 12, 13};
    const auto admitted = admit(InputKind::decoded_raster,
        make_descriptor(3, 2, 1, ChannelOrder::gray), values, kAdmission);
    if (!admitted.has_value()) return false;
    const auto result = canonicalize_identity(*admitted.value(), request(), kLimits);
    if (!result.has_value()) return false;
    const auto& transform = result.raster.transform;
    constexpr std::array<double, 9> identity{1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0};
    if (transform.source_width != 3 || transform.target_width != 3 ||
        transform.source_height != 2 || transform.target_height != 2 ||
        transform.matrix_3x3 != identity || transform.inverse_matrix_3x3 != identity ||
        !transform.invertible || !transform.source_to_target) return false;
    constexpr std::array<std::array<double, 2>, 5> points{{
        {0.5,0.5}, {2.5,0.5}, {0.5,1.5}, {2.5,1.5}, {1.5,1.5}}};
    for (const auto& point : points) {
        double x = -1.0;
        double y = -1.0;
        if (!map_source_pixel_center(transform, point[0], point[1], x, y) ||
            x != point[0] || y != point[1]) return false;
    }
    double x = 0.0;
    double y = 0.0;
    if (map_source_pixel_center(transform, 0.0, 0.5, x, y) ||
        map_source_pixel_center(transform, 3.0, 1.5, x, y) ||
        map_source_pixel_center(transform, 0.5, 2.0, x, y)) return false;
    auto malformed = transform;
    malformed.matrix_3x3[0] = 2.0;
    if (map_source_pixel_center(malformed, 0.5, 0.5, x, y)) return false;
    malformed = transform;
    malformed.source_width = (std::uint64_t{1} << 52U) + 1U;
    malformed.target_width = malformed.source_width;
    if (map_source_pixel_center(malformed, 0.5, 0.5, x, y)) return false;
    malformed = transform;
    malformed.target_frame_id = "bad frame";
    if (map_source_pixel_center(malformed, 0.5, 0.5, x, y)) return false;

    const auto degenerate_map = [](std::uint64_t width, std::uint64_t height,
                                   double center_x, double center_y) noexcept {
        const std::vector<std::uint8_t> pixels(static_cast<std::size_t>(width * height), 0);
        const auto admitted_input = admit(InputKind::decoded_raster,
            make_descriptor(width, height, 1, ChannelOrder::gray), pixels, kAdmission);
        if (!admitted_input.has_value()) return false;
        const auto canonical = canonicalize_identity(*admitted_input.value(), request(), kLimits);
        if (!canonical.has_value()) return false;
        double mapped_x = -1.0;
        double mapped_y = -1.0;
        return map_source_pixel_center(canonical.raster.transform, center_x, center_y,
                                       mapped_x, mapped_y) &&
               mapped_x == center_x && mapped_y == center_y;
    };
    return degenerate_map(1, 1, 0.5, 0.5) &&
           degenerate_map(4, 1, 3.5, 0.5) &&
           degenerate_map(1, 4, 0.5, 3.5);
}

[[nodiscard]] bool disabled_policies_reject() noexcept {
    const std::vector<std::uint8_t> values{1,2,3,4};
    const auto admitted = admit(InputKind::decoded_raster,
        make_descriptor(2, 2, 1, ChannelOrder::gray), values, kAdmission);
    if (!admitted.has_value()) return false;
    auto r = request();
    r.geometry_operation = GeometryOperation::resize;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.geometry_operation = GeometryOperation::crop;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.geometry_operation = GeometryOperation::pad;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.geometry_operation = GeometryOperation::other;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.color_action = ColorAction::convert;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.color_action = ColorAction::infer;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.channel_action = ChannelAction::reorder;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.alpha_action = AlphaAction::discard;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.alpha_action = AlphaAction::composite;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.orientation_action = OrientationAction::apply;
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy)) return false;
    r = request(); r.orientation_action = OrientationAction::infer;
    return failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::unsupported_policy);
}

[[nodiscard]] bool limits_and_invalid_input_reject() noexcept {
    const std::vector<std::uint8_t> values{1,2,3,4};
    const auto admitted = admit(InputKind::decoded_raster,
        make_descriptor(2, 2, 1, ChannelOrder::gray), values, kAdmission);
    if (!admitted.has_value()) return false;
    auto tiny = kLimits; tiny.max_output_bytes = 3;
    if (!failed_closed(canonicalize_identity(*admitted.value(), request(), tiny), ErrorCode::resource_limit)) return false;
    tiny = kLimits; tiny.max_work_units = 0;
    if (!failed_closed(canonicalize_identity(*admitted.value(), request(), tiny), ErrorCode::profile_mismatch)) return false;
    tiny = kLimits; tiny.max_width = 1;
    if (!failed_closed(canonicalize_identity(*admitted.value(), request(), tiny), ErrorCode::resource_limit)) return false;
    tiny = kLimits; tiny.max_pixels = 3;
    if (!failed_closed(canonicalize_identity(*admitted.value(), request(), tiny), ErrorCode::resource_limit)) return false;
    auto r = request(); r.color_profile_id = "";
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::profile_mismatch)) return false;
    r = request(); r.color_profile_id = "srgb-v1";
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::profile_mismatch)) return false;
    r = request(); r.source_frame_id = "bad frame";
    if (!failed_closed(canonicalize_identity(*admitted.value(), r, kLimits), ErrorCode::invalid_input)) return false;
    const agi::image::p4::RasterView empty{};
    if (!failed_closed(canonicalize_identity(empty, request(), kLimits), ErrorCode::invalid_input)) return false;
    auto unsupported = make_descriptor(2, 2, 1, ChannelOrder::gray);
    unsupported.layout = Layout::planar;
    if (admit(InputKind::decoded_raster, unsupported, values, kAdmission).error_code() !=
        agi::image::p4::ErrorCode::unsupported_format) return false;
    unsupported = make_descriptor(2, 2, 3, ChannelOrder::bgr);
    return admit(InputKind::decoded_raster, unsupported, values, kAdmission).error_code() ==
           agi::image::p4::ErrorCode::unsupported_format;
}

[[nodiscard]] bool overflow_rejects_before_canonicalization() noexcept {
    constexpr std::uint64_t max = std::numeric_limits<std::uint64_t>::max();
    constexpr AdmissionLimits broad{max, max, max, 4, max, max};
    const RasterDescriptor overflow{max, 2, 1, Layout::hwc, ChannelOrder::gray,
                                    SampleType::uint8, 0, 255, max, 1, 1, 0};
    const auto rejected = admit(InputKind::decoded_raster, overflow, {}, broad);
    return !rejected.has_value() && rejected.error_code() == agi::image::p4::ErrorCode::resource_limit &&
           failed_closed(canonicalize_identity(agi::image::p4::RasterView{}, request(), kLimits),
                         ErrorCode::invalid_input);
}

struct TestCase final { const char* id; const char* catalog; const char* label; bool (*run)() noexcept; };
constexpr std::array<TestCase, 10> kTests{{
    {"P5-TEST-001", "PIX-005", "1x1 GRAY exact-value identity view", one_pixel_gray},
    {"P5-TEST-002", "PIX-005", "1xN RGBA preserves all alpha samples", one_row_rgba_alpha_exact},
    {"P5-TEST-003", "PIX-005", "Nx1 RGB exact-value identity view", one_column_rgb},
    {"P5-TEST-004", "PIX-005", "odd 3x5 GRAY exact-value oracle", odd_gray_exact},
    {"P5-TEST-005", "PIX-005", "odd 3x3 RGB exact-value oracle", odd_rgb_exact},
    {"P5-TEST-006", "PIX-005", "odd 2x3 RGBA exact alpha oracle", odd_rgba_exact_alpha},
    {"P5-TEST-007", "GEO-006", "identity dimensions matrix inverse and pixel centers", identity_pixel_center_map},
    {"P5-TEST-008", "PIX-006", "conversion reorder orientation resize and alpha loss reject", disabled_policies_reject},
    {"P5-TEST-009", "PIX-006", "limits metadata declarations and empty input reject", limits_and_invalid_input_reject},
    {"P5-TEST-010", "PIX-006", "overflow rejected before producing canonical view", overflow_rejects_before_canonicalization},
}};
}

int main() {
    std::size_t passed = 0;
    for (const auto& test : kTests) {
        const bool success = test.run();
        passed += success ? 1U : 0U;
        std::printf("CASE\t%s\t%s\t%s\t%s\n", test.id, success ? "pass" : "fail",
                    test.catalog, test.label);
    }
    std::printf("SUMMARY\t%zu\t%zu\n", passed, kTests.size());
    return passed == kTests.size() ? 0 : 1;
}
