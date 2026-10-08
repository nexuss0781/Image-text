#include "forward_difference.hpp"

#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <new>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

namespace agi::image::p6 {
namespace {

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

[[nodiscard]] bool identity_transform_matches(
    const agi::image::p5::TransformRecord& transform,
    std::uint64_t width, std::uint64_t height) noexcept {
    constexpr std::array<double, 9> identity{
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0,
    };
    return transform.source_to_target && transform.invertible &&
           valid_identifier(transform.transform_id) &&
           valid_identifier(transform.source_frame_id) &&
           valid_identifier(transform.target_frame_id) &&
           transform.source_width == width && transform.target_width == width &&
           transform.source_height == height && transform.target_height == height &&
           transform.matrix_3x3 == identity &&
           transform.inverse_matrix_3x3 == identity;
}

[[nodiscard]] ErrorCode check_control(
    const agi::image::p4::AdmissionControl& control) noexcept {
    if (control.cancellation.stop_requested()) return ErrorCode::cancelled;
    if (control.has_deadline && std::chrono::steady_clock::now() >= control.deadline) {
        return ErrorCode::deadline_exceeded;
    }
    return ErrorCode::none;
}

[[nodiscard]] Result failure(ErrorCode code) noexcept { return {code, {}}; }

}  // namespace

Result forward_difference_xy_v1(
    const agi::image::p5::CanonicalRasterView& source,
    const Limits& limits,
    const agi::image::p4::AdmissionControl& control) noexcept {
    using agi::image::p4::ChannelOrder;
    using agi::image::p5::PixelFormat;

    const ErrorCode initial_control = check_control(control);
    if (initial_control != ErrorCode::none) return failure(initial_control);

    if (limits.max_pixels == 0U || limits.max_channels == 0U ||
        limits.max_channels > 4U || limits.max_output_elements == 0U ||
        limits.max_output_bytes == 0U || limits.max_work_units == 0U) {
        return failure(ErrorCode::invalid_limits);
    }

    const std::uint64_t width = source.width;
    const std::uint64_t height = source.height;
    const std::uint32_t channels = source.channels;
    const auto order = source.channel_order;
    if (width == 0U || height == 0U || source.samples.data() == nullptr ||
        source.samples.empty() || !identity_transform_matches(source.transform, width, height)) {
        return failure(ErrorCode::invalid_input);
    }
    const std::uint32_t expected_channels =
        order == ChannelOrder::gray ? 1U :
        order == ChannelOrder::rgb ? 3U :
        order == ChannelOrder::rgba ? 4U : 0U;
    const PixelFormat expected_format =
        order == ChannelOrder::gray ? PixelFormat::gray_u8 :
        order == ChannelOrder::rgb ? PixelFormat::rgb_u8 :
        order == ChannelOrder::rgba ? PixelFormat::rgba_u8 : PixelFormat::unknown;
    if (expected_channels == 0U || channels != expected_channels ||
        source.pixel_format != expected_format) {
        return failure(ErrorCode::unsupported_layout);
    }

    std::uint64_t pixels = 0U;
    std::uint64_t samples = 0U;
    std::uint64_t row_samples = 0U;
    std::uint64_t output_elements = 0U;
    std::uint64_t output_bytes = 0U;
    std::uint64_t work_units = 0U;
    if (!checked_multiply(width, height, pixels) ||
        !checked_multiply(pixels, channels, samples) ||
        !checked_multiply(width, channels, row_samples) ||
        !checked_multiply(samples, 2U, output_elements) ||
        !checked_multiply(output_elements, sizeof(std::int16_t), output_bytes)) {
        return failure(ErrorCode::resource_limit);
    }
    work_units = output_elements;  // One unit per directional output value.

    const std::vector<std::int16_t> empty_vector{};
    const std::uint64_t vector_max_size = static_cast<std::uint64_t>(empty_vector.max_size());
    const std::uint64_t size_max = static_cast<std::uint64_t>(
        std::numeric_limits<std::size_t>::max());
    const std::uint64_t ptrdiff_max = static_cast<std::uint64_t>(
        std::numeric_limits<std::ptrdiff_t>::max());
    if (pixels != source.pixel_count || samples != source.samples.size() ||
        pixels > limits.max_pixels || channels > limits.max_channels ||
        output_elements > limits.max_output_elements ||
        output_bytes > limits.max_output_bytes || work_units > limits.max_work_units ||
        samples > vector_max_size || samples > size_max / sizeof(std::int16_t) ||
        samples > ptrdiff_max / sizeof(std::int16_t) ||
        output_elements > size_max || output_bytes > size_max || output_bytes > ptrdiff_max ||
        row_samples > size_max) {
        return failure(ErrorCode::resource_limit);
    }

    const ErrorCode preallocation_control = check_control(control);
    if (preallocation_control != ErrorCode::none) return failure(preallocation_control);

    try {
        const auto sample_count = static_cast<std::size_t>(samples);
        std::vector<std::int16_t> dx(sample_count);
        std::vector<std::int16_t> dy(sample_count);
        const ErrorCode postallocation_control = check_control(control);
        if (postallocation_control != ErrorCode::none) return failure(postallocation_control);

        const auto width_size = static_cast<std::size_t>(width);
        const auto height_size = static_cast<std::size_t>(height);
        const auto channels_size = static_cast<std::size_t>(channels);
        const auto row_samples_size = static_cast<std::size_t>(row_samples);
        std::uint64_t completed_work = 0U;
        for (std::size_t y = 0U; y < height_size; ++y) {
            const ErrorCode row_control = check_control(control);
            if (row_control != ErrorCode::none) return failure(row_control);
            const std::size_t next_y = y == height_size - 1U ? y : y + 1U;
            const std::size_t row_base = y * row_samples_size;
            const std::size_t next_row_base = next_y * row_samples_size;
            for (std::size_t x = 0U; x < width_size; ++x) {
                const std::size_t next_x = x == width_size - 1U ? x : x + 1U;
                const std::size_t pixel_offset = x * channels_size;
                const std::size_t right_offset = next_x * channels_size;
                const std::size_t current = row_base + pixel_offset;
                const std::size_t right = row_base + right_offset;
                const std::size_t down = next_row_base + pixel_offset;
                for (std::size_t channel = 0U; channel < channels_size; ++channel) {
                    const std::size_t index = current + channel;
                    const std::int32_t sample = static_cast<std::int32_t>(source.samples[index]);
                    const std::int32_t right_sample =
                        static_cast<std::int32_t>(source.samples[right + channel]);
                    const std::int32_t down_sample =
                        static_cast<std::int32_t>(source.samples[down + channel]);
                    dx[index] = static_cast<std::int16_t>(right_sample - sample);
                    dy[index] = static_cast<std::int16_t>(down_sample - sample);
                    completed_work += 2U;
                    if ((completed_work & 2047U) == 0U) {
                        const ErrorCode periodic_control = check_control(control);
                        if (periodic_control != ErrorCode::none) return failure(periodic_control);
                    }
                }
            }
        }
        const ErrorCode final_control = check_control(control);
        if (final_control != ErrorCode::none) return failure(final_control);
        if (completed_work != work_units) return failure(ErrorCode::resource_limit);

        DifferencePlanes planes{};
        planes.width = width;
        planes.height = height;
        planes.pixel_count = pixels;
        planes.channels = channels;
        planes.channel_order = order;
        planes.output_elements = output_elements;
        planes.output_bytes = output_bytes;
        planes.work_units = work_units;
        planes.source_transform = source.transform;
        planes.dx = std::move(dx);
        planes.dy = std::move(dy);
        return {ErrorCode::none, std::move(planes)};
    } catch (const std::bad_alloc&) {
        return failure(ErrorCode::allocation_failure);
    } catch (const std::length_error&) {
        return failure(ErrorCode::resource_limit);
    } catch (...) {
        return failure(ErrorCode::allocation_failure);
    }
}

const char* error_code_name(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::none: return "NONE";
        case ErrorCode::invalid_input: return "INVALID_INPUT";
        case ErrorCode::unsupported_layout: return "UNSUPPORTED_LAYOUT";
        case ErrorCode::invalid_limits: return "INVALID_LIMITS";
        case ErrorCode::resource_limit: return "RESOURCE_LIMIT";
        case ErrorCode::cancelled: return "CANCELLED";
        case ErrorCode::deadline_exceeded: return "DEADLINE_EXCEEDED";
        case ErrorCode::allocation_failure: return "ALLOCATION_FAILURE";
    }
    return "INVALID_INPUT";
}

}  // namespace agi::image::p6
