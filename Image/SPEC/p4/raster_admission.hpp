#pragma once

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <span>
#include <stop_token>
#include <vector>

namespace agi::image::p4 {

enum class InputKind : std::uint8_t {
    decoded_raster,
    encoded_image,
    unknown,
};

enum class Layout : std::uint8_t {
    hwc,
    planar,
    unknown,
};

enum class ChannelOrder : std::uint8_t {
    gray,
    rgb,
    rgba,
    bgr,
    bgra,
    unknown,
};

enum class SampleType : std::uint8_t {
    uint8,
    uint16,
    float32,
    unknown,
};

enum class ErrorCode : std::uint8_t {
    none,
    invalid_descriptor,
    unsupported_format,
    resource_limit,
    profile_mismatch,
    cancelled,
    deadline_exceeded,
};

// All size and work ceilings are explicit call inputs. There are no production
// defaults in this API. A caller must supply limits from its separately
// authorized profile; P4 tests pass proposal-only values, which are not an
// authorization for production use.
struct AdmissionLimits final {
    std::uint64_t max_width;
    std::uint64_t max_height;
    std::uint64_t max_pixels;
    std::uint32_t max_channels;
    std::uint64_t max_decoded_bytes;
    std::uint64_t max_work_units;
};

struct RasterDescriptor final {
    std::uint64_t width;
    std::uint64_t height;
    std::uint32_t channels;
    Layout layout;
    ChannelOrder channel_order;
    SampleType sample_type;
    std::uint16_t sample_range_min;
    std::uint16_t sample_range_max;
    // Strides are in bytes. Only canonical tightly packed HWC is admitted.
    std::uint64_t row_stride_bytes;
    std::uint64_t pixel_stride_bytes;
    std::uint64_t channel_stride_bytes;
    std::uint64_t payload_bytes;
};

struct AdmissionControl final {
    std::stop_token cancellation;
    bool has_deadline;
    std::chrono::steady_clock::time_point deadline;
};

class AdmissionResult;

class RasterView final {
public:
    RasterView() noexcept = default;

    [[nodiscard]] std::uint64_t width() const noexcept { return width_; }
    [[nodiscard]] std::uint64_t height() const noexcept { return height_; }
    [[nodiscard]] std::uint64_t pixel_count() const noexcept { return pixel_count_; }
    [[nodiscard]] std::uint32_t channels() const noexcept { return channels_; }
    [[nodiscard]] ChannelOrder channel_order() const noexcept { return channel_order_; }
    [[nodiscard]] std::uint64_t work_units() const noexcept { return work_units_; }
    [[nodiscard]] std::span<const std::uint8_t> samples() const noexcept { return samples_; }

private:
    RasterView(std::span<const std::uint8_t> samples,
               std::uint64_t width,
               std::uint64_t height,
               std::uint64_t pixel_count,
               std::uint32_t channels,
               ChannelOrder channel_order,
               std::uint64_t work_units) noexcept;

    std::span<const std::uint8_t> samples_{};
    std::uint64_t width_{0};
    std::uint64_t height_{0};
    std::uint64_t pixel_count_{0};
    std::uint32_t channels_{0};
    ChannelOrder channel_order_{ChannelOrder::unknown};
    std::uint64_t work_units_{0};

    friend class AdmissionResult;
    friend AdmissionResult admit(InputKind,
                                 const RasterDescriptor&,
                                 std::span<const std::uint8_t>,
                                 const AdmissionLimits&,
                                 const AdmissionControl&) noexcept;
};

class AdmissionResult final {
public:
    [[nodiscard]] bool has_value() const noexcept { return accepted_; }
    [[nodiscard]] ErrorCode error_code() const noexcept { return error_code_; }
    [[nodiscard]] const RasterView* value() const noexcept {
        return accepted_ ? &view_ : nullptr;
    }
    [[nodiscard]] bool retryable() const noexcept { return false; }
    [[nodiscard]] bool state_changed() const noexcept { return false; }

private:
    AdmissionResult(bool accepted, ErrorCode error_code, RasterView view) noexcept;

    bool accepted_{false};
    ErrorCode error_code_{ErrorCode::invalid_descriptor};
    RasterView view_{};

    friend AdmissionResult admit(InputKind,
                                 const RasterDescriptor&,
                                 std::span<const std::uint8_t>,
                                 const AdmissionLimits&,
                                 const AdmissionControl&) noexcept;
};

enum class DecodedFormat : std::uint8_t {
    pgm_p5,
    ppm_p6,
};

enum class DecodeErrorCode : std::uint8_t {
    none,
    unsupported_format,
    malformed_header,
    corrupt_payload,
    resource_limit,
    profile_mismatch,
    cancelled,
    deadline_exceeded,
};

// Every limit is supplied by the caller. Tests use proposal-derived values only
// as explicit test bounds; there are no runtime or production defaults.
struct DecodeLimits final {
    std::uint64_t max_encoded_bytes;
    std::uint64_t max_header_bytes;
    std::uint64_t max_width;
    std::uint64_t max_height;
    std::uint64_t max_pixels;
    std::uint32_t max_channels;
    std::uint64_t max_decoded_bytes;
    std::uint64_t max_work_units;
};

struct DecodedRaster final {
    static constexpr const char* decoder_id = "agi-image-pnm-p5-p6-v1";
    DecodedFormat format{DecodedFormat::pgm_p5};
    std::uint64_t width{0};
    std::uint64_t height{0};
    std::uint32_t channels{0};
    ChannelOrder channel_order{ChannelOrder::unknown};
    std::uint64_t work_units{0};
    std::vector<std::uint8_t> samples{};
};

struct DecodeResult final {
    DecodeErrorCode error_code{DecodeErrorCode::malformed_header};
    DecodedRaster raster{};

    [[nodiscard]] bool has_value() const noexcept {
        return error_code == DecodeErrorCode::none;
    }
    [[nodiscard]] bool retryable() const noexcept { return false; }
    [[nodiscard]] bool state_changed() const noexcept { return false; }
};

// Admits only the selected profile's tightly packed decoded HWC uint8 raster
// descriptor. Encoded and unknown input kinds fail closed; this API has no
// decoder and never inspects or copies sample bytes. On success, the returned
// view borrows `samples`; the caller must keep that storage alive and immutable
// for the entire use of the view. std::span cannot enforce the lifetime rule.
// This function performs no allocation, pointer arithmetic, dereference, or
// publication side effect; all failure results contain no raster view.
[[nodiscard]] AdmissionResult admit(
    InputKind input_kind,
    const RasterDescriptor& descriptor,
    std::span<const std::uint8_t> samples,
    const AdmissionLimits& limits,
    const AdmissionControl& control = {}) noexcept;
// Decode exactly one binary Netpbm P5 (8-bit grayscale) or P6 (8-bit RGB)
// image. Header parsing is bounded and single-pass; pixels are copied once into
// owned storage. Other Netpbm variants and trailing bytes fail closed.
[[nodiscard]] DecodeResult decode_binary_pnm(
    std::span<const std::uint8_t> encoded,
    const DecodeLimits& limits,
    const AdmissionControl& control = {}) noexcept;

[[nodiscard]] const char* error_code_name(ErrorCode code) noexcept;
[[nodiscard]] const char* decode_error_code_name(DecodeErrorCode code) noexcept;

}  // namespace agi::image::p4
