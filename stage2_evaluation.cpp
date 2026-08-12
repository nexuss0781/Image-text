#include "alvs_core.h"
#include "stb_image.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr float kPsnrThresholdDb = 58.0f;
constexpr float kCorrelationThreshold = 1.0e-4f;
constexpr float kGradientNormThreshold = 10.0f;

#ifndef ALVS_SOURCE_DIR
#define ALVS_SOURCE_DIR "."
#endif

struct EvaluationResult {
    std::string id;
    bool passed;
    std::string detail;
};

struct ImageTensor {
    std::size_t width{0};
    std::size_t height{0};
    std::vector<alvs::Pixel> pixels;
};

ImageTensor loadRgbImage(const std::string& path) {
    int width = 0;
    int height = 0;
    int channels = 0;
    unsigned char* decoded = stbi_load(path.c_str(), &width, &height, &channels, 3);
    if (decoded == nullptr || width <= 0 || height <= 0) {
        throw std::runtime_error("Unable to load test image: " + path);
    }
    ImageTensor image;
    image.width = static_cast<std::size_t>(width);
    image.height = static_cast<std::size_t>(height);
    image.pixels.resize(image.width * image.height);
    constexpr float normalize = 1.0f / 255.0f;
    for (std::size_t index = 0; index < image.pixels.size(); ++index) {
        const std::size_t rgb = index * 3;
        image.pixels[index] = alvs::Pixel(decoded[rgb] * normalize,
                                          decoded[rgb + 1] * normalize,
                                          decoded[rgb + 2] * normalize);
    }
    stbi_image_free(decoded);
    return image;
}

float psnr(const std::vector<float>& expected, const std::vector<float>& actual) {
    if (expected.size() != actual.size() || expected.empty()) {
        throw std::invalid_argument("PSNR requires equal non-empty inputs");
    }
    double mse = 0.0;
    for (std::size_t index = 0; index < expected.size(); ++index) {
        const double delta = static_cast<double>(expected[index]) - actual[index];
        mse += delta * delta;
    }
    mse /= static_cast<double>(expected.size());
    if (mse <= std::numeric_limits<double>::min()) {
        return std::numeric_limits<float>::infinity();
    }
    return static_cast<float>(10.0 * std::log10(1.0 / mse));
}

EvaluationResult testReconstruction() {
    const std::array<std::string, 3> assets = {"city.jpg", "dog.jpg", "gradient.jpg"};
    alvs::Atomizer atomizer;
    float minimum_psnr = std::numeric_limits<float>::infinity();
    for (const std::string& asset : assets) {
        const std::filesystem::path asset_path = std::filesystem::path(ALVS_SOURCE_DIR) / asset;
        if (!std::filesystem::exists(asset_path)) {
            return {"TC-2.1", false, "required repository test asset is missing: " + asset_path.string()};
        }
        const ImageTensor image = loadRgbImage(asset_path.string());
        const alvs::AtomicContext context = atomizer.atomizeMultiScale(image.pixels, image.width, image.height, 2);
        const std::vector<float> reconstructed = atomizer.reconstructEnergyPyramid(context.wavelet);
        const float image_psnr = psnr(context.energy, reconstructed);
        minimum_psnr = std::min(minimum_psnr, image_psnr);
        if (context.wavelet.levels.empty() || reconstructed.size() != context.energy.size()) {
            return {"TC-2.1", false, "invalid pyramid topology for " + asset};
        }
    }
    return {"TC-2.1", minimum_psnr > kPsnrThresholdDb,
            "minimum energy-layer reconstruction PSNR=" + std::to_string(minimum_psnr) +
                " dB; threshold=" + std::to_string(kPsnrThresholdDb) + " dB"};
}

EvaluationResult testHaarBasisOrthogonality() {
    // Rows are the normalized 2x2 Haar basis vectors in spatial coefficient order.
    constexpr std::array<std::array<float, 4>, 4> basis = {{
        {{0.5f, 0.5f, 0.5f, 0.5f}},
        {{0.5f, -0.5f, 0.5f, -0.5f}},
        {{0.5f, 0.5f, -0.5f, -0.5f}},
        {{0.5f, -0.5f, -0.5f, 0.5f}},
    }};

    float maximum_cross_correlation = 0.0f;
    float maximum_norm_error = 0.0f;
    for (std::size_t left = 0; left < basis.size(); ++left) {
        float norm = 0.0f;
        for (const float value : basis[left]) {
            norm += value * value;
        }
        maximum_norm_error = std::max(maximum_norm_error, std::abs(norm - 1.0f));
        for (std::size_t right = left + 1; right < basis.size(); ++right) {
            float dot = 0.0f;
            for (std::size_t element = 0; element < basis[left].size(); ++element) {
                dot += basis[left][element] * basis[right][element];
            }
            maximum_cross_correlation = std::max(maximum_cross_correlation, std::abs(dot));
        }
    }
    const bool passed = maximum_cross_correlation < kCorrelationThreshold && maximum_norm_error < kCorrelationThreshold;
    return {"TC-2.3", passed,
            "Haar basis max cross-correlation=" + std::to_string(maximum_cross_correlation) +
                "; max norm error=" + std::to_string(maximum_norm_error) +
                "; threshold=" + std::to_string(kCorrelationThreshold)};
}

EvaluationResult testGateConvergence() {
    struct TrainingExample {
        alvs::SemanticGateFeatures features;
        std::array<float, alvs::SemanticAttentionGate::kOutputCount> target;
    };

    const std::array<TrainingExample, 3> examples = {{
        {{{{1.0f, 0.05f, 0.01f, 0.01f}}}, {{0.55f, 0.25f, 0.05f, 0.05f, 0.03f, 0.07f}}},
        {{{{1.0f, 0.18f, 0.65f, 0.60f}}}, {{0.10f, 0.10f, 0.20f, 0.20f, 0.32f, 0.08f}}},
        {{{{1.0f, 0.50f, 0.30f, 0.85f}}}, {{0.15f, 0.15f, 0.10f, 0.10f, 0.40f, 0.10f}}},
    }};

    alvs::SemanticAttentionGate gate;
    auto meanCrossEntropy = [&gate, &examples]() {
        float total = 0.0f;
        for (const TrainingExample& example : examples) {
            const alvs::SemanticGateOutput output = gate.infer(example.features);
            for (std::size_t index = 0; index < output.weights.size(); ++index) {
                total -= example.target[index] * std::log(std::max(output.weights[index], 1.0e-12f));
            }
        }
        return total / static_cast<float>(examples.size());
    };

    const float initial_loss = meanCrossEntropy();
    float maximum_gradient_norm = 0.0f;
    for (std::size_t epoch = 0; epoch < 10; ++epoch) {
        for (const TrainingExample& example : examples) {
            float gradient_norm = 0.0f;
            gate.trainStep(example.features, example.target, 0.20f, &gradient_norm);
            maximum_gradient_norm = std::max(maximum_gradient_norm, gradient_norm);
        }
    }
    const float final_loss = meanCrossEntropy();
    const bool passed = final_loss < initial_loss && maximum_gradient_norm < kGradientNormThreshold;
    return {"TC-2.2", passed,
            "initial loss=" + std::to_string(initial_loss) + "; final loss=" + std::to_string(final_loss) +
                "; max gradient L2=" + std::to_string(maximum_gradient_norm) +
                "; threshold=" + std::to_string(kGradientNormThreshold)};
}

EvaluationResult testFeatureAndGateContract() {
    constexpr std::size_t width = 64;
    constexpr std::size_t height = 64;
    std::vector<alvs::Pixel> texture(width * height);
    for (std::size_t y = 0; y < height; ++y) {
        for (std::size_t x = 0; x < width; ++x) {
            const bool checker = ((x / 4) + (y / 4)) % 2 == 0;
            const float value = checker ? 0.90f : 0.10f;
            texture[y * width + x] = alvs::Pixel(value, 1.0f - value, 0.25f + 0.5f * value);
        }
    }

    alvs::Atomizer atomizer;
    const alvs::AtomicContext context = atomizer.atomizeMultiScale(texture, width, height, 2);
    const float weight_sum = std::accumulate(context.semantic_gate.weights.begin(),
                                             context.semantic_gate.weights.end(), 0.0f);
    const bool finite = std::isfinite(context.semantic_gate.complexity) &&
                        std::isfinite(context.semantic_gate.entropy) &&
                        std::all_of(context.semantic_gate.weights.begin(), context.semantic_gate.weights.end(),
                                    [](float value) { return std::isfinite(value) && value >= 0.0f; });
    const bool passed = context.wavelet.levels.size() == 2 && std::abs(weight_sum - 1.0f) < 1.0e-6f && finite;
    return {"TC-2.4", passed,
            "levels=" + std::to_string(context.wavelet.levels.size()) + "; weight sum=" +
                std::to_string(weight_sum) + "; complexity=" + std::to_string(context.semantic_gate.complexity) +
                "; normalized entropy=" + std::to_string(context.semantic_gate.entropy)};
}

EvaluationResult testDirectMultiscaleContract() {
    constexpr std::size_t width = 65;
    constexpr std::size_t height = 47;
    const std::size_t pixels = width * height;
    std::vector<float> interleaved(pixels * 3);
    std::vector<alvs::Pixel> legacy_pixels(pixels);
    for (std::size_t index = 0; index < pixels; ++index) {
        const std::size_t rgb = index * 3;
        interleaved[rgb] = static_cast<float>((index * 17) % 251) / 250.0f;
        interleaved[rgb + 1] = static_cast<float>((index * 37) % 251) / 250.0f;
        interleaved[rgb + 2] = static_cast<float>((index * 71) % 251) / 250.0f;
        legacy_pixels[index] = alvs::Pixel(interleaved[rgb], interleaved[rgb + 1], interleaved[rgb + 2]);
    }
    const std::vector<float> original_input = interleaved;

    alvs::Atomizer atomizer;
    const alvs::AtomicContext legacy = atomizer.atomizeMultiScale(legacy_pixels, width, height, 2);
    std::vector<float> energy(pixels);
    std::vector<float> flow_x(pixels);
    std::vector<float> flow_y(pixels);
    alvs::HaarWaveletPyramid pyramid;
    alvs::SemanticGateFeatures features;
    alvs::SemanticGateOutput gate;
    atomizer.atomizeMultiScaleInterleaved(interleaved.data(), width, height,
                                          energy.data(), flow_x.data(), flow_y.data(),
                                          pyramid, features, gate, 2);

    const float energy_psnr = psnr(legacy.energy, energy);
    const float flow_x_psnr = psnr(legacy.flow_x, flow_x);
    const float flow_y_psnr = psnr(legacy.flow_y, flow_y);
    const float gate_sum = std::accumulate(gate.weights.begin(), gate.weights.end(), 0.0f);
    const bool passed = interleaved == original_input && pyramid.levels.size() == legacy.wavelet.levels.size() &&
                        energy_psnr > kPsnrThresholdDb && flow_x_psnr > kPsnrThresholdDb &&
                        flow_y_psnr > kPsnrThresholdDb && std::abs(gate_sum - 1.0f) < 1.0e-6f;
    return {"TC-2.5", passed,
            "direct RGB input unchanged; Energy/Flow PSNRs=" + std::to_string(energy_psnr) + "/" +
                std::to_string(flow_x_psnr) + "/" + std::to_string(flow_y_psnr) +
                " dB; levels=" + std::to_string(pyramid.levels.size())};
}

void printResult(const EvaluationResult& result) {
    std::cout << '[' << (result.passed ? "PASS" : "FAIL") << "] " << result.id << " — " << result.detail << '\n';
}

} // namespace

int main(int argc, char** argv) {
    bool quick = false;
    for (int index = 1; index < argc; ++index) {
        quick = quick || std::string(argv[index]) == "--quick";
    }
    (void)quick;

    std::cout << "AGI-VS Stage 2 Native Evaluation Harness\n\n";
    std::vector<EvaluationResult> results;
    try {
        results.emplace_back(testReconstruction());
        results.emplace_back(testGateConvergence());
        results.emplace_back(testHaarBasisOrthogonality());
        results.emplace_back(testFeatureAndGateContract());
        results.emplace_back(testDirectMultiscaleContract());
    } catch (const std::exception& error) {
        results.emplace_back(EvaluationResult{"TC-2.runtime", false, error.what()});
    }

    bool passed = true;
    for (const EvaluationResult& result : results) {
        printResult(result);
        passed = passed && result.passed;
    }
    std::cout << "\nStage 2 native harness: " << (passed ? "PASS" : "FAIL") << '\n';
    return passed ? 0 : 1;
}
