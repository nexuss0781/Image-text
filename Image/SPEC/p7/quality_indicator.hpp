#pragma once

#include "../p4/raster_admission.hpp"
#include "../p5/canonical_raster.hpp"

#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace agi::image::p7 {

enum class ErrorCode : std::uint8_t {
    none,
    invalid_descriptor,
    unsupported_format,
    profile_mismatch,
    resource_limit,
    nonfinite_input,
    uncertainty_unavailable,
    cancelled,
    deadline_exceeded,
    internal_error,
};

// All limits are explicit call inputs. No proposal or production defaults are
// available from this API. The scalar output payload is exactly 24 wire-value
// bytes: two uint64 counts and one IEEE-754 binary64 fraction (metadata excluded).
struct Limits final {
    std::uint64_t max_pixels;
    std::uint32_t max_channels;
    std::uint64_t max_output_bytes;
    std::uint64_t max_work_units;
};

struct Options final {
    // The candidate profile binds uncertainty mode to disabled. true fails closed;
    // it never selects or fabricates an uncertainty estimator.
    bool require_uncertainty{false};
};

struct QualityIndicator final {
    static constexpr std::string_view name{"endpoint_code_fraction"};
    static constexpr std::string_view method_id{"uint8-endpoint-code-fraction"};
    static constexpr std::string_view method_version{"1"};
    static constexpr std::string_view units{"fraction"};
    static constexpr std::string_view scope{"image"};
    static constexpr std::string_view acceptance_effect{"descriptive_only"};

    std::uint64_t numerator{0};
    std::uint64_t denominator{0};
    double value{0.0};
    std::uint64_t work_units{0};
    std::uint64_t output_payload_bytes{0};
};

// This type makes disabled uncertainty omission explicit. Phase 7 never fills it.
struct UncertaintyOutput final {
    std::vector<float> values{};
};

struct Result final {
    ErrorCode error_code{ErrorCode::invalid_descriptor};
    std::optional<QualityIndicator> quality{};
    std::optional<UncertaintyOutput> uncertainty{};

    [[nodiscard]] bool has_value() const noexcept {
        return error_code == ErrorCode::none && quality.has_value();
    }
    [[nodiscard]] bool retryable() const noexcept { return false; }
    [[nodiscard]] bool state_changed() const noexcept { return false; }
};

[[nodiscard]] Result measure_endpoint_code_fraction_v1(
    const agi::image::p5::CanonicalRasterView& source,
    const Limits& limits,
    const Options& options,
    const agi::image::p4::AdmissionControl& control = {}) noexcept;

[[nodiscard]] const char* error_code_name(ErrorCode code) noexcept;
// Fixed allowlisted messages. They are stable for this draft contract and never
// include caller-controlled payload bytes, text, paths, or identifiers.
[[nodiscard]] const char* error_message(ErrorCode code) noexcept;

#ifdef AGI_IMAGE_P7_TESTING
namespace testing {
enum class FaultPoint : std::uint8_t { none, after_first_sample, before_publish };
}
[[nodiscard]] Result measure_endpoint_code_fraction_v1_with_test_fault(
    const agi::image::p5::CanonicalRasterView& source,
    const Limits& limits,
    const Options& options,
    const agi::image::p4::AdmissionControl& control,
    testing::FaultPoint fault) noexcept;
#endif

}  // namespace agi::image::p7
