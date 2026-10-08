#include "../../p4/raster_admission.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <new>
#include <span>
#include <stop_token>
#include <type_traits>
#include <utility>
#include <vector>
#include <initializer_list>
#include <string_view>

using agi::image::p4::AdmissionControl;
using agi::image::p4::AdmissionLimits;
using agi::image::p4::AdmissionResult;
using agi::image::p4::ChannelOrder;
using agi::image::p4::DecodeErrorCode;
using agi::image::p4::DecodeLimits;
using agi::image::p4::DecodedFormat;
using agi::image::p4::DecodeResult;
using agi::image::p4::ErrorCode;
using agi::image::p4::InputKind;
using agi::image::p4::Layout;
using agi::image::p4::RasterDescriptor;
using agi::image::p4::RasterView;
using agi::image::p4::SampleType;
using agi::image::p4::admit;
using agi::image::p4::decode_binary_pnm;

namespace {

std::atomic<std::uint64_t> g_heap_allocations{0};

// The allocation counter is sampled only around calls to admit(). Test setup,
// including the candidate-maximum buffer allocation, occurs outside that span.
[[nodiscard]] bool failure_is(const AdmissionResult& result, ErrorCode expected) noexcept {
    return !result.has_value() && result.error_code() == expected &&
           result.value() == nullptr && !result.retryable() && !result.state_changed();
}

constexpr AdmissionLimits kTinyLimits{5, 4, 20, 4, 80, 80};
constexpr AdmissionLimits kShapeLimits{5, 5, 25, 4, 100, 100};
// Copied from the proposal solely as a test ceiling. This is not an approved or
// production profile, and no runtime default is derived from it.
constexpr AdmissionLimits kProposalTestLimits{
    4096, 4096, 16777216, 4, 67108864, 67108864};
constexpr DecodeLimits kTinyDecodeLimits{1024, 128, 5, 5, 25, 4, 100, 1024};
constexpr DecodeLimits kProposalDecodeTestLimits{
    67108864, 65536, 4096, 4096, 16777216, 4, 67108864, 134217728};

[[nodiscard]] std::vector<std::uint8_t> make_pnm(
    std::string_view header, std::initializer_list<std::uint8_t> samples) {
    std::vector<std::uint8_t> encoded;
    encoded.reserve(header.size() + samples.size());
    for (const char byte : header) {
        encoded.push_back(static_cast<std::uint8_t>(static_cast<unsigned char>(byte)));
    }
    encoded.insert(encoded.end(), samples.begin(), samples.end());
    return encoded;
}

[[nodiscard]] bool decode_failure_is(const DecodeResult& result,
                                     DecodeErrorCode expected) noexcept {
    return !result.has_value() && result.error_code == expected &&
           result.raster.samples.empty() && !result.retryable() &&
           !result.state_changed();
}

[[nodiscard]] RasterDescriptor descriptor(std::uint64_t width,
                                          std::uint64_t height,
                                          std::uint32_t channels,
                                          ChannelOrder order) noexcept {
    const std::uint64_t pixel_stride = channels;
    const std::uint64_t row_stride = width * pixel_stride;
    const std::uint64_t bytes = row_stride * height;
    return {width, height, channels, Layout::hwc, order, SampleType::uint8,
            0, 255, row_stride, pixel_stride, 1, bytes};
}

[[nodiscard]] bool valid_small_shapes() noexcept {
    std::array<std::uint8_t, 80> data{};
    const auto one_pixel = descriptor(1, 1, 1, ChannelOrder::gray);
    const auto row = descriptor(5, 1, 3, ChannelOrder::rgb);
    const auto column = descriptor(1, 5, 4, ChannelOrder::rgba);
    const auto odd = descriptor(3, 5, 3, ChannelOrder::rgb);

    const auto a = admit(InputKind::decoded_raster, one_pixel,
                         std::span<const std::uint8_t>(data.data(), 1), kShapeLimits);
    const auto b = admit(InputKind::decoded_raster, row,
                         std::span<const std::uint8_t>(data.data(), 15), kShapeLimits);
    const auto c = admit(InputKind::decoded_raster, column,
                         std::span<const std::uint8_t>(data.data(), 20), kShapeLimits);
    const auto d = admit(InputKind::decoded_raster, odd,
                         std::span<const std::uint8_t>(data.data(), 45), kShapeLimits);
    return a.has_value() && a.value()->width() == 1 && a.value()->height() == 1 &&
           a.value()->pixel_count() == 1 && a.value()->channels() == 1 &&
           b.has_value() && b.value()->width() == 5 && b.value()->height() == 1 &&
           b.value()->pixel_count() == 5 && b.value()->channels() == 3 &&
           c.has_value() && c.value()->width() == 1 && c.value()->height() == 5 &&
           c.value()->pixel_count() == 5 && c.value()->channels() == 4 &&
           d.has_value() && d.value()->width() == 3 && d.value()->height() == 5 &&
           d.value()->pixel_count() == 15 && d.value()->channels() == 3 &&
           d.value()->work_units() == 45;
}

[[nodiscard]] bool supported_channel_classes() noexcept {
    std::array<std::uint8_t, 12> data{};
    const auto gray = descriptor(2, 2, 1, ChannelOrder::gray);
    const auto rgb = descriptor(2, 1, 3, ChannelOrder::rgb);
    const auto rgba = descriptor(1, 2, 4, ChannelOrder::rgba);
    return admit(InputKind::decoded_raster, gray,
                 std::span<const std::uint8_t>(data.data(), 4), kTinyLimits).has_value() &&
           admit(InputKind::decoded_raster, rgb,
                 std::span<const std::uint8_t>(data.data(), 6), kTinyLimits).has_value() &&
           admit(InputKind::decoded_raster, rgba,
                 std::span<const std::uint8_t>(data.data(), 8), kTinyLimits).has_value();
}

[[nodiscard]] bool zero_dimensions_reject() noexcept {
    std::array<std::uint8_t, 1> data{};
    auto d = descriptor(1, 1, 1, ChannelOrder::gray);
    d.width = 0;
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::invalid_descriptor)) return false;
    d = descriptor(1, 1, 1, ChannelOrder::gray);
    d.height = 0;
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::invalid_descriptor)) return false;
    d = descriptor(1, 1, 1, ChannelOrder::gray);
    d.channels = 0;
    return failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                      ErrorCode::invalid_descriptor);
}

[[nodiscard]] bool dimension_product_overflow_rejects() noexcept {
    constexpr auto u64max = std::numeric_limits<std::uint64_t>::max();
    constexpr AdmissionLimits broad{u64max, u64max, u64max, 4, u64max, u64max};
    RasterDescriptor d{u64max, 2, 1, Layout::hwc, ChannelOrder::gray,
                       SampleType::uint8, 0, 255, u64max, 1, 1, 0};
    return failure_is(admit(InputKind::decoded_raster, d, {}, broad),
                      ErrorCode::resource_limit);
}

[[nodiscard]] bool sample_count_overflow_rejects() noexcept {
    constexpr auto u64max = std::numeric_limits<std::uint64_t>::max();
    constexpr AdmissionLimits broad{u64max, u64max, u64max, 4, u64max, u64max};
    constexpr std::uint64_t width = u64max / 4 + 1;
    RasterDescriptor d{width, 1, 4, Layout::hwc, ChannelOrder::rgba,
                       SampleType::uint8, 0, 255, 0, 4, 1, 0};
    return failure_is(admit(InputKind::decoded_raster, d, {}, broad),
                      ErrorCode::resource_limit);
}

[[nodiscard]] bool stride_offset_overflow_rejects() noexcept {
    constexpr auto u64max = std::numeric_limits<std::uint64_t>::max();
    constexpr AdmissionLimits broad{u64max, u64max, u64max, 4, u64max, u64max};
    std::array<std::uint8_t, 4> data{};
    RasterDescriptor d{2, 2, 1, Layout::hwc, ChannelOrder::gray,
                       SampleType::uint8, 0, 255, u64max, u64max, 1, 4};
    return failure_is(admit(InputKind::decoded_raster, d, data, broad),
                      ErrorCode::resource_limit);
}

[[nodiscard]] bool host_pointer_difference_bound_rejects() noexcept {
    constexpr auto u64max = std::numeric_limits<std::uint64_t>::max();
    constexpr AdmissionLimits broad{u64max, u64max, u64max, 4, u64max, u64max};
    const auto width = static_cast<std::uint64_t>(std::numeric_limits<std::ptrdiff_t>::max()) + 1;
    RasterDescriptor d{width, 1, 1, Layout::hwc, ChannelOrder::gray,
                       SampleType::uint8, 0, 255, width, 1, 1, width};
    return failure_is(admit(InputKind::decoded_raster, d, {}, broad),
                      ErrorCode::resource_limit);
}

[[nodiscard]] bool malformed_stride_rejects() noexcept {
    std::array<std::uint8_t, 6> data{};
    auto d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.row_stride_bytes = 1;
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 4), kTinyLimits),
                    ErrorCode::invalid_descriptor)) return false;
    d = descriptor(2, 2, 3, ChannelOrder::rgb);
    d.pixel_stride_bytes = 2;
    return failure_is(admit(InputKind::decoded_raster, d,
                            std::span<const std::uint8_t>(data.data(), 12), kTinyLimits),
                      ErrorCode::invalid_descriptor);
}

[[nodiscard]] bool unknown_or_unsupported_declarations_reject() noexcept {
    std::array<std::uint8_t, 4> data{};
    auto d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.layout = Layout::planar;
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::unsupported_format)) return false;
    d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.sample_type = SampleType::uint16;
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::unsupported_format)) return false;
    d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.layout = static_cast<Layout>(255);
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::unsupported_format)) return false;
    d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.sample_type = static_cast<SampleType>(255);
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::unsupported_format)) return false;
    d = descriptor(2, 2, 3, ChannelOrder::bgr);
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 12), kTinyLimits),
                    ErrorCode::unsupported_format)) return false;
    d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.channel_order = static_cast<ChannelOrder>(255);
    return failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                      ErrorCode::unsupported_format);
}

[[nodiscard]] bool channel_and_range_inconsistency_reject() noexcept {
    std::array<std::uint8_t, 4> data{};
    auto d = descriptor(2, 2, 3, ChannelOrder::rgb);
    d.channels = 1;
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::invalid_descriptor)) return false;
    d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.sample_range_min = 10;
    d.sample_range_max = 200;
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                    ErrorCode::profile_mismatch)) return false;
    d.sample_range_min = 255;
    d.sample_range_max = 0;
    return failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits),
                      ErrorCode::invalid_descriptor);
}

[[nodiscard]] bool payload_length_and_empty_view_reject() noexcept {
    std::array<std::uint8_t, 8> data{};
    auto d = descriptor(2, 2, 1, ChannelOrder::gray);
    d.payload_bytes = 3;
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 4), kTinyLimits),
                    ErrorCode::invalid_descriptor)) return false;
    d = descriptor(2, 2, 1, ChannelOrder::gray);
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 3), kTinyLimits),
                    ErrorCode::invalid_descriptor)) return false;
    return failure_is(admit(InputKind::decoded_raster, d, {}, kTinyLimits),
                      ErrorCode::invalid_descriptor);
}

[[nodiscard]] bool each_proposal_limit_is_enforced() noexcept {
    std::array<std::uint8_t, 128> data{};
    auto d = descriptor(6, 1, 1, ChannelOrder::gray);
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 6), kTinyLimits),
                    ErrorCode::resource_limit)) return false;
    d = descriptor(1, 5, 1, ChannelOrder::gray);
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 5), kTinyLimits),
                    ErrorCode::resource_limit)) return false;
    auto pixels_limited = kTinyLimits;
    pixels_limited.max_pixels = 19;
    d = descriptor(5, 4, 1, ChannelOrder::gray);
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 20), pixels_limited),
                    ErrorCode::resource_limit)) return false;
    auto bytes_limited = kTinyLimits;
    bytes_limited.max_decoded_bytes = 79;
    d = descriptor(5, 4, 4, ChannelOrder::rgba);
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 80), bytes_limited),
                    ErrorCode::resource_limit)) return false;
    auto work_limited = kTinyLimits;
    work_limited.max_work_units = 79;
    if (!failure_is(admit(InputKind::decoded_raster, d,
                          std::span<const std::uint8_t>(data.data(), 80), work_limited),
                    ErrorCode::resource_limit)) return false;
    auto channel_limited = kTinyLimits;
    channel_limited.max_channels = 3;
    d = descriptor(1, 1, 4, ChannelOrder::rgba);
    return failure_is(admit(InputKind::decoded_raster, d,
                            std::span<const std::uint8_t>(data.data(), 4), channel_limited),
                      ErrorCode::resource_limit);
}

[[nodiscard]] bool tiny_profile_exact_boundary_accepts() noexcept {
    std::array<std::uint8_t, 80> data{};
    const auto d = descriptor(5, 4, 4, ChannelOrder::rgba);
    const auto result = admit(InputKind::decoded_raster, d, data, kTinyLimits);
    return result.has_value() && result.value()->pixel_count() == 20 &&
           result.value()->samples().size() == 80 && result.value()->work_units() == 80;
}

[[nodiscard]] bool proposal_maximum_boundary_accepts() {
    constexpr std::size_t bytes = 67108864;
    std::vector<std::uint8_t> data(bytes);
    const auto d = descriptor(4096, 4096, 4, ChannelOrder::rgba);
    const auto result = admit(InputKind::decoded_raster, d, data, kProposalTestLimits);
    return result.has_value() && result.value()->pixel_count() == 16777216 &&
           result.value()->samples().size() == bytes && result.value()->work_units() == 67108864;
}

[[nodiscard]] bool encoded_requests_fail_closed() noexcept {
    std::array<std::uint8_t, 4> encoded_bytes{0x89, 0x50, 0x4e, 0x47};
    const auto d = descriptor(1, 1, 1, ChannelOrder::gray);
    return failure_is(admit(InputKind::encoded_image, d, encoded_bytes, kProposalTestLimits),
                      ErrorCode::unsupported_format) &&
           failure_is(admit(InputKind::unknown, d, encoded_bytes, kProposalTestLimits),
                      ErrorCode::unsupported_format);
}

[[nodiscard]] bool invalid_limits_reject_profile_mismatch() noexcept {
    std::array<std::uint8_t, 1> data{};
    auto limits = kTinyLimits;
    limits.max_width = 0;
    return failure_is(admit(InputKind::decoded_raster,
                            descriptor(1, 1, 1, ChannelOrder::gray), data, limits),
                      ErrorCode::profile_mismatch);
}

[[nodiscard]] bool cancellation_deadline_and_precedence() noexcept {
    std::array<std::uint8_t, 1> data{};
    const auto d = descriptor(1, 1, 1, ChannelOrder::gray);
    std::stop_source source;
    source.request_stop();
    AdmissionControl cancelled{source.get_token(), false, {}};
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits, cancelled),
                    ErrorCode::cancelled)) return false;
    AdmissionControl expired{{}, true, std::chrono::steady_clock::time_point::min()};
    if (!failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits, expired),
                    ErrorCode::deadline_exceeded)) return false;
    expired.cancellation = source.get_token();
    return failure_is(admit(InputKind::decoded_raster, d, data, kTinyLimits, expired),
                      ErrorCode::cancelled);
}

[[nodiscard]] bool returned_view_is_read_only_borrow() noexcept {
    static_assert(std::is_same_v<decltype(std::declval<RasterView>().samples()),
                                 std::span<const std::uint8_t>>);
    std::array<std::uint8_t, 4> data{1, 2, 3, 4};
    const auto d = descriptor(2, 2, 1, ChannelOrder::gray);
    const auto result = admit(InputKind::decoded_raster, d, data, kTinyLimits);
    if (!result.has_value()) return false;
    const auto borrowed = result.value()->samples();
    return borrowed.data() == data.data() && borrowed.size() == data.size() &&
           borrowed[0] == 1 && borrowed[3] == 4;
}

[[nodiscard]] bool admission_success_and_rejection_do_not_allocate() noexcept {
    std::array<std::uint8_t, 1> data{};
    const auto d = descriptor(1, 1, 1, ChannelOrder::gray);
    auto before = g_heap_allocations.load(std::memory_order_relaxed);
    const auto accepted = admit(InputKind::decoded_raster, d, data, kTinyLimits);
    auto after_success = g_heap_allocations.load(std::memory_order_relaxed);
    auto constrained = kTinyLimits;
    constrained.max_width = 0;
    const auto rejected = admit(InputKind::decoded_raster, d, data, constrained);
    auto after_reject = g_heap_allocations.load(std::memory_order_relaxed);
    return accepted.has_value() && failure_is(rejected, ErrorCode::profile_mismatch) &&
           before == after_success && after_success == after_reject;
}

[[nodiscard]] bool oversized_rejection_precedes_any_allocation() noexcept {
    constexpr auto u64max = std::numeric_limits<std::uint64_t>::max();
    constexpr AdmissionLimits tiny{2, 2, 4, 4, 16, 16};
    RasterDescriptor d{u64max, u64max, 4, Layout::hwc, ChannelOrder::rgba,
                       SampleType::uint8, 0, 255, u64max, 4, 1, u64max};
    const auto before = g_heap_allocations.load(std::memory_order_relaxed);
    const auto result = admit(InputKind::decoded_raster, d, {}, tiny);
    const auto after = g_heap_allocations.load(std::memory_order_relaxed);
    return failure_is(result, ErrorCode::resource_limit) && before == after;
}

[[nodiscard]] bool pgm_p5_decodes_gray_exactly() {
    const auto encoded = make_pnm("P5\n# gray fixture\n2 2\n255\n",
                                  {0, static_cast<std::uint8_t>('#'),
                                   static_cast<std::uint8_t>('\n'),
                                   static_cast<std::uint8_t>(' ')});
    const auto result = decode_binary_pnm(encoded, kTinyDecodeLimits);
    return result.has_value() && result.raster.format == DecodedFormat::pgm_p5 &&
           result.raster.width == 2 && result.raster.height == 2 &&
           result.raster.channels == 1 && result.raster.channel_order == ChannelOrder::gray &&
           result.raster.samples.size() == 4 && result.raster.samples[0] == 0 &&
           result.raster.samples[1] == static_cast<std::uint8_t>('#') &&
           result.raster.samples[2] == static_cast<std::uint8_t>('\n') &&
           result.raster.samples[3] == static_cast<std::uint8_t>(' ') &&
           result.raster.work_units == encoded.size() + 4;
}

[[nodiscard]] bool ppm_p6_decodes_rgb_exactly() {
    const auto encoded = make_pnm("P6\r\n# rgb fixture\r\n2 1 255\r\n",
                                  {255, 0, 1, 2, 3, 4});
    const auto result = decode_binary_pnm(encoded, kTinyDecodeLimits);
    return result.has_value() && result.raster.format == DecodedFormat::ppm_p6 &&
           result.raster.width == 2 && result.raster.height == 1 &&
           result.raster.channels == 3 && result.raster.channel_order == ChannelOrder::rgb &&
           result.raster.samples.size() == 6 && result.raster.samples[0] == 255 &&
           result.raster.samples[1] == 0 && result.raster.samples[2] == 1 &&
           result.raster.samples[3] == 2 && result.raster.samples[4] == 3 &&
           result.raster.samples[5] == 4;
}

[[nodiscard]] bool unsupported_pnm_variants_and_ranges_reject() {
    const auto ascii_gray = make_pnm("P2\n1 1\n255\n", {0});
    const auto ascii_rgb = make_pnm("P3\n1 1\n255\n", {0});
    const auto low_max = make_pnm("P5\n1 1\n15\n", {0});
    const auto high_max = make_pnm("P6\n1 1\n256\n", {0, 0, 0});
    return decode_failure_is(decode_binary_pnm(ascii_gray, kTinyDecodeLimits),
                             DecodeErrorCode::unsupported_format) &&
           decode_failure_is(decode_binary_pnm(ascii_rgb, kTinyDecodeLimits),
                             DecodeErrorCode::unsupported_format) &&
           decode_failure_is(decode_binary_pnm(low_max, kTinyDecodeLimits),
                             DecodeErrorCode::unsupported_format) &&
           decode_failure_is(decode_binary_pnm(high_max, kTinyDecodeLimits),
                             DecodeErrorCode::unsupported_format);
}

[[nodiscard]] bool malformed_pnm_headers_reject() {
    const auto bad_width = make_pnm("P5\nx 1\n255\n", {0});
    const auto zero_dimension = make_pnm("P5\n0 1\n255\n", {0});
    const auto missing_separator = make_pnm("P5\n1 1\n255", {0});
    const auto post_max_comment = make_pnm("P5\n1 1\n255# comment\n", {0});
    const auto overflow_width = make_pnm("P5\n18446744073709551616 1\n255\n", {0});
    return decode_failure_is(decode_binary_pnm(bad_width, kTinyDecodeLimits),
                             DecodeErrorCode::malformed_header) &&
           decode_failure_is(decode_binary_pnm(zero_dimension, kTinyDecodeLimits),
                             DecodeErrorCode::malformed_header) &&
           decode_failure_is(decode_binary_pnm(missing_separator, kTinyDecodeLimits),
                             DecodeErrorCode::malformed_header) &&
           decode_failure_is(decode_binary_pnm(post_max_comment, kTinyDecodeLimits),
                             DecodeErrorCode::malformed_header) &&
           decode_failure_is(decode_binary_pnm(overflow_width, kTinyDecodeLimits),
                             DecodeErrorCode::malformed_header);
}

[[nodiscard]] bool truncated_and_extra_payload_reject() {
    const auto truncated = make_pnm("P5\n2 1\n255\n", {42});
    const auto extra = make_pnm("P5\n1 1\n255\n", {42, 43});
    return decode_failure_is(decode_binary_pnm(truncated, kTinyDecodeLimits),
                             DecodeErrorCode::corrupt_payload) &&
           decode_failure_is(decode_binary_pnm(extra, kTinyDecodeLimits),
                             DecodeErrorCode::corrupt_payload);
}

[[nodiscard]] bool decoder_resource_limits_preflight_without_allocation() {
    const auto encoded = make_pnm("P6\n2 1\n255\n", {1, 2, 3, 4, 5, 6});
    auto encoded_cap = kTinyDecodeLimits;
    encoded_cap.max_encoded_bytes = encoded.size() - 1;
    encoded_cap.max_header_bytes = encoded.size() - 1;
    auto header_cap = kTinyDecodeLimits;
    header_cap.max_header_bytes = 8;
    auto width_cap = kTinyDecodeLimits;
    width_cap.max_width = 1;
    auto pixel_cap = kTinyDecodeLimits;
    pixel_cap.max_pixels = 1;
    auto channel_cap = kTinyDecodeLimits;
    channel_cap.max_channels = 2;
    auto bytes_cap = kTinyDecodeLimits;
    bytes_cap.max_decoded_bytes = 5;
    auto work_cap = kTinyDecodeLimits;
    work_cap.max_work_units = encoded.size() + 5;
    const auto before = g_heap_allocations.load(std::memory_order_relaxed);
    const bool all_reject =
        decode_failure_is(decode_binary_pnm(encoded, encoded_cap), DecodeErrorCode::resource_limit) &&
        decode_failure_is(decode_binary_pnm(encoded, header_cap), DecodeErrorCode::resource_limit) &&
        decode_failure_is(decode_binary_pnm(encoded, width_cap), DecodeErrorCode::resource_limit) &&
        decode_failure_is(decode_binary_pnm(encoded, pixel_cap), DecodeErrorCode::resource_limit) &&
        decode_failure_is(decode_binary_pnm(encoded, channel_cap), DecodeErrorCode::resource_limit) &&
        decode_failure_is(decode_binary_pnm(encoded, bytes_cap), DecodeErrorCode::resource_limit) &&
        decode_failure_is(decode_binary_pnm(encoded, work_cap), DecodeErrorCode::resource_limit);
    const auto after = g_heap_allocations.load(std::memory_order_relaxed);
    return all_reject && before == after;
}

[[nodiscard]] bool huge_dimensions_reject_before_allocation() {
    const auto encoded = make_pnm("P5\n4294967296 4294967296\n255\n", {});
    const auto before = g_heap_allocations.load(std::memory_order_relaxed);
    const auto result = decode_binary_pnm(encoded, kTinyDecodeLimits);
    const auto after = g_heap_allocations.load(std::memory_order_relaxed);
    return decode_failure_is(result, DecodeErrorCode::resource_limit) && before == after;
}

[[nodiscard]] bool header_byte_limit_rejects_long_comment() {
    const auto encoded = make_pnm("P5\n#0123456789012345678901234567890123456789\n1 1\n255\n", {0});
    auto limits = kTinyDecodeLimits;
    limits.max_header_bytes = 16;
    return decode_failure_is(decode_binary_pnm(encoded, limits), DecodeErrorCode::resource_limit);
}

[[nodiscard]] bool decoder_cancellation_and_deadline_are_atomic() {
    const auto encoded = make_pnm("P5\n1 1\n255\n", {7});
    std::stop_source source;
    source.request_stop();
    const AdmissionControl cancelled{source.get_token(), false, {}};
    const AdmissionControl expired{{}, true, std::chrono::steady_clock::time_point::min()};
    return decode_failure_is(decode_binary_pnm(encoded, kTinyDecodeLimits, cancelled),
                             DecodeErrorCode::cancelled) &&
           decode_failure_is(decode_binary_pnm(encoded, kTinyDecodeLimits, expired),
                             DecodeErrorCode::deadline_exceeded);
}

[[nodiscard]] bool decoder_exact_small_limits_accept() {
    const auto encoded = make_pnm("P6\n2 1\n255\n", {1, 2, 3, 4, 5, 6});
    const DecodeLimits exact{static_cast<std::uint64_t>(encoded.size()), 11, 2, 1, 2, 3, 6,
                             static_cast<std::uint64_t>(encoded.size()) + 6};
    const auto result = decode_binary_pnm(encoded, exact);
    return result.has_value() && result.raster.samples.size() == 6 &&
           result.raster.width == 2 && result.raster.height == 1;
}

[[nodiscard]] bool concatenated_images_reject_as_multipage() {
    const auto encoded = make_pnm("P5\n1 1\n255\n",
                                  {7, 'P', '5', '\n', '1', ' ', '1', '\n',
                                   '2', '5', '5', '\n', 8});
    return decode_failure_is(decode_binary_pnm(encoded, kTinyDecodeLimits),
                             DecodeErrorCode::corrupt_payload);
}

[[nodiscard]] bool encoded_admission_stays_separate_from_decoder() noexcept {
    const std::array<std::uint8_t, 3> encoded{'P', '5', '\n'};
    const auto d = descriptor(1, 1, 1, ChannelOrder::gray);
    return failure_is(admit(InputKind::encoded_image, d, encoded, kTinyLimits),
                      ErrorCode::unsupported_format);
}

[[nodiscard]] bool proposal_pixel_boundary_pgm_decodes() {
    constexpr std::uint64_t pixels = 16777216;
    constexpr std::string_view header = "P5\n4096 4096\n255\n";
    std::vector<std::uint8_t> encoded;
    encoded.reserve(header.size() + static_cast<std::size_t>(pixels));
    for (const char byte : header) {
        encoded.push_back(static_cast<std::uint8_t>(static_cast<unsigned char>(byte)));
    }
    encoded.resize(header.size() + static_cast<std::size_t>(pixels), 127);
    const auto result = decode_binary_pnm(encoded, kProposalDecodeTestLimits);
    return result.has_value() && result.raster.width == 4096 && result.raster.height == 4096 &&
           result.raster.channels == 1 && result.raster.samples.size() == pixels &&
           result.raster.samples.front() == 127 && result.raster.samples.back() == 127;
}

struct Test final {
    const char* id;
    const char* catalog_case;
    const char* label;
    bool (*run)();
};

const std::array<Test, 33> kTests{{
    {"P4-TEST-001", "ADM-001", "positive single/row/column/odd raster shapes", valid_small_shapes},
    {"P4-TEST-002", "ADM-001", "GRAY/RGB/RGBA channel classes", supported_channel_classes},
    {"P4-TEST-003", "ADM-002", "zero width/height/channels", zero_dimensions_reject},
    {"P4-TEST-004", "ADM-003", "width-height multiplication overflow", dimension_product_overflow_rejects},
    {"P4-TEST-005", "ADM-003", "pixel-channel sample-count overflow", sample_count_overflow_rejects},
    {"P4-TEST-006", "ADM-004", "checked stride-offset addition and multiplication overflow", stride_offset_overflow_rejects},
    {"P4-TEST-007", "ADM-003", "host pointer-difference representability bound", host_pointer_difference_bound_rejects},
    {"P4-TEST-008", "ADM-004", "short row and pixel strides", malformed_stride_rejects},
    {"P4-TEST-009", "ADM-005", "unsupported layout/type/order and unknown enum", unknown_or_unsupported_declarations_reject},
    {"P4-TEST-010", "ADM-005", "channel count and declared-range consistency", channel_and_range_inconsistency_reject},
    {"P4-TEST-011", "ADM-001", "declared/actual buffer length and empty input", payload_length_and_empty_view_reject},
    {"P4-TEST-012", "ADM-003", "width/height/pixel/channel/byte/work ceilings", each_proposal_limit_is_enforced},
    {"P4-TEST-013", "ADM-001", "small-profile exact boundary", tiny_profile_exact_boundary_accepts},
    {"P4-TEST-014", "ADM-001", "proposal-only maximum 4096x4096x4 boundary", proposal_maximum_boundary_accepts},
    {"P4-TEST-015", "ADM-006", "descriptor admission keeps encoded decode on its explicit API", encoded_requests_fail_closed},
    {"P4-TEST-016", "ADM-005", "invalid limit record fails with profile mismatch", invalid_limits_reject_profile_mismatch},
    {"P4-TEST-017", "ADM-007", "cancellation/deadline typed reject and precedence", cancellation_deadline_and_precedence},
    {"P4-TEST-018", "ADM-001", "read-only non-owning view aliases caller storage", returned_view_is_read_only_borrow},
    {"P4-TEST-019", "ADM-001", "success and failure paths perform no heap allocation", admission_success_and_rejection_do_not_allocate},
    {"P4-TEST-020", "ADM-003", "over-limit rejection occurs before allocation", oversized_rejection_precedes_any_allocation},
    {"P4-TEST-021", "DEC-001", "binary PGM P5 gray pixels decode exactly with comments", pgm_p5_decodes_gray_exactly},
    {"P4-TEST-022", "DEC-001", "binary PPM P6 RGB pixels decode exactly", ppm_p6_decodes_rgb_exactly},
    {"P4-TEST-023", "DEC-002", "ASCII variants and non-255 maxval reject", unsupported_pnm_variants_and_ranges_reject},
    {"P4-TEST-024", "DEC-003", "malformed header tokens and separators reject", malformed_pnm_headers_reject},
    {"P4-TEST-025", "DEC-003", "truncated and extra raster bytes reject atomically", truncated_and_extra_payload_reject},
    {"P4-TEST-026", "ADM-003", "encoded/header/dimension/channel/byte/work caps preflight", decoder_resource_limits_preflight_without_allocation},
    {"P4-TEST-027", "ADM-003", "huge dimensions reject before output allocation", huge_dimensions_reject_before_allocation},
    {"P4-TEST-028", "ADM-003", "header byte ceiling bounds comment scanning", header_byte_limit_rejects_long_comment},
    {"P4-TEST-029", "ADM-007", "decoder cancellation and deadline return empty typed failures", decoder_cancellation_and_deadline_are_atomic},
    {"P4-TEST-030", "DEC-001", "exact small test limits accept valid P6 at boundary", decoder_exact_small_limits_accept},
    {"P4-TEST-031", "DEC-004", "concatenated/multipage PNM input rejects", concatenated_images_reject_as_multipage},
    {"P4-TEST-032", "ADM-006", "descriptor admission remains separate from PNM decoder", encoded_admission_stays_separate_from_decoder},
    {"P4-TEST-033", "DEC-001", "proposal-only 4096x4096 pixel ceiling PGM decodes", proposal_pixel_boundary_pgm_decodes},
}};

}  // namespace

void* operator new(std::size_t size) {
    g_heap_allocations.fetch_add(1, std::memory_order_relaxed);
    if (void* const allocation = std::malloc(size == 0 ? 1 : size)) return allocation;
    throw std::bad_alloc();
}

void* operator new[](std::size_t size) {
    g_heap_allocations.fetch_add(1, std::memory_order_relaxed);
    if (void* const allocation = std::malloc(size == 0 ? 1 : size)) return allocation;
    throw std::bad_alloc();
}

void operator delete(void* allocation) noexcept { std::free(allocation); }
void operator delete[](void* allocation) noexcept { std::free(allocation); }
void operator delete(void* allocation, std::size_t) noexcept { std::free(allocation); }
void operator delete[](void* allocation, std::size_t) noexcept { std::free(allocation); }

void* operator new(std::size_t size, std::align_val_t alignment) {
    g_heap_allocations.fetch_add(1, std::memory_order_relaxed);
    const auto alignment_size = static_cast<std::size_t>(alignment);
    const auto requested = size == 0 ? std::size_t{1} : size;
    if (requested > std::numeric_limits<std::size_t>::max() - (alignment_size - 1)) {
        throw std::bad_alloc();
    }
    const auto rounded = ((requested + alignment_size - 1) / alignment_size) * alignment_size;
    if (void* const allocation = std::aligned_alloc(alignment_size, rounded)) return allocation;
    throw std::bad_alloc();
}

void* operator new[](std::size_t size, std::align_val_t alignment) {
    return ::operator new(size, alignment);
}

void operator delete(void* allocation, std::align_val_t) noexcept { std::free(allocation); }
void operator delete[](void* allocation, std::align_val_t) noexcept { std::free(allocation); }
void operator delete(void* allocation, std::size_t, std::align_val_t) noexcept { std::free(allocation); }
void operator delete[](void* allocation, std::size_t, std::align_val_t) noexcept { std::free(allocation); }

int main() {
    std::size_t passed = 0;
    for (const auto& test : kTests) {
        const bool ok = test.run();
        std::printf("CASE\t%s\t%s\t%s\t%s\n", test.id, ok ? "pass" : "fail",
                    test.catalog_case, test.label);
        passed += ok ? 1U : 0U;
    }
    std::printf("SUMMARY\t%zu\t%zu\n", passed, kTests.size());
    return passed == kTests.size() ? 0 : 1;
}
