#ifndef ALVS_CORE_H
#define ALVS_CORE_H

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cmath>
#include <memory>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>

namespace alvs {

/**
 * A minimal 64-byte aligned owning buffer for tensor-sized allocations.
 *
 * The alignment is sufficient for cache-line alignment and AVX-512-friendly
 * loads while remaining portable to CPU-only installations. This class owns
 * its storage and is intentionally non-copyable to make tensor lifetime and
 * ownership explicit.
 */
class AlignedTensorBuffer {
public:
    static constexpr std::size_t kAlignment = 64;

    AlignedTensorBuffer() noexcept = default;
    explicit AlignedTensorBuffer(std::size_t size_bytes);
    ~AlignedTensorBuffer() = default;

    AlignedTensorBuffer(const AlignedTensorBuffer&) = delete;
    AlignedTensorBuffer& operator=(const AlignedTensorBuffer&) = delete;
    AlignedTensorBuffer(AlignedTensorBuffer&&) noexcept = default;
    AlignedTensorBuffer& operator=(AlignedTensorBuffer&&) noexcept = default;

    void resize(std::size_t size_bytes);
    void reset() noexcept;

    [[nodiscard]] void* data() noexcept { return data_.get(); }
    [[nodiscard]] const void* data() const noexcept { return data_.get(); }
    [[nodiscard]] std::size_t size_bytes() const noexcept { return size_bytes_; }
    [[nodiscard]] bool empty() const noexcept { return data_ == nullptr; }
    [[nodiscard]] bool is_aligned() const noexcept;

private:
    struct AlignedFree {
        void operator()(void* pointer) const noexcept;
    };

    std::unique_ptr<void, AlignedFree> data_{nullptr};
    std::size_t size_bytes_{0};
};

// High-performance pixel structure.
static_assert(sizeof(float) == 4, "ALVS requires 32-bit IEEE-compatible float storage");
struct Pixel {
    float r, g, b;

    Pixel() : r(0), g(0), b(0) {}
    Pixel(float red, float green, float blue) : r(red), g(green), b(blue) {}
};
static_assert(sizeof(Pixel) == sizeof(float) * 3, "Pixel must remain tightly packed");

// Atomic context holding all computed layers.
struct AtomicContext {
    std::vector<Pixel> color;
    std::vector<float> energy;
    std::vector<float> flow_x;
    std::vector<float> flow_y;
    std::size_t width{0};
    std::size_t height{0};
};

class VisionLoader {
public:
    VisionLoader() = default;

    std::vector<Pixel> loadToMath(const std::string& file_path);
    void saveFromMath(const std::vector<Pixel>& matrix, std::size_t width, std::size_t height,
                      const std::string& output_path);

private:
    std::vector<unsigned char> loadImageFile(const std::string& file_path,
                                              std::size_t& width, std::size_t& height, int& channels);
    void saveImageFile(const std::vector<unsigned char>& data, std::size_t width, std::size_t height,
                       const std::string& output_path);
};

class Atomizer {
public:
    Atomizer() = default;

    // Legacy owning interface retained for existing callers.
    AtomicContext atomize(const std::vector<Pixel>& color_matrix, std::size_t width, std::size_t height);

    /**
     * Direct, non-owning interleaved-RGB interface.
     *
     * The caller owns both the HxWx3 float32 input and HxW output buffers.
     * No image-sized input buffer is allocated or copied by this method.
     */
    void atomizeInterleaved(const float* color_interleaved,
                            std::size_t width,
                            std::size_t height,
                            float* energy_out,
                            float* flow_x_out,
                            float* flow_y_out) const;

    // Computes Rec. 709 energy values from tightly packed RGB float32 pixels.
    void computeEnergyInterleaved(const float* color_interleaved,
                                  float* energy_out,
                                  std::size_t pixel_count) const;

    // Runtime-selected SIMD implementation status for diagnostic and test use.
    [[nodiscard]] bool simdAvailable() const noexcept;
    [[nodiscard]] const char* simdBackend() const noexcept;

    std::vector<float> getSmartAtom(const AtomicContext& ctx, std::size_t x, std::size_t y);

private:
    static constexpr float LUMA_R = 0.2126f;
    static constexpr float LUMA_G = 0.7152f;
    static constexpr float LUMA_B = 0.0722f;

    void computeFlowInterleaved(const float* color_interleaved,
                                std::size_t width,
                                std::size_t height,
                                float* flow_x_out,
                                float* flow_y_out) const;
};

class Synthesizer {
public:
    Synthesizer() = default;

    std::vector<Pixel> reconstruct(const AtomicContext& ctx);
    std::vector<Pixel> smartRemix(const AtomicContext& ctx, const std::string& mode);

private:
    std::vector<Pixel> visualizeFlow(const AtomicContext& ctx);
    std::vector<Pixel> quantumInverse(const AtomicContext& ctx);
    std::vector<Pixel> energyBoost(const AtomicContext& ctx);
};

} // namespace alvs

#endif // ALVS_CORE_H
