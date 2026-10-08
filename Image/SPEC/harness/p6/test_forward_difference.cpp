#include "../../p4/raster_admission.hpp"
#include "../../p5/canonical_raster.hpp"
#include "../../p6/forward_difference.hpp"

#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <span>
#include <stop_token>
#include <string_view>
#include <vector>

using agi::image::p4::AdmissionControl;
using agi::image::p4::ChannelOrder;
using agi::image::p5::CanonicalRasterView;
using agi::image::p5::PixelFormat;
using agi::image::p6::ErrorCode;
using agi::image::p6::Limits;
using agi::image::p6::Result;
using agi::image::p6::forward_difference_xy_v1;

namespace {

constexpr Limits kLimits{4096U, 4U, 8192U, 16384U, 8192U};
const AdmissionControl kNoControl{};

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
    return !result.has_value() && result.error_code == expected &&
           result.planes.width == 0U && result.planes.height == 0U &&
           result.planes.pixel_count == 0U && result.planes.channels == 0U &&
           result.planes.output_elements == 0U && result.planes.output_bytes == 0U &&
           result.planes.work_units == 0U && result.planes.dx.empty() &&
           result.planes.dy.empty() && !result.state_changed();
}

[[nodiscard]] bool exact(
    std::uint64_t width, std::uint64_t height, std::uint32_t channels,
    ChannelOrder order, const std::vector<std::uint8_t>& input,
    const std::vector<std::int16_t>& expected_dx,
    const std::vector<std::int16_t>& expected_dy) noexcept {
    const auto view = make_view(width, height, channels, order, input);
    const Result result = forward_difference_xy_v1(view, kLimits, kNoControl);
    const std::uint64_t samples = width * height * channels;
    return result.has_value() && result.planes.width == width &&
           result.planes.height == height && result.planes.pixel_count == width * height &&
           result.planes.channels == channels && result.planes.channel_order == order &&
           result.planes.dx == expected_dx && result.planes.dy == expected_dy &&
           result.planes.dx.size() == samples && result.planes.dy.size() == samples &&
           result.planes.output_elements == 2U * samples &&
           result.planes.output_bytes == 4U * samples &&
           result.planes.work_units == 2U * samples &&
           result.planes.source_transform.transform_id == view.transform.transform_id &&
           result.planes.source_transform.source_width == width &&
           result.planes.source_transform.target_height == height;
}

[[nodiscard]] bool constant_field() noexcept {
    const std::vector<std::uint8_t> input{5, 5, 5, 5, 5, 5};
    const std::vector<std::int16_t> zero(6U, 0);
    return exact(3U, 2U, 1U, ChannelOrder::gray, input, zero, zero);
}

[[nodiscard]] bool impulse_sign_and_location() noexcept {
    const std::vector<std::uint8_t> input{0,0,0, 0,1,0, 0,0,0};
    const std::vector<std::int16_t> dx{0,0,0, 1,-1,0, 0,0,0};
    const std::vector<std::int16_t> dy{0,1,0, 0,-1,0, 0,0,0};
    return exact(3U, 3U, 1U, ChannelOrder::gray, input, dx, dy);
}

[[nodiscard]] bool horizontal_ramp_and_one_row() noexcept {
    const std::vector<std::uint8_t> input{0,1,3,6};
    const std::vector<std::int16_t> dx{1,2,3,0};
    const std::vector<std::int16_t> dy{0,0,0,0};
    return exact(4U, 1U, 1U, ChannelOrder::gray, input, dx, dy);
}

[[nodiscard]] bool vertical_ramp_and_one_column() noexcept {
    const std::vector<std::uint8_t> input{0,2,5,9};
    const std::vector<std::int16_t> dx{0,0,0,0};
    const std::vector<std::int16_t> dy{2,3,4,0};
    return exact(1U, 4U, 1U, ChannelOrder::gray, input, dx, dy);
}

[[nodiscard]] bool checkerboard_and_one_by_one() noexcept {
    const std::vector<std::uint8_t> checker{0,1,1,0};
    const std::vector<std::int16_t> checker_dx{1,0,-1,0};
    const std::vector<std::int16_t> checker_dy{1,-1,0,0};
    if (!exact(2U, 2U, 1U, ChannelOrder::gray, checker, checker_dx, checker_dy)) return false;
    const std::vector<std::uint8_t> single{173};
    const std::vector<std::int16_t> zero{0};
    return exact(1U, 1U, 1U, ChannelOrder::gray, single, zero, zero);
}

[[nodiscard]] bool rgb_channel_order_is_preserved() noexcept {
    const std::vector<std::uint8_t> input{
        1,20,200, 10,40,150,
        50,5,90, 70,25,30,
    };
    const std::vector<std::int16_t> dx{
        9,20,-50, 0,0,0,
        20,20,-60, 0,0,0,
    };
    const std::vector<std::int16_t> dy{
        49,-15,-110, 60,-15,-120,
        0,0,0, 0,0,0,
    };
    return exact(2U, 2U, 3U, ChannelOrder::rgb, input, dx, dy);
}

[[nodiscard]] bool rgba_channel_and_alpha_order_is_preserved() noexcept {
    const std::vector<std::uint8_t> input{
        2,30,80,255, 12,10,50,0,
        7,60,20,128, 0,40,220,64,
    };
    const std::vector<std::int16_t> dx{
        10,-20,-30,-255, 0,0,0,0,
        -7,-20,200,-64, 0,0,0,0,
    };
    const std::vector<std::int16_t> dy{
        5,30,-60,-127, -12,30,170,64,
        0,0,0,0, 0,0,0,0,
    };
    return exact(2U, 2U, 4U, ChannelOrder::rgba, input, dx, dy);
}

[[nodiscard]] bool seeded_rgb_vector_matches_literal_oracle() noexcept {
    const std::vector<std::uint8_t> input{
        31,25,40, 157,204,231, 140,23,66, 206,239,190,
        10,31,169, 106,252,198, 7,252,187, 114,178,79,
        249,125,169, 131,193,25, 52,156,106, 247,38,85,
    };
    const std::vector<std::int16_t> dx{
        126,179,191, -17,-181,-165, 66,216,124, 0,0,0,
        96,221,29, -99,0,-11, 107,-74,-108, 0,0,0,
        -118,68,-144, -79,-37,81, 195,-118,-21, 0,0,0,
    };
    const std::vector<std::int16_t> dy{
        -21,6,129, -51,48,-33, -133,229,121, -92,-61,-111,
        239,94,0, 25,-59,-173, 45,-96,-81, 133,-140,6,
        0,0,0, 0,0,0, 0,0,0, 0,0,0,
    };
    return exact(4U, 3U, 3U, ChannelOrder::rgb, input, dx, dy);
}

[[nodiscard]] bool deterministic_replay_has_fixed_work_and_outputs() noexcept {
    const std::vector<std::uint8_t> input{
        0,10,250, 255,30,0, 17,200,64, 90,90,90,
        5,40,240, 200,0,10, 255,128,1, 1,254,128,
        255,255,255, 0,0,0, 128,64,32, 254,2,127,
    };
    const auto view = make_view(4U, 3U, 3U, ChannelOrder::rgb, input);
    const Result first = forward_difference_xy_v1(view, kLimits, kNoControl);
    const Result second = forward_difference_xy_v1(view, kLimits, kNoControl);
    return first.has_value() && second.has_value() &&
           first.planes.dx == second.planes.dx && first.planes.dy == second.planes.dy &&
           first.planes.work_units == second.planes.work_units &&
           first.planes.work_units == 72U && first.planes.output_elements == 72U &&
           first.planes.output_bytes == 144U;
}

[[nodiscard]] bool limits_and_invalid_limit_values_fail_closed() noexcept {
    const std::vector<std::uint8_t> input{1,2,3,4};
    const auto view = make_view(2U, 2U, 1U, ChannelOrder::gray, input);
    Limits tiny = kLimits;
    tiny.max_pixels = 3U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::resource_limit)) return false;
    tiny = kLimits; tiny.max_channels = 0U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::invalid_limits)) return false;
    tiny = kLimits; tiny.max_channels = 5U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::invalid_limits)) return false;
    const std::vector<std::uint8_t> rgba_input{8,9,10,11};
    const auto rgba_view = make_view(1U, 1U, 4U, ChannelOrder::rgba, rgba_input);
    tiny = kLimits; tiny.max_channels = 3U;
    if (!failed_closed(forward_difference_xy_v1(rgba_view, tiny, kNoControl), ErrorCode::resource_limit)) return false;
    tiny = kLimits; tiny.max_output_elements = 7U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::resource_limit)) return false;
    tiny = kLimits; tiny.max_output_elements = 0U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::invalid_limits)) return false;
    tiny = kLimits; tiny.max_output_bytes = 15U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::resource_limit)) return false;
    tiny = kLimits; tiny.max_output_bytes = 0U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::invalid_limits)) return false;
    tiny = kLimits; tiny.max_work_units = 7U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::resource_limit)) return false;
    tiny = kLimits; tiny.max_work_units = 0U;
    if (!failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::invalid_limits)) return false;
    tiny = kLimits; tiny.max_pixels = 0U;
    return failed_closed(forward_difference_xy_v1(view, tiny, kNoControl), ErrorCode::invalid_limits);
}

[[nodiscard]] bool unsupported_channels_and_mismatched_metadata_reject() noexcept {
    const std::vector<std::uint8_t> input{1,2,3,4,5,6,7,8};
    auto view = make_view(2U, 1U, 2U, ChannelOrder::unknown, input);
    if (!failed_closed(forward_difference_xy_v1(view, kLimits, kNoControl), ErrorCode::unsupported_layout)) return false;
    view = make_view(2U, 1U, 3U, ChannelOrder::bgr, input);
    if (!failed_closed(forward_difference_xy_v1(view, kLimits, kNoControl), ErrorCode::unsupported_layout)) return false;
    view = make_view(2U, 1U, 3U, ChannelOrder::rgb, input);
    view.pixel_format = PixelFormat::rgba_u8;
    if (!failed_closed(forward_difference_xy_v1(view, kLimits, kNoControl), ErrorCode::unsupported_layout)) return false;
    view = make_view(2U, 1U, 1U, ChannelOrder::gray, input);
    view.pixel_count = 9U;
    if (!failed_closed(forward_difference_xy_v1(view, kLimits, kNoControl), ErrorCode::resource_limit)) return false;
    view = make_view(2U, 1U, 1U, ChannelOrder::gray, input);
    view.transform.matrix_3x3[0] = 2.0;
    return failed_closed(forward_difference_xy_v1(view, kLimits, kNoControl), ErrorCode::invalid_input);
}

[[nodiscard]] bool arithmetic_overflow_and_empty_input_reject() noexcept {
    CanonicalRasterView invalid{};
    const Result empty = forward_difference_xy_v1(invalid, kLimits, kNoControl);
    if (!failed_closed(empty, ErrorCode::invalid_input)) return false;

    const std::uint8_t byte = 1U;
    auto overflow = make_view(std::numeric_limits<std::uint64_t>::max(), 2U, 1U,
                              ChannelOrder::gray, std::span<const std::uint8_t>(&byte, 1U));
    return failed_closed(forward_difference_xy_v1(overflow, kLimits, kNoControl),
                         ErrorCode::resource_limit);
}

[[nodiscard]] bool cancellation_and_deadline_leave_no_planes() noexcept {
    const std::vector<std::uint8_t> input{1,2,3,4};
    const auto view = make_view(2U, 2U, 1U, ChannelOrder::gray, input);
    std::stop_source stop;
    stop.request_stop();
    AdmissionControl cancelled{};
    cancelled.cancellation = stop.get_token();
    if (!failed_closed(forward_difference_xy_v1(view, kLimits, cancelled), ErrorCode::cancelled)) return false;
    AdmissionControl expired{};
    expired.has_deadline = true;
    expired.deadline = std::chrono::steady_clock::now() - std::chrono::seconds(1);
    return failed_closed(forward_difference_xy_v1(view, kLimits, expired), ErrorCode::deadline_exceeded);
}

struct TestCase final {
    const char* id;
    const char* catalog;
    const char* label;
    bool (*run)() noexcept;
};

constexpr std::array<TestCase, 13> kTests{{
    {"P6-TEST-001", "DIF-001", "constant field gives two zero planes", constant_field},
    {"P6-TEST-002", "DIF-001", "center impulse sign and localization", impulse_sign_and_location},
    {"P6-TEST-003", "DIF-001", "horizontal ramp and one-row edge", horizontal_ramp_and_one_row},
    {"P6-TEST-004", "DIF-001", "vertical ramp and one-column edge", vertical_ramp_and_one_column},
    {"P6-TEST-005", "DIF-001", "checkerboard and explicit one-by-one", checkerboard_and_one_by_one},
    {"P6-TEST-006", "DIF-002", "RGB HWC channel order and output shape", rgb_channel_order_is_preserved},
    {"P6-TEST-007", "DIF-002", "RGBA channel and alpha-position order", rgba_channel_and_alpha_order_is_preserved},
    {"P6-TEST-008", "DIF-003", "seeded RGB byte vector literal oracle", seeded_rgb_vector_matches_literal_oracle},
    {"P6-TEST-009", "DIF-003", "deterministic replay preserves exact outputs and work", deterministic_replay_has_fixed_work_and_outputs},
    {"P6-TEST-010", "DIF-004", "pixels channels elements bytes and work limits", limits_and_invalid_limit_values_fail_closed},
    {"P6-TEST-011", "DIF-004", "unsupported channels and malformed metadata", unsupported_channels_and_mismatched_metadata_reject},
    {"P6-TEST-012", "DIF-004", "checked arithmetic overflow and empty input", arithmetic_overflow_and_empty_input_reject},
    {"P6-TEST-013", "DIF-005", "cancellation and expired deadline are atomic", cancellation_and_deadline_leave_no_planes},
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
