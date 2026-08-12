#include "alvs_core.h"

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#if defined(__AVX512F__) || defined(__AVX2__)
#include <immintrin.h>
#endif

#ifdef ALVS_HAS_OPENMP
#include <omp.h>
#endif

#include <cstring>
#include <limits>
#include <numeric>

namespace {

bool checkedPixelCount(std::size_t width, std::size_t height, std::size_t& pixel_count) {
    if (width == 0 || height == 0) {
        pixel_count = 0;
        return true;
    }
    if (width > std::numeric_limits<std::size_t>::max() / height) {
        return false;
    }
    pixel_count = width * height;
    return true;
}

void computeEnergyScalar(const float* color_interleaved, float* energy_out, std::size_t pixel_count) {
    constexpr float kLumaR = 0.2126f;
    constexpr float kLumaG = 0.7152f;
    constexpr float kLumaB = 0.0722f;

    for (std::size_t i = 0; i < pixel_count; ++i) {
        const std::size_t rgb = i * 3;
        energy_out[i] = color_interleaved[rgb] * kLumaR +
                        color_interleaved[rgb + 1] * kLumaG +
                        color_interleaved[rgb + 2] * kLumaB;
    }
}

#if defined(__AVX512F__)
void computeEnergyAvx512(const float* color_interleaved, float* energy_out, std::size_t pixel_count) {
    constexpr std::size_t kWidth = 16;
    const __m512 r_weight = _mm512_set1_ps(0.2126f);
    const __m512 g_weight = _mm512_set1_ps(0.7152f);
    const __m512 b_weight = _mm512_set1_ps(0.0722f);
    const __m512i offsets = _mm512_setr_epi32(0, 3, 6, 9, 12, 15, 18, 21,
                                               24, 27, 30, 33, 36, 39, 42, 45);

    std::size_t i = 0;
    for (; i + kWidth <= pixel_count; i += kWidth) {
        const float* base = color_interleaved + i * 3;
        const __m512 r = _mm512_i32gather_ps(offsets, base, sizeof(float));
        const __m512 g = _mm512_i32gather_ps(_mm512_add_epi32(offsets, _mm512_set1_epi32(1)), base, sizeof(float));
        const __m512 b = _mm512_i32gather_ps(_mm512_add_epi32(offsets, _mm512_set1_epi32(2)), base, sizeof(float));
        const __m512 energy = _mm512_add_ps(
            _mm512_add_ps(_mm512_mul_ps(r, r_weight), _mm512_mul_ps(g, g_weight)),
            _mm512_mul_ps(b, b_weight));
        _mm512_storeu_ps(energy_out + i, energy);
    }
    computeEnergyScalar(color_interleaved + i * 3, energy_out + i, pixel_count - i);
}
#elif defined(__AVX2__)
void computeEnergyAvx2(const float* color_interleaved, float* energy_out, std::size_t pixel_count) {
    constexpr std::size_t kWidth = 8;
    const __m256 r_weight = _mm256_set1_ps(0.2126f);
    const __m256 g_weight = _mm256_set1_ps(0.7152f);
    const __m256 b_weight = _mm256_set1_ps(0.0722f);
    const __m256i offsets = _mm256_setr_epi32(0, 3, 6, 9, 12, 15, 18, 21);

    std::size_t i = 0;
    for (; i + kWidth <= pixel_count; i += kWidth) {
        const float* base = color_interleaved + i * 3;
        const __m256 r = _mm256_i32gather_ps(base, offsets, sizeof(float));
        const __m256 g = _mm256_i32gather_ps(base, _mm256_add_epi32(offsets, _mm256_set1_epi32(1)), sizeof(float));
        const __m256 b = _mm256_i32gather_ps(base, _mm256_add_epi32(offsets, _mm256_set1_epi32(2)), sizeof(float));
        const __m256 energy = _mm256_add_ps(
            _mm256_add_ps(_mm256_mul_ps(r, r_weight), _mm256_mul_ps(g, g_weight)),
            _mm256_mul_ps(b, b_weight));
        _mm256_storeu_ps(energy_out + i, energy);
    }
    computeEnergyScalar(color_interleaved + i * 3, energy_out + i, pixel_count - i);
}
#endif

} // namespace

namespace alvs {

void AlignedTensorBuffer::AlignedFree::operator()(void* pointer) const noexcept {
    if (pointer != nullptr) {
        ::operator delete(pointer, std::align_val_t(AlignedTensorBuffer::kAlignment));
    }
}

AlignedTensorBuffer::AlignedTensorBuffer(std::size_t size_bytes) {
    resize(size_bytes);
}

void AlignedTensorBuffer::resize(std::size_t size_bytes) {
    reset();
    if (size_bytes == 0) {
        return;
    }
    void* allocation = ::operator new(size_bytes, std::align_val_t(kAlignment));
    data_.reset(allocation);
    size_bytes_ = size_bytes;
}

void AlignedTensorBuffer::reset() noexcept {
    data_.reset();
    size_bytes_ = 0;
}

bool AlignedTensorBuffer::is_aligned() const noexcept {
    return data_ == nullptr || (reinterpret_cast<std::uintptr_t>(data_.get()) % kAlignment) == 0;
}

VisualTokenProjection VisualTokenProjector::project(const float* energy,
                                                     const float* flow_x,
                                                     const float* flow_y,
                                                     std::size_t width,
                                                     std::size_t height,
                                                     const HaarWaveletPyramid& wavelet,
                                                     const SemanticGateOutput& gate,
                                                     const ProjectionConfig& config) const {
    std::size_t pixel_count = 0;
    if (!checkedPixelCount(width, height, pixel_count)) {
        throw std::overflow_error("Projection dimensions exceed supported tensor size");
    }
    if (pixel_count == 0) {
        return {};
    }
    if (energy == nullptr || flow_x == nullptr || flow_y == nullptr) {
        throw std::invalid_argument("Projection requires non-null atomic layer buffers");
    }
    if (config.patch_size == 0 || config.embedding_dimension == 0 ||
        !std::isfinite(config.retention_ratio) || config.retention_ratio <= 0.0f ||
        config.retention_ratio > 1.0f) {
        throw std::invalid_argument("Projection configuration has an invalid patch size, dimension, or retention ratio");
    }
    const float gate_total = std::accumulate(gate.weights.begin(), gate.weights.end(), 0.0f);
    if (!std::isfinite(gate_total) || std::abs(gate_total - 1.0f) > 1.0e-4f) {
        throw std::invalid_argument("Projection requires normalized semantic gate weights");
    }

    struct Candidate {
        std::size_t patch_y;
        std::size_t patch_x;
        float importance;
        std::array<float, 6> features;
    };

    const std::size_t patch_rows = (height + config.patch_size - 1) / config.patch_size;
    const std::size_t patch_columns = (width + config.patch_size - 1) / config.patch_size;
    std::vector<Candidate> candidates;
    candidates.reserve(patch_rows * patch_columns);

    const WaveletLevel* finest = wavelet.levels.empty() ? nullptr : &wavelet.levels.front();
    auto sampleBand = [finest](const std::vector<float>& band, std::size_t x, std::size_t y) {
        if (finest == nullptr || band.empty() || finest->output_width == 0 || finest->output_height == 0) {
            return 0.0f;
        }
        const std::size_t wave_x = std::min(x / 2, finest->output_width - 1);
        const std::size_t wave_y = std::min(y / 2, finest->output_height - 1);
        return band[wave_y * finest->output_width + wave_x];
    };

    for (std::size_t patch_y = 0; patch_y < patch_rows; ++patch_y) {
        const std::size_t start_y = patch_y * config.patch_size;
        const std::size_t end_y = std::min(start_y + config.patch_size, height);
        for (std::size_t patch_x = 0; patch_x < patch_columns; ++patch_x) {
            const std::size_t start_x = patch_x * config.patch_size;
            const std::size_t end_x = std::min(start_x + config.patch_size, width);
            float energy_sum = 0.0f;
            float abs_flow_x_sum = 0.0f;
            float abs_flow_y_sum = 0.0f;
            float flow_magnitude_sum = 0.0f;
            float approximation_sum = 0.0f;
            float detail_sum = 0.0f;
            std::size_t samples = 0;

            for (std::size_t y = start_y; y < end_y; ++y) {
                for (std::size_t x = start_x; x < end_x; ++x) {
                    const std::size_t index = y * width + x;
                    energy_sum += energy[index];
                    abs_flow_x_sum += std::abs(flow_x[index]);
                    abs_flow_y_sum += std::abs(flow_y[index]);
                    flow_magnitude_sum += std::sqrt(flow_x[index] * flow_x[index] + flow_y[index] * flow_y[index]);
                    if (finest != nullptr) {
                        approximation_sum += sampleBand(finest->approximation, x, y);
                        detail_sum += (std::abs(sampleBand(finest->detail_horizontal, x, y)) +
                                       std::abs(sampleBand(finest->detail_vertical, x, y)) +
                                       std::abs(sampleBand(finest->detail_diagonal, x, y))) / 3.0f;
                    }
                    ++samples;
                }
            }
            const float inverse_samples = 1.0f / static_cast<float>(samples);
            Candidate candidate;
            candidate.patch_y = patch_y;
            candidate.patch_x = patch_x;
            candidate.features = {energy_sum * inverse_samples,
                                  abs_flow_x_sum * inverse_samples,
                                  abs_flow_y_sum * inverse_samples,
                                  flow_magnitude_sum * inverse_samples,
                                  approximation_sum * inverse_samples,
                                  detail_sum * inverse_samples};
            candidate.importance = gate.weights[1] * candidate.features[0] +
                                   gate.weights[2] * candidate.features[1] +
                                   gate.weights[3] * candidate.features[2] +
                                   gate.weights[4] * candidate.features[5] +
                                   gate.weights[5] * candidate.features[4] +
                                   0.10f * candidate.features[3];
            candidates.emplace_back(candidate);
        }
    }

    std::stable_sort(candidates.begin(), candidates.end(), [](const Candidate& left, const Candidate& right) {
        if (left.importance != right.importance) {
            return left.importance > right.importance;
        }
        if (left.patch_y != right.patch_y) {
            return left.patch_y < right.patch_y;
        }
        return left.patch_x < right.patch_x;
    });

    std::size_t retained = static_cast<std::size_t>(std::ceil(candidates.size() * config.retention_ratio));
    retained = std::max<std::size_t>(1, retained);
    if (config.max_tokens > 0) {
        retained = std::min(retained, config.max_tokens);
    }
    retained = std::min(retained, candidates.size());

    VisualTokenProjection projection;
    projection.embedding_dimension = config.embedding_dimension;
    projection.source_patch_count = candidates.size();
    projection.retained_token_count = retained;
    projection.patch_y.resize(retained);
    projection.patch_x.resize(retained);
    projection.importance.resize(retained);
    projection.embeddings.resize(retained * config.embedding_dimension);

    constexpr std::array<std::size_t, 6> kFeatureGateIndex = {1, 2, 3, 0, 5, 4};
    for (std::size_t token = 0; token < retained; ++token) {
        const Candidate& candidate = candidates[token];
        projection.patch_y[token] = candidate.patch_y;
        projection.patch_x[token] = candidate.patch_x;
        projection.importance[token] = candidate.importance;
        float square_sum = 0.0f;
        for (std::size_t dimension = 0; dimension < config.embedding_dimension; ++dimension) {
            const float phase = static_cast<float>(dimension + 1) * 0.013f +
                                static_cast<float>(candidate.patch_x + 1) * 0.071f +
                                static_cast<float>(candidate.patch_y + 1) * 0.113f;
            float value = 0.0f;
            for (std::size_t channel = 0; channel < candidate.features.size(); ++channel) {
                const float frequency = static_cast<float>(channel + 1) * 0.37f;
                const float basis = (dimension + channel) % 2 == 0
                    ? std::sin(phase * frequency)
                    : std::cos(phase * frequency);
                value += candidate.features[channel] * gate.weights[kFeatureGateIndex[channel]] * basis;
            }
            value += candidate.importance * 0.05f;
            projection.embeddings[token * config.embedding_dimension + dimension] = value;
            square_sum += value * value;
        }
        const float inverse_rms = 1.0f / std::sqrt(square_sum / static_cast<float>(config.embedding_dimension) + 1.0e-6f);
        for (std::size_t dimension = 0; dimension < config.embedding_dimension; ++dimension) {
            projection.embeddings[token * config.embedding_dimension + dimension] *= inverse_rms;
        }
    }
    return projection;
}

SemanticAttentionGate::SemanticAttentionGate() {
    reset();
}

void SemanticAttentionGate::reset() noexcept {
    for (auto& row : weights_) {
        row.fill(0.0f);
    }
    biases_.fill(0.0f);

    // Deterministic priors: favor detail and flow as visual complexity rises,
    // while retaining low-frequency energy information for smooth scenes.
    biases_[0] = 0.30f;  // RGB
    weights_[1][1] = 0.60f;  // Energy variance
    weights_[2][2] = 0.95f;  // Flow-X variance
    weights_[3][2] = 0.95f;  // Flow-Y variance
    weights_[4][2] = 0.40f;  // Wavelet detail
    weights_[4][3] = 1.35f;
    weights_[5][1] = 0.45f;  // Wavelet approximation
}

SemanticGateOutput SemanticAttentionGate::infer(const SemanticGateFeatures& features) const {
    std::array<float, kOutputCount> logits{};
    float maximum = -std::numeric_limits<float>::infinity();
    for (std::size_t output = 0; output < kOutputCount; ++output) {
        float value = biases_[output];
        for (std::size_t feature = 0; feature < kFeatureCount; ++feature) {
            value += weights_[output][feature] * features.values[feature];
        }
        logits[output] = value;
        maximum = std::max(maximum, value);
    }

    SemanticGateOutput result;
    float normalizer = 0.0f;
    for (std::size_t output = 0; output < kOutputCount; ++output) {
        result.weights[output] = std::exp(logits[output] - maximum);
        normalizer += result.weights[output];
    }
    for (float& weight : result.weights) {
        weight /= normalizer;
    }

    constexpr float kInverseLogOutputs = 1.0f / 1.7917594692280550f; // 1 / ln(6)
    float entropy = 0.0f;
    for (const float weight : result.weights) {
        entropy -= weight * std::log(std::max(weight, 1.0e-12f));
    }
    result.entropy = entropy * kInverseLogOutputs;
    result.complexity = std::clamp(0.30f * features.values[1] +
                                   0.35f * features.values[2] +
                                   0.35f * features.values[3],
                                   0.0f, 1.0f);
    return result;
}

float SemanticAttentionGate::trainStep(const SemanticGateFeatures& features,
                                       const std::array<float, kOutputCount>& target,
                                       float learning_rate,
                                       float* gradient_l2_norm) {
    if (!(learning_rate > 0.0f) || !std::isfinite(learning_rate)) {
        throw std::invalid_argument("Semantic gate learning rate must be finite and positive");
    }
    float target_total = 0.0f;
    for (const float target_weight : target) {
        if (target_weight < 0.0f || !std::isfinite(target_weight)) {
            throw std::invalid_argument("Semantic gate target weights must be finite and non-negative");
        }
        target_total += target_weight;
    }
    if (std::abs(target_total - 1.0f) > 1.0e-4f) {
        throw std::invalid_argument("Semantic gate target weights must sum to one");
    }

    const SemanticGateOutput prediction = infer(features);
    float loss = 0.0f;
    float norm_squared = 0.0f;
    for (std::size_t output = 0; output < kOutputCount; ++output) {
        loss -= target[output] * std::log(std::max(prediction.weights[output], 1.0e-12f));
        const float gradient = prediction.weights[output] - target[output];
        norm_squared += gradient * gradient;
        biases_[output] = std::clamp(biases_[output] - learning_rate * gradient, -4.0f, 4.0f);
        for (std::size_t feature = 0; feature < kFeatureCount; ++feature) {
            const float parameter_gradient = gradient * features.values[feature];
            norm_squared += parameter_gradient * parameter_gradient;
            weights_[output][feature] = std::clamp(weights_[output][feature] - learning_rate * parameter_gradient,
                                                    -4.0f, 4.0f);
        }
    }
    if (gradient_l2_norm != nullptr) {
        *gradient_l2_norm = std::sqrt(norm_squared);
    }
    return loss;
}

HaarWaveletPyramid Atomizer::decomposeEnergyPyramid(const float* energy,
                                                     std::size_t width,
                                                     std::size_t height,
                                                     std::size_t max_levels) const {
    std::size_t pixel_count = 0;
    if (!checkedPixelCount(width, height, pixel_count)) {
        throw std::overflow_error("Wavelet input dimensions exceed supported tensor size");
    }
    if (pixel_count > 0 && energy == nullptr) {
        throw std::invalid_argument("Wavelet decomposition requires a non-null energy buffer");
    }

    HaarWaveletPyramid pyramid;
    pyramid.original_width = width;
    pyramid.original_height = height;
    if (pixel_count == 0 || max_levels == 0) {
        return pyramid;
    }

    std::vector<float> current(energy, energy + pixel_count);
    std::size_t current_width = width;
    std::size_t current_height = height;
    for (std::size_t level_index = 0; level_index < max_levels; ++level_index) {
        if (current_width == 1 && current_height == 1) {
            break;
        }
        WaveletLevel level;
        level.input_width = current_width;
        level.input_height = current_height;
        level.output_width = (current_width + 1) / 2;
        level.output_height = (current_height + 1) / 2;
        const std::size_t output_count = level.output_width * level.output_height;
        level.approximation.resize(output_count);
        level.detail_horizontal.resize(output_count);
        level.detail_vertical.resize(output_count);
        level.detail_diagonal.resize(output_count);

        for (std::size_t y = 0; y < level.output_height; ++y) {
            const std::size_t y0 = y * 2;
            const std::size_t y1 = std::min(y0 + 1, current_height - 1);
            for (std::size_t x = 0; x < level.output_width; ++x) {
                const std::size_t x0 = x * 2;
                const std::size_t x1 = std::min(x0 + 1, current_width - 1);
                const float a = current[y0 * current_width + x0];
                const float b = current[y0 * current_width + x1];
                const float c = current[y1 * current_width + x0];
                const float d = current[y1 * current_width + x1];
                const std::size_t out = y * level.output_width + x;
                level.approximation[out] = 0.5f * (a + b + c + d);
                level.detail_horizontal[out] = 0.5f * (a - b + c - d);
                level.detail_vertical[out] = 0.5f * (a + b - c - d);
                level.detail_diagonal[out] = 0.5f * (a - b - c + d);
            }
        }

        current = level.approximation;
        current_width = level.output_width;
        current_height = level.output_height;
        pyramid.levels.emplace_back(std::move(level));
    }
    return pyramid;
}

std::vector<float> Atomizer::reconstructEnergyPyramid(const HaarWaveletPyramid& pyramid) const {
    if (pyramid.empty()) {
        return {};
    }

    std::vector<float> current = pyramid.levels.back().approximation;
    for (auto iterator = pyramid.levels.rbegin(); iterator != pyramid.levels.rend(); ++iterator) {
        const WaveletLevel& level = *iterator;
        const std::size_t expected_count = level.output_width * level.output_height;
        if (current.size() != expected_count || level.detail_horizontal.size() != expected_count ||
            level.detail_vertical.size() != expected_count || level.detail_diagonal.size() != expected_count) {
            throw std::invalid_argument("Wavelet pyramid has inconsistent sub-band sizes");
        }

        std::vector<float> reconstructed(level.input_width * level.input_height);
        for (std::size_t y = 0; y < level.output_height; ++y) {
            const std::size_t y0 = y * 2;
            const std::size_t y1 = y0 + 1;
            for (std::size_t x = 0; x < level.output_width; ++x) {
                const std::size_t x0 = x * 2;
                const std::size_t x1 = x0 + 1;
                const std::size_t index = y * level.output_width + x;
                const float ll = current[index];
                const float lh = level.detail_horizontal[index];
                const float hl = level.detail_vertical[index];
                const float hh = level.detail_diagonal[index];
                const float a = 0.5f * (ll + lh + hl + hh);
                const float b = 0.5f * (ll - lh + hl - hh);
                const float c = 0.5f * (ll + lh - hl - hh);
                const float d = 0.5f * (ll - lh - hl + hh);
                reconstructed[y0 * level.input_width + x0] = a;
                if (x1 < level.input_width) {
                    reconstructed[y0 * level.input_width + x1] = b;
                }
                if (y1 < level.input_height) {
                    reconstructed[y1 * level.input_width + x0] = c;
                    if (x1 < level.input_width) {
                        reconstructed[y1 * level.input_width + x1] = d;
                    }
                }
            }
        }
        current = std::move(reconstructed);
    }
    return current;
}

SemanticGateFeatures Atomizer::extractGateFeatures(const AtomicContext& context) const {
    const std::size_t pixel_count = context.width * context.height;
    if (pixel_count == 0 || context.energy.size() != pixel_count ||
        context.flow_x.size() != pixel_count || context.flow_y.size() != pixel_count) {
        throw std::invalid_argument("Atomic context does not contain complete base layers");
    }

    double energy_mean = 0.0;
    for (const float value : context.energy) {
        energy_mean += value;
    }
    energy_mean /= static_cast<double>(pixel_count);
    double energy_variance = 0.0;
    double flow_power = 0.0;
    for (std::size_t index = 0; index < pixel_count; ++index) {
        const double energy_delta = static_cast<double>(context.energy[index]) - energy_mean;
        energy_variance += energy_delta * energy_delta;
        flow_power += static_cast<double>(context.flow_x[index]) * context.flow_x[index] +
                      static_cast<double>(context.flow_y[index]) * context.flow_y[index];
    }
    energy_variance /= static_cast<double>(pixel_count);
    flow_power /= static_cast<double>(pixel_count);

    double detail_power = 0.0;
    std::size_t detail_count = 0;
    for (const WaveletLevel& level : context.wavelet.levels) {
        for (std::size_t index = 0; index < level.detail_horizontal.size(); ++index) {
            detail_power += static_cast<double>(level.detail_horizontal[index]) * level.detail_horizontal[index] +
                            static_cast<double>(level.detail_vertical[index]) * level.detail_vertical[index] +
                            static_cast<double>(level.detail_diagonal[index]) * level.detail_diagonal[index];
            detail_count += 3;
        }
    }
    detail_power = detail_count == 0 ? 0.0 : detail_power / static_cast<double>(detail_count);

    SemanticGateFeatures features;
    features.values[0] = 1.0f;
    features.values[1] = static_cast<float>(energy_variance / (energy_variance + 0.02));
    features.values[2] = static_cast<float>(flow_power / (flow_power + 0.01));
    features.values[3] = static_cast<float>(detail_power / (detail_power + 0.01));
    return features;
}

void Atomizer::atomizeMultiScaleInterleaved(const float* color_interleaved,
                                             std::size_t width,
                                             std::size_t height,
                                             float* energy_out,
                                             float* flow_x_out,
                                             float* flow_y_out,
                                             HaarWaveletPyramid& wavelet_out,
                                             SemanticGateFeatures& gate_features_out,
                                             SemanticGateOutput& semantic_gate_out,
                                             std::size_t max_levels) const {
    atomizeInterleaved(color_interleaved, width, height, energy_out, flow_x_out, flow_y_out);
    wavelet_out = decomposeEnergyPyramid(energy_out, width, height, max_levels);
    if (width == 0 || height == 0) {
        gate_features_out = SemanticGateFeatures{};
        SemanticAttentionGate gate;
        semantic_gate_out = gate.infer(gate_features_out);
        return;
    }

    const std::size_t pixel_count = width * height;
    double energy_mean = 0.0;
    for (std::size_t index = 0; index < pixel_count; ++index) {
        energy_mean += energy_out[index];
    }
    energy_mean /= static_cast<double>(pixel_count);
    double energy_variance = 0.0;
    double flow_power = 0.0;
    for (std::size_t index = 0; index < pixel_count; ++index) {
        const double energy_delta = static_cast<double>(energy_out[index]) - energy_mean;
        energy_variance += energy_delta * energy_delta;
        flow_power += static_cast<double>(flow_x_out[index]) * flow_x_out[index] +
                      static_cast<double>(flow_y_out[index]) * flow_y_out[index];
    }
    energy_variance /= static_cast<double>(pixel_count);
    flow_power /= static_cast<double>(pixel_count);
    double detail_power = 0.0;
    std::size_t detail_count = 0;
    for (const WaveletLevel& level : wavelet_out.levels) {
        for (std::size_t index = 0; index < level.detail_horizontal.size(); ++index) {
            detail_power += static_cast<double>(level.detail_horizontal[index]) * level.detail_horizontal[index] +
                            static_cast<double>(level.detail_vertical[index]) * level.detail_vertical[index] +
                            static_cast<double>(level.detail_diagonal[index]) * level.detail_diagonal[index];
            detail_count += 3;
        }
    }
    detail_power = detail_count == 0 ? 0.0 : detail_power / static_cast<double>(detail_count);

    gate_features_out.values = {1.0f,
                                static_cast<float>(energy_variance / (energy_variance + 0.02)),
                                static_cast<float>(flow_power / (flow_power + 0.01)),
                                static_cast<float>(detail_power / (detail_power + 0.01))};
    SemanticAttentionGate gate;
    semantic_gate_out = gate.infer(gate_features_out);
}

AtomicContext Atomizer::atomizeMultiScale(const std::vector<Pixel>& color_matrix,
                                          std::size_t width,
                                          std::size_t height,
                                          std::size_t max_levels) const {
    Atomizer mutable_atomizer;
    AtomicContext context = mutable_atomizer.atomize(color_matrix, width, height);
    context.wavelet = decomposeEnergyPyramid(context.energy.data(), width, height, max_levels);
    context.gate_features = extractGateFeatures(context);
    SemanticAttentionGate gate;
    context.semantic_gate = gate.infer(context.gate_features);
    return context;
}

std::vector<unsigned char> VisionLoader::loadImageFile(const std::string& file_path,
                                                        std::size_t& width,
                                                        std::size_t& height,
                                                        int& channels) {
    int decoded_width = 0;
    int decoded_height = 0;
    unsigned char* data = stbi_load(file_path.c_str(), &decoded_width, &decoded_height, &channels, 3);

    if (data == nullptr || decoded_width <= 0 || decoded_height <= 0) {
        throw std::runtime_error("Failed to load image: " + file_path);
    }

    width = static_cast<std::size_t>(decoded_width);
    height = static_cast<std::size_t>(decoded_height);
    std::size_t num_pixels = 0;
    if (!checkedPixelCount(width, height, num_pixels) || num_pixels > std::numeric_limits<std::size_t>::max() / 3) {
        stbi_image_free(data);
        throw std::overflow_error("Image dimensions exceed supported tensor size");
    }

    std::vector<unsigned char> result(data, data + num_pixels * 3);
    stbi_image_free(data);
    return result;
}

void VisionLoader::saveImageFile(const std::vector<unsigned char>& data,
                                 std::size_t width,
                                 std::size_t height,
                                 const std::string& output_path) {
    if (width > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        height > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
        throw std::overflow_error("Image dimensions exceed PNG encoder limits");
    }

    const int success = stbi_write_png(output_path.c_str(),
                                       static_cast<int>(width),
                                       static_cast<int>(height),
                                       3,
                                       data.data(),
                                       static_cast<int>(width * 3));
    if (success == 0) {
        throw std::runtime_error("Failed to save image: " + output_path);
    }
}

std::vector<Pixel> VisionLoader::loadToMath(const std::string& file_path) {
    std::size_t width = 0;
    std::size_t height = 0;
    int channels = 0;
    const auto raw_data = loadImageFile(file_path, width, height, channels);

    std::size_t pixel_count = 0;
    if (!checkedPixelCount(width, height, pixel_count)) {
        throw std::overflow_error("Image dimensions exceed supported tensor size");
    }

    std::vector<Pixel> matrix(pixel_count);
    constexpr float kNormalization = 1.0f / 255.0f;
    for (std::size_t i = 0; i < pixel_count; ++i) {
        const std::size_t rgb = i * 3;
        matrix[i] = Pixel(static_cast<float>(raw_data[rgb]) * kNormalization,
                          static_cast<float>(raw_data[rgb + 1]) * kNormalization,
                          static_cast<float>(raw_data[rgb + 2]) * kNormalization);
    }
    return matrix;
}

void VisionLoader::saveFromMath(const std::vector<Pixel>& matrix,
                                std::size_t width,
                                std::size_t height,
                                const std::string& output_path) {
    std::size_t pixel_count = 0;
    if (!checkedPixelCount(width, height, pixel_count) || matrix.size() != pixel_count) {
        throw std::invalid_argument("Matrix dimensions do not match the requested image dimensions");
    }

    std::vector<unsigned char> data(pixel_count * 3);
    for (std::size_t i = 0; i < pixel_count; ++i) {
        const Pixel& pixel = matrix[i];
        const std::size_t rgb = i * 3;
        data[rgb] = static_cast<unsigned char>(std::clamp(pixel.r, 0.0f, 1.0f) * 255.0f + 0.5f);
        data[rgb + 1] = static_cast<unsigned char>(std::clamp(pixel.g, 0.0f, 1.0f) * 255.0f + 0.5f);
        data[rgb + 2] = static_cast<unsigned char>(std::clamp(pixel.b, 0.0f, 1.0f) * 255.0f + 0.5f);
    }
    saveImageFile(data, width, height, output_path);
}

AtomicContext Atomizer::atomize(const std::vector<Pixel>& color_matrix,
                                std::size_t width,
                                std::size_t height) {
    std::size_t pixel_count = 0;
    if (!checkedPixelCount(width, height, pixel_count) || color_matrix.size() != pixel_count) {
        throw std::invalid_argument("Color matrix dimensions do not match its storage");
    }

    AtomicContext ctx;
    ctx.width = width;
    ctx.height = height;
    ctx.color = color_matrix;
    ctx.energy.resize(pixel_count);
    ctx.flow_x.resize(pixel_count);
    ctx.flow_y.resize(pixel_count);

    atomizeInterleaved(reinterpret_cast<const float*>(ctx.color.data()), width, height,
                       ctx.energy.data(), ctx.flow_x.data(), ctx.flow_y.data());
    return ctx;
}

void Atomizer::atomizeInterleaved(const float* color_interleaved,
                                  std::size_t width,
                                  std::size_t height,
                                  float* energy_out,
                                  float* flow_x_out,
                                  float* flow_y_out) const {
    std::size_t pixel_count = 0;
    if (!checkedPixelCount(width, height, pixel_count)) {
        throw std::overflow_error("Image dimensions exceed supported tensor size");
    }
    if (pixel_count == 0) {
        return;
    }
    if (color_interleaved == nullptr || energy_out == nullptr || flow_x_out == nullptr || flow_y_out == nullptr) {
        throw std::invalid_argument("Atomizer requires non-null input and output buffers");
    }

    computeEnergyInterleaved(color_interleaved, energy_out, pixel_count);
    computeFlowInterleaved(color_interleaved, width, height, flow_x_out, flow_y_out);
}

void Atomizer::atomizeAcceleratedInterleaved(const float* color_interleaved,
                                             std::size_t width,
                                             std::size_t height,
                                             float* energy_out,
                                             float* flow_x_out,
                                             float* flow_y_out,
                                             ExecutionReport& report) const {
    std::size_t pixel_count = 0;
    if (!checkedPixelCount(width, height, pixel_count)) {
        throw std::overflow_error("Image dimensions exceed supported tensor size");
    }
    if (pixel_count == 0) {
        report = ExecutionReport{};
        report.backend = parallelAvailable() ? "cpu-openmp-avx" : "cpu-reference";
        report.worker_threads = availableWorkerThreads();
        report.simd_enabled = simdAvailable();
        report.parallel_enabled = parallelAvailable();
        return;
    }
    if (color_interleaved == nullptr || energy_out == nullptr || flow_x_out == nullptr || flow_y_out == nullptr) {
        throw std::invalid_argument("Accelerated atomizer requires non-null input and output buffers");
    }

#ifdef ALVS_HAS_OPENMP
    if (height > 1 && parallelAvailable()) {
        #pragma omp parallel for schedule(static)
        for (std::ptrdiff_t row = 0; row < static_cast<std::ptrdiff_t>(height); ++row) {
            const std::size_t y = static_cast<std::size_t>(row);
            computeEnergyInterleaved(color_interleaved + y * width * 3, energy_out + y * width, width);
        }
        computeFlowInterleavedParallel(color_interleaved, width, height, flow_x_out, flow_y_out);
        report.backend = simdAvailable() ? "cpu-openmp-avx" : "cpu-openmp-scalar";
        report.worker_threads = static_cast<std::size_t>(omp_get_max_threads());
        report.simd_enabled = simdAvailable();
        report.parallel_enabled = true;
        report.gpu_available = false;
        return;
    }
#endif

    atomizeInterleaved(color_interleaved, width, height, energy_out, flow_x_out, flow_y_out);
    report.backend = simdAvailable() ? "cpu-avx-reference" : "cpu-reference";
    report.worker_threads = 1;
    report.simd_enabled = simdAvailable();
    report.parallel_enabled = false;
    report.gpu_available = false;
}

void Atomizer::computeEnergyInterleaved(const float* color_interleaved,
                                        float* energy_out,
                                        std::size_t pixel_count) const {
    if (pixel_count == 0) {
        return;
    }
    if (color_interleaved == nullptr || energy_out == nullptr) {
        throw std::invalid_argument("Energy computation requires non-null input and output buffers");
    }

#if defined(__AVX512F__)
    computeEnergyAvx512(color_interleaved, energy_out, pixel_count);
#elif defined(__AVX2__)
    computeEnergyAvx2(color_interleaved, energy_out, pixel_count);
#else
    computeEnergyScalar(color_interleaved, energy_out, pixel_count);
#endif
}

void Atomizer::computeFlowInterleaved(const float* color_interleaved,
                                      std::size_t width,
                                      std::size_t height,
                                      float* flow_x_out,
                                      float* flow_y_out) const {
    auto intensity = [color_interleaved](std::size_t index) noexcept {
        const std::size_t rgb = index * 3;
        return (color_interleaved[rgb] + color_interleaved[rgb + 1] + color_interleaved[rgb + 2]) / 3.0f;
    };

    for (std::size_t y = 0; y < height; ++y) {
        for (std::size_t x = 0; x < width; ++x) {
            const std::size_t index = y * width + x;
            const float center = intensity(index);
            if (width == 1) {
                flow_x_out[index] = 0.0f;
            } else if (x == 0) {
                flow_x_out[index] = intensity(index + 1) - center;
            } else if (x + 1 == width) {
                flow_x_out[index] = center - intensity(index - 1);
            } else {
                flow_x_out[index] = (intensity(index + 1) - intensity(index - 1)) * 0.5f;
            }

            if (height == 1) {
                flow_y_out[index] = 0.0f;
            } else if (y == 0) {
                flow_y_out[index] = intensity(index + width) - center;
            } else if (y + 1 == height) {
                flow_y_out[index] = center - intensity(index - width);
            } else {
                flow_y_out[index] = (intensity(index + width) - intensity(index - width)) * 0.5f;
            }
        }
    }
}

void Atomizer::computeFlowInterleavedParallel(const float* color_interleaved,
                                              std::size_t width,
                                              std::size_t height,
                                              float* flow_x_out,
                                              float* flow_y_out) const {
#ifndef ALVS_HAS_OPENMP
    computeFlowInterleaved(color_interleaved, width, height, flow_x_out, flow_y_out);
    return;
#else
    auto intensity = [color_interleaved](std::size_t index) noexcept {
        const std::size_t rgb = index * 3;
        return (color_interleaved[rgb] + color_interleaved[rgb + 1] + color_interleaved[rgb + 2]) / 3.0f;
    };

    #pragma omp parallel for schedule(static)
    for (std::ptrdiff_t row = 0; row < static_cast<std::ptrdiff_t>(height); ++row) {
        const std::size_t y = static_cast<std::size_t>(row);
        for (std::size_t x = 0; x < width; ++x) {
            const std::size_t index = y * width + x;
            const float center = intensity(index);
            if (width == 1) {
                flow_x_out[index] = 0.0f;
            } else if (x == 0) {
                flow_x_out[index] = intensity(index + 1) - center;
            } else if (x + 1 == width) {
                flow_x_out[index] = center - intensity(index - 1);
            } else {
                flow_x_out[index] = (intensity(index + 1) - intensity(index - 1)) * 0.5f;
            }

            if (height == 1) {
                flow_y_out[index] = 0.0f;
            } else if (y == 0) {
                flow_y_out[index] = intensity(index + width) - center;
            } else if (y + 1 == height) {
                flow_y_out[index] = center - intensity(index - width);
            } else {
                flow_y_out[index] = (intensity(index + width) - intensity(index - width)) * 0.5f;
            }
        }
    }
#endif
}

bool Atomizer::parallelAvailable() const noexcept {
#ifdef ALVS_HAS_OPENMP
    return omp_get_max_threads() > 1;
#else
    return false;
#endif
}

std::size_t Atomizer::availableWorkerThreads() const noexcept {
#ifdef ALVS_HAS_OPENMP
    return static_cast<std::size_t>(omp_get_max_threads());
#else
    return 1;
#endif
}

bool Atomizer::simdAvailable() const noexcept {
#if defined(__AVX512F__) || defined(__AVX2__)
    return true;
#else
    return false;
#endif
}

const char* Atomizer::simdBackend() const noexcept {
#if defined(__AVX512F__)
    return "AVX-512F";
#elif defined(__AVX2__)
    return "AVX2";
#else
    return "scalar";
#endif
}

std::vector<float> Atomizer::getSmartAtom(const AtomicContext& ctx, std::size_t x, std::size_t y) {
    if (x >= ctx.width || y >= ctx.height) {
        return {};
    }

    const std::size_t index = y * ctx.width + x;
    return {static_cast<float>(x), static_cast<float>(y),
            ctx.color[index].r, ctx.color[index].g, ctx.color[index].b,
            ctx.energy[index], ctx.flow_x[index], ctx.flow_y[index]};
}

std::vector<Pixel> Synthesizer::reconstruct(const AtomicContext& ctx) {
    return ctx.color;
}

std::vector<Pixel> Synthesizer::smartRemix(const AtomicContext& ctx, const std::string& mode) {
    if (mode == "visualize_flow") {
        return visualizeFlow(ctx);
    }
    if (mode == "quantum_inverse") {
        return quantumInverse(ctx);
    }
    if (mode == "energy_boost") {
        return energyBoost(ctx);
    }
    return ctx.color;
}

std::vector<Pixel> Synthesizer::visualizeFlow(const AtomicContext& ctx) {
    const std::size_t pixel_count = ctx.width * ctx.height;
    std::vector<Pixel> result(pixel_count);
    for (std::size_t i = 0; i < pixel_count; ++i) {
        const float magnitude = std::sqrt(ctx.flow_x[i] * ctx.flow_x[i] + ctx.flow_y[i] * ctx.flow_y[i]);
        const float flow_visual = std::min(1.0f, magnitude * 5.0f);
        result[i] = Pixel(flow_visual, flow_visual, flow_visual);
    }
    return result;
}

std::vector<Pixel> Synthesizer::quantumInverse(const AtomicContext& ctx) {
    const std::size_t pixel_count = ctx.width * ctx.height;
    std::vector<Pixel> result(pixel_count);
    for (std::size_t i = 0; i < pixel_count; ++i) {
        result[i] = Pixel(1.0f - ctx.color[i].r, 1.0f - ctx.color[i].g, 1.0f - ctx.color[i].b);
    }
    return result;
}

std::vector<Pixel> Synthesizer::energyBoost(const AtomicContext& ctx) {
    const std::size_t pixel_count = ctx.width * ctx.height;
    std::vector<Pixel> result(pixel_count);
    for (std::size_t i = 0; i < pixel_count; ++i) {
        if (ctx.energy[i] > 0.5f) {
            result[i] = Pixel(std::min(1.0f, ctx.color[i].r + 0.2f),
                              std::min(1.0f, ctx.color[i].g + 0.2f),
                              std::min(1.0f, ctx.color[i].b + 0.2f));
        } else {
            result[i] = ctx.color[i];
        }
    }
    return result;
}

} // namespace alvs
