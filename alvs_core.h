#ifndef ALVS_CORE_H
#define ALVS_CORE_H

#include <algorithm>
#include <array>
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

/** One orthonormal Haar analysis level; all sub-bands have output_width x output_height samples. */
struct WaveletLevel {
    std::size_t input_width{0};
    std::size_t input_height{0};
    std::size_t output_width{0};
    std::size_t output_height{0};
    std::vector<float> approximation;
    std::vector<float> detail_horizontal;
    std::vector<float> detail_vertical;
    std::vector<float> detail_diagonal;
};

/** Multi-scale, edge-replicated Haar pyramid that preserves the original tensor geometry. */
struct HaarWaveletPyramid {
    std::size_t original_width{0};
    std::size_t original_height{0};
    std::vector<WaveletLevel> levels;

    [[nodiscard]] bool empty() const noexcept { return levels.empty(); }
};

struct SemanticGateFeatures {
    // Bias, normalized energy variance, normalized flow variance, normalized detail energy.
    std::array<float, 4> values{1.0f, 0.0f, 0.0f, 0.0f};
};

struct ExecutionReport {
    std::string backend{"cpu-reference"};
    std::size_t worker_threads{1};
    bool simd_enabled{false};
    bool parallel_enabled{false};
    bool gpu_available{false};
};

struct SemanticGateOutput {
    // RGB, Energy, Flow-X, Flow-Y, Wavelet details, Wavelet approximation.
    std::array<float, 6> weights{1.0f / 6.0f, 1.0f / 6.0f, 1.0f / 6.0f,
                                 1.0f / 6.0f, 1.0f / 6.0f, 1.0f / 6.0f};
    float complexity{0.0f};
    float entropy{0.0f};
};

struct ProjectionConfig {
    std::size_t patch_size{4};
    std::size_t embedding_dimension{4096};
    float retention_ratio{0.25f};
    std::size_t max_tokens{0}; // Zero retains the adaptive-ratio budget.
};

struct VisualTokenProjection {
    std::size_t embedding_dimension{0};
    std::size_t source_patch_count{0};
    std::size_t retained_token_count{0};
    std::vector<std::size_t> patch_y;
    std::vector<std::size_t> patch_x;
    std::vector<float> importance;
    std::vector<float> embeddings; // Token-major [retained_token_count, embedding_dimension].
};

/**
 * Deterministic Stage 4 visual-token projector. It converts Stage 1/2 atomic
 * layers into RMS-normalized LLM-shaped embeddings without asserting semantic
 * alignment to a pretrained language model.
 */
class VisualTokenProjector {
public:
    [[nodiscard]] VisualTokenProjection project(const float* energy,
                                                const float* flow_x,
                                                const float* flow_y,
                                                std::size_t width,
                                                std::size_t height,
                                                const HaarWaveletPyramid& wavelet,
                                                const SemanticGateOutput& gate,
                                                const ProjectionConfig& config = {}) const;
};

/**
 * A compact, trainable softmax gate. It consumes deterministic visual-statistic
 * features and distributes attention over atomic visual representations.
 */
class SemanticAttentionGate {
public:
    static constexpr std::size_t kFeatureCount = 4;
    static constexpr std::size_t kOutputCount = 6;

    SemanticAttentionGate();

    [[nodiscard]] SemanticGateOutput infer(const SemanticGateFeatures& features) const;
    float trainStep(const SemanticGateFeatures& features,
                    const std::array<float, kOutputCount>& target,
                    float learning_rate,
                    float* gradient_l2_norm = nullptr);
    void reset() noexcept;

private:
    std::array<std::array<float, kFeatureCount>, kOutputCount> weights_{};
    std::array<float, kOutputCount> biases_{};
};

// Atomic context holding all computed layers.
struct AtomicContext {
    std::vector<Pixel> color;
    std::vector<float> energy;
    std::vector<float> flow_x;
    std::vector<float> flow_y;
    HaarWaveletPyramid wavelet;
    SemanticGateFeatures gate_features;
    SemanticGateOutput semantic_gate;
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
     * Stage 2 semantic atomization: extends the base context with an
     * orthonormal multi-scale Haar pyramid and deterministic gate output.
     */
    AtomicContext atomizeMultiScale(const std::vector<Pixel>& color_matrix,
                                    std::size_t width,
                                    std::size_t height,
                                    std::size_t max_levels = 2) const;

    /**
     * Direct Stage 2 interface. The RGB input remains caller-owned; only
     * output layers and the explicitly requested wavelet pyramid are created.
     */
    void atomizeMultiScaleInterleaved(const float* color_interleaved,
                                      std::size_t width,
                                      std::size_t height,
                                      float* energy_out,
                                      float* flow_x_out,
                                      float* flow_y_out,
                                      HaarWaveletPyramid& wavelet_out,
                                      SemanticGateFeatures& gate_features_out,
                                      SemanticGateOutput& semantic_gate_out,
                                      std::size_t max_levels = 2) const;

    HaarWaveletPyramid decomposeEnergyPyramid(const float* energy,
                                              std::size_t width,
                                              std::size_t height,
                                              std::size_t max_levels = 2) const;
    std::vector<float> reconstructEnergyPyramid(const HaarWaveletPyramid& pyramid) const;
    SemanticGateFeatures extractGateFeatures(const AtomicContext& context) const;

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

    /**
     * Stage 3 parallel CPU dispatch. It preserves the reference numerical
     * contract and reports the selected backend; GPU availability is reported
     * explicitly rather than silently simulated.
     */
    void atomizeAcceleratedInterleaved(const float* color_interleaved,
                                      std::size_t width,
                                      std::size_t height,
                                      float* energy_out,
                                      float* flow_x_out,
                                      float* flow_y_out,
                                      ExecutionReport& report) const;

    [[nodiscard]] bool parallelAvailable() const noexcept;
    [[nodiscard]] std::size_t availableWorkerThreads() const noexcept;

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
    void computeFlowInterleavedParallel(const float* color_interleaved,
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
