#include "alvs_core.h"

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#if defined(__AVX512F__) || defined(__AVX2__)
#include <immintrin.h>
#endif

#include <cstring>
#include <limits>

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
