#include "raster_admission.hpp"

#include <cstring>
#include <limits>
#include <new>
#include <stdexcept>
#include <utility>

namespace agi::image::p4 {
namespace {

[[nodiscard]] bool checked_multiply(std::uint64_t left,
                                    std::uint64_t right,
                                    std::uint64_t& result) noexcept {
    if (left != 0 && right > std::numeric_limits<std::uint64_t>::max() / left) {
        return false;
    }
    result = left * right;
    return true;
}

[[nodiscard]] bool checked_add(std::uint64_t left,
                               std::uint64_t right,
                               std::uint64_t& result) noexcept {
    if (right > std::numeric_limits<std::uint64_t>::max() - left) {
        return false;
    }
    result = left + right;
    return true;
}

[[nodiscard]] bool deadline_expired(const AdmissionControl& control) noexcept {
    return control.has_deadline &&
           std::chrono::steady_clock::now() >= control.deadline;
}

[[nodiscard]] std::uint32_t expected_channels(ChannelOrder order) noexcept {
    switch (order) {
        case ChannelOrder::gray: return 1;
        case ChannelOrder::rgb: return 3;
        case ChannelOrder::rgba: return 4;
        case ChannelOrder::bgr:
        case ChannelOrder::bgra:
        case ChannelOrder::unknown: return 0;
    }
    return 0;
}

[[nodiscard]] bool ascii_space(std::uint8_t byte) noexcept {
    return byte == static_cast<std::uint8_t>(' ') ||
           byte == static_cast<std::uint8_t>('\t') ||
           byte == static_cast<std::uint8_t>('\n') ||
           byte == static_cast<std::uint8_t>('\r') ||
           byte == static_cast<std::uint8_t>('\v') ||
           byte == static_cast<std::uint8_t>('\f');
}

struct Token final {
    std::size_t begin;
    std::size_t length;
};

class PnmHeader final {
public:
    PnmHeader(std::span<const std::uint8_t> bytes,
              std::uint64_t max_header_bytes,
              std::size_t position) noexcept
        : bytes_(bytes), max_header_bytes_(max_header_bytes), position_(position) {}

    [[nodiscard]] bool next_token(Token& token) noexcept {
        if (!skip_separators()) return false;
        const std::size_t begin = position_;
        while (position_ < bytes_.size()) {
            if (at_header_limit()) return false;
            const std::uint8_t byte = bytes_[position_];
            if (ascii_space(byte) || byte == static_cast<std::uint8_t>('#')) break;
            ++position_;
        }
        token = {begin, position_ - begin};
        return token.length != 0;
    }

    [[nodiscard]] bool final_separator(std::size_t& raster_offset) noexcept {
        if (position_ >= bytes_.size() || at_header_limit()) return false;
        const std::uint8_t separator = bytes_[position_];
        if (!ascii_space(separator)) return false;
        ++position_;
        if (separator == static_cast<std::uint8_t>('\r') &&
            position_ < bytes_.size() &&
            bytes_[position_] == static_cast<std::uint8_t>('\n')) {
            if (at_header_limit()) return false;
            ++position_;
        }
        raster_offset = position_;
        return true;
    }

    [[nodiscard]] DecodeErrorCode error() const noexcept { return error_; }

private:
    [[nodiscard]] bool at_header_limit() noexcept {
        if (std::cmp_greater_equal(position_, max_header_bytes_)) {
            error_ = DecodeErrorCode::resource_limit;
            return true;
        }
        return false;
    }

    [[nodiscard]] bool skip_separators() noexcept {
        while (position_ < bytes_.size()) {
            if (at_header_limit()) return false;
            const std::uint8_t byte = bytes_[position_];
            if (ascii_space(byte)) {
                ++position_;
                continue;
            }
            if (byte != static_cast<std::uint8_t>('#')) return true;
            ++position_;
            while (position_ < bytes_.size()) {
                if (at_header_limit()) return false;
                const std::uint8_t comment_byte = bytes_[position_];
                if (comment_byte == static_cast<std::uint8_t>('\n') ||
                    comment_byte == static_cast<std::uint8_t>('\r')) break;
                ++position_;
            }
            if (position_ < bytes_.size()) {
                const std::uint8_t newline = bytes_[position_];
                if (at_header_limit()) return false;
                ++position_;
                if (newline == static_cast<std::uint8_t>('\r') &&
                    position_ < bytes_.size() &&
                    bytes_[position_] == static_cast<std::uint8_t>('\n')) {
                    if (at_header_limit()) return false;
                    ++position_;
                }
            }
        }
        return false;
    }

    std::span<const std::uint8_t> bytes_;
    std::uint64_t max_header_bytes_;
    std::size_t position_;
    DecodeErrorCode error_{DecodeErrorCode::malformed_header};
};

[[nodiscard]] bool parse_decimal(std::span<const std::uint8_t> bytes,
                                 Token token,
                                 std::uint64_t& value) noexcept {
    if (token.length == 0) return false;
    value = 0;
    for (std::size_t index = 0; index < token.length; ++index) {
        const std::uint8_t byte = bytes[token.begin + index];
        if (byte < static_cast<std::uint8_t>('0') || byte > static_cast<std::uint8_t>('9')) {
            return false;
        }
        const std::uint64_t digit = static_cast<std::uint64_t>(byte - static_cast<std::uint8_t>('0'));
        if (value > (std::numeric_limits<std::uint64_t>::max() - digit) / 10) return false;
        value = value * 10 + digit;
    }
    return true;
}

[[nodiscard]] DecodeResult decode_failure(DecodeErrorCode code) noexcept {
    return {code, DecodedRaster{}};
}

[[nodiscard]] bool decode_cancelled(const AdmissionControl& control) noexcept {
    return control.cancellation.stop_requested();
}

[[nodiscard]] bool decode_deadline_expired(const AdmissionControl& control) noexcept {
    return control.has_deadline &&
           std::chrono::steady_clock::now() >= control.deadline;
}

}  // namespace

RasterView::RasterView(std::span<const std::uint8_t> samples,
                       std::uint64_t width,
                       std::uint64_t height,
                       std::uint64_t pixel_count,
                       std::uint32_t channels,
                       ChannelOrder channel_order,
                       std::uint64_t work_units) noexcept
    : samples_(samples),
      width_(width),
      height_(height),
      pixel_count_(pixel_count),
      channels_(channels),
      channel_order_(channel_order),
      work_units_(work_units) {}

AdmissionResult::AdmissionResult(bool accepted,
                                 ErrorCode error_code,
                                 RasterView view) noexcept
    : accepted_(accepted), error_code_(error_code), view_(view) {}

AdmissionResult admit(InputKind input_kind,
                      const RasterDescriptor& descriptor,
                      std::span<const std::uint8_t> samples,
                      const AdmissionLimits& limits,
                      const AdmissionControl& control) noexcept {
    const auto reject = [](ErrorCode code) noexcept {
        return AdmissionResult(false, code, RasterView{});
    };
    if (control.cancellation.stop_requested()) {
        return reject(ErrorCode::cancelled);
    }
    if (deadline_expired(control)) {
        return reject(ErrorCode::deadline_exceeded);
    }
    // Encoded inputs use decode_binary_pnm; admission itself never interprets bytes.
    if (input_kind != InputKind::decoded_raster) {
        return reject(ErrorCode::unsupported_format);
    }
    if (limits.max_width == 0 || limits.max_height == 0 || limits.max_channels == 0) {
        return reject(ErrorCode::profile_mismatch);
    }
    if (descriptor.layout != Layout::hwc) {
        return reject(ErrorCode::unsupported_format);
    }
    if (descriptor.sample_type != SampleType::uint8) {
        return reject(ErrorCode::unsupported_format);
    }
    const std::uint32_t channel_count = expected_channels(descriptor.channel_order);
    if (channel_count == 0) {
        return reject(ErrorCode::unsupported_format);
    }
    if (descriptor.width == 0 || descriptor.height == 0 || descriptor.channels == 0) {
        return reject(ErrorCode::invalid_descriptor);
    }
    if (descriptor.channels != channel_count) {
        return reject(ErrorCode::invalid_descriptor);
    }
    if (descriptor.sample_range_min > descriptor.sample_range_max) {
        return reject(ErrorCode::invalid_descriptor);
    }
    if (descriptor.sample_range_min != 0 || descriptor.sample_range_max != 255) {
        return reject(ErrorCode::profile_mismatch);
    }
    if (descriptor.width > limits.max_width || descriptor.height > limits.max_height ||
        descriptor.channels > limits.max_channels) {
        return reject(ErrorCode::resource_limit);
    }

    std::uint64_t pixel_count = 0;
    if (!checked_multiply(descriptor.width, descriptor.height, pixel_count)) {
        return reject(ErrorCode::resource_limit);
    }
    if (pixel_count > limits.max_pixels) {
        return reject(ErrorCode::resource_limit);
    }
    std::uint64_t sample_count = 0;
    if (!checked_multiply(pixel_count, descriptor.channels, sample_count)) {
        return reject(ErrorCode::resource_limit);
    }
    const std::uint64_t decoded_bytes = sample_count;
    const std::uint64_t work_units = sample_count;
    if (decoded_bytes > limits.max_decoded_bytes || work_units > limits.max_work_units) {
        return reject(ErrorCode::resource_limit);
    }
    if (std::cmp_greater(decoded_bytes, std::numeric_limits<std::size_t>::max()) ||
        std::cmp_greater(decoded_bytes, std::numeric_limits<std::ptrdiff_t>::max())) {
        return reject(ErrorCode::resource_limit);
    }
    if (std::cmp_greater(samples.size(), limits.max_decoded_bytes)) {
        return reject(ErrorCode::resource_limit);
    }

    std::uint64_t row_last = 0;
    std::uint64_t pixel_last = 0;
    std::uint64_t channel_last = 0;
    std::uint64_t last_offset = 0;
    std::uint64_t partial_offset = 0;
    std::uint64_t addressed_bytes = 0;
    if (!checked_multiply(descriptor.height - 1, descriptor.row_stride_bytes, row_last) ||
        !checked_multiply(descriptor.width - 1, descriptor.pixel_stride_bytes, pixel_last) ||
        !checked_multiply(static_cast<std::uint64_t>(descriptor.channels - 1),
                          descriptor.channel_stride_bytes, channel_last) ||
        !checked_add(row_last, pixel_last, partial_offset) ||
        !checked_add(partial_offset, channel_last, last_offset) ||
        !checked_add(last_offset, 1, addressed_bytes)) {
        return reject(ErrorCode::resource_limit);
    }
    if (addressed_bytes > limits.max_decoded_bytes) {
        return reject(ErrorCode::resource_limit);
    }
    std::uint64_t expected_row_stride = 0;
    if (!checked_multiply(descriptor.width, descriptor.channels, expected_row_stride)) {
        return reject(ErrorCode::resource_limit);
    }
    if (descriptor.channel_stride_bytes != 1 ||
        descriptor.pixel_stride_bytes != descriptor.channels ||
        descriptor.row_stride_bytes != expected_row_stride || addressed_bytes != decoded_bytes) {
        return reject(ErrorCode::invalid_descriptor);
    }
    if (descriptor.payload_bytes != decoded_bytes ||
        !std::cmp_equal(samples.size(), decoded_bytes) || samples.data() == nullptr) {
        return reject(ErrorCode::invalid_descriptor);
    }
    if (control.cancellation.stop_requested()) {
        return reject(ErrorCode::cancelled);
    }
    if (deadline_expired(control)) {
        return reject(ErrorCode::deadline_exceeded);
    }
    const RasterView view(samples, descriptor.width, descriptor.height, pixel_count,
                          descriptor.channels, descriptor.channel_order, work_units);
    return AdmissionResult(true, ErrorCode::none, view);
}

DecodeResult decode_binary_pnm(std::span<const std::uint8_t> encoded,
                               const DecodeLimits& limits,
                               const AdmissionControl& control) noexcept {
    if (decode_cancelled(control)) return decode_failure(DecodeErrorCode::cancelled);
    if (decode_deadline_expired(control)) return decode_failure(DecodeErrorCode::deadline_exceeded);
    if (limits.max_encoded_bytes == 0 || limits.max_header_bytes == 0 ||
        limits.max_header_bytes > limits.max_encoded_bytes || limits.max_width == 0 ||
        limits.max_height == 0 || limits.max_pixels == 0 || limits.max_channels == 0 ||
        limits.max_decoded_bytes == 0 || limits.max_work_units == 0) {
        return decode_failure(DecodeErrorCode::profile_mismatch);
    }
    if (std::cmp_greater(encoded.size(), limits.max_encoded_bytes)) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }
    if (std::cmp_greater(encoded.size(), std::numeric_limits<std::ptrdiff_t>::max())) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }
    if (encoded.size() < 3) return decode_failure(DecodeErrorCode::corrupt_payload);
    if (encoded[0] != static_cast<std::uint8_t>('P')) {
        return decode_failure(DecodeErrorCode::unsupported_format);
    }

    DecodedFormat format{};
    std::uint32_t channels = 0;
    ChannelOrder order = ChannelOrder::unknown;
    if (encoded[1] == static_cast<std::uint8_t>('5')) {
        format = DecodedFormat::pgm_p5;
        channels = 1;
        order = ChannelOrder::gray;
    } else if (encoded[1] == static_cast<std::uint8_t>('6')) {
        format = DecodedFormat::ppm_p6;
        channels = 3;
        order = ChannelOrder::rgb;
    } else {
        return decode_failure(DecodeErrorCode::unsupported_format);
    }
    if (!ascii_space(encoded[2])) return decode_failure(DecodeErrorCode::malformed_header);

    PnmHeader header(encoded, limits.max_header_bytes, 2);
    Token width_token{};
    Token height_token{};
    Token maxval_token{};
    std::uint64_t width = 0;
    std::uint64_t height = 0;
    std::uint64_t maxval = 0;
    if (!header.next_token(width_token) || !parse_decimal(encoded, width_token, width) ||
        !header.next_token(height_token) || !parse_decimal(encoded, height_token, height) ||
        !header.next_token(maxval_token) || !parse_decimal(encoded, maxval_token, maxval)) {
        return decode_failure(header.error());
    }
    if (width == 0 || height == 0 || maxval == 0) {
        return decode_failure(DecodeErrorCode::malformed_header);
    }
    if (maxval != 255) return decode_failure(DecodeErrorCode::unsupported_format);
    if (channels > limits.max_channels || width > limits.max_width || height > limits.max_height) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }

    std::size_t raster_offset = 0;
    if (!header.final_separator(raster_offset)) return decode_failure(header.error());
    if (std::cmp_greater(raster_offset, limits.max_header_bytes)) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }
    std::uint64_t pixels = 0;
    std::uint64_t decoded_bytes = 0;
    if (!checked_multiply(width, height, pixels) || pixels > limits.max_pixels ||
        !checked_multiply(pixels, channels, decoded_bytes)) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }
    if (decoded_bytes > limits.max_decoded_bytes ||
        std::cmp_greater(decoded_bytes, std::numeric_limits<std::size_t>::max()) ||
        std::cmp_greater(decoded_bytes, std::numeric_limits<std::ptrdiff_t>::max())) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }
    if (std::cmp_greater(encoded.size(), std::numeric_limits<std::uint64_t>::max())) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }
    const std::uint64_t encoded_bytes = static_cast<std::uint64_t>(encoded.size());
    std::uint64_t work_units = 0;
    if (!checked_add(encoded_bytes, decoded_bytes, work_units) ||
        work_units > limits.max_work_units) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }

    std::uint64_t expected_encoded_bytes = 0;
    if (std::cmp_greater(raster_offset, std::numeric_limits<std::uint64_t>::max()) ||
        !checked_add(static_cast<std::uint64_t>(raster_offset), decoded_bytes,
                     expected_encoded_bytes) ||
        !std::cmp_equal(expected_encoded_bytes, encoded.size())) {
        return decode_failure(DecodeErrorCode::corrupt_payload);
    }
    if (decode_cancelled(control)) return decode_failure(DecodeErrorCode::cancelled);
    if (decode_deadline_expired(control)) return decode_failure(DecodeErrorCode::deadline_exceeded);

    std::vector<std::uint8_t> samples;
    try {
        if (decoded_bytes > samples.max_size()) return decode_failure(DecodeErrorCode::resource_limit);
        samples.resize(static_cast<std::size_t>(decoded_bytes));
    } catch (const std::bad_alloc&) {
        return decode_failure(DecodeErrorCode::resource_limit);
    } catch (const std::length_error&) {
        return decode_failure(DecodeErrorCode::resource_limit);
    }
    constexpr std::size_t kCopyChunkBytes = 65536;
    const auto source = encoded.subspan(raster_offset, samples.size());
    for (std::size_t offset = 0; offset < samples.size();) {
        if (decode_cancelled(control)) return decode_failure(DecodeErrorCode::cancelled);
        if (decode_deadline_expired(control)) return decode_failure(DecodeErrorCode::deadline_exceeded);
        const std::size_t remaining = samples.size() - offset;
        const std::size_t count = remaining < kCopyChunkBytes ? remaining : kCopyChunkBytes;
        std::memcpy(samples.data() + offset, source.data() + offset, count);
        offset += count;
    }
    if (decode_cancelled(control)) return decode_failure(DecodeErrorCode::cancelled);
    if (decode_deadline_expired(control)) return decode_failure(DecodeErrorCode::deadline_exceeded);

    DecodedRaster raster{format, width, height, channels, order, work_units,
                         std::move(samples)};
    return {DecodeErrorCode::none, std::move(raster)};
}

const char* error_code_name(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::none: return "NONE";
        case ErrorCode::invalid_descriptor: return "INVALID_DESCRIPTOR";
        case ErrorCode::unsupported_format: return "UNSUPPORTED_FORMAT";
        case ErrorCode::resource_limit: return "RESOURCE_LIMIT";
        case ErrorCode::profile_mismatch: return "PROFILE_MISMATCH";
        case ErrorCode::cancelled: return "CANCELLED";
        case ErrorCode::deadline_exceeded: return "DEADLINE_EXCEEDED";
    }
    return "INTERNAL_ERROR";
}

const char* decode_error_code_name(DecodeErrorCode code) noexcept {
    switch (code) {
        case DecodeErrorCode::none: return "NONE";
        case DecodeErrorCode::unsupported_format: return "UNSUPPORTED_FORMAT";
        case DecodeErrorCode::malformed_header: return "MALFORMED_HEADER";
        case DecodeErrorCode::corrupt_payload: return "CORRUPT_PAYLOAD";
        case DecodeErrorCode::resource_limit: return "RESOURCE_LIMIT";
        case DecodeErrorCode::profile_mismatch: return "PROFILE_MISMATCH";
        case DecodeErrorCode::cancelled: return "CANCELLED";
        case DecodeErrorCode::deadline_exceeded: return "DEADLINE_EXCEEDED";
    }
    return "INTERNAL_ERROR";
}

}  // namespace agi::image::p4
