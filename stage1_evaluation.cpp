#include "alvs_core.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <string>
#include <vector>

namespace {

constexpr float kLumaR = 0.2126f;
constexpr float kLumaG = 0.7152f;
constexpr float kLumaB = 0.0722f;
constexpr float kCorrectnessTolerance = 1.0e-6f;

struct EvaluationResult {
    std::string id;
    bool passed;
    std::string detail;
};

void computeEnergyReference(const float* color, float* energy, std::size_t pixel_count) {
    for (std::size_t i = 0; i < pixel_count; ++i) {
        const auto rgb = i * 3;
        energy[i] = color[rgb] * kLumaR + color[rgb + 1] * kLumaG + color[rgb + 2] * kLumaB;
    }
}

float maxAbsError(const std::vector<float>& lhs, const std::vector<float>& rhs) {
    float maximum = 0.0f;
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        maximum = std::max(maximum, std::abs(lhs[i] - rhs[i]));
    }
    return maximum;
}

std::vector<float> makeRandomRgb(std::size_t pixels, std::uint32_t seed = 20260811U) {
    std::mt19937 generator(seed);
    std::uniform_real_distribution<float> distribution(0.0f, 1.0f);
    std::vector<float> values(pixels * 3);
    for (float& value : values) {
        value = distribution(generator);
    }
    return values;
}

EvaluationResult testAlignedAllocation(std::size_t iterations, std::size_t bytes_per_iteration) {
    try {
        std::uint64_t checksum = 0;
        for (std::size_t i = 0; i < iterations; ++i) {
            alvs::AlignedTensorBuffer buffer(bytes_per_iteration);
            if (!buffer.is_aligned() || buffer.data() == nullptr || buffer.size_bytes() != bytes_per_iteration) {
                return {"TC-1.1", false, "aligned allocation metadata was invalid"};
            }
            auto* bytes = static_cast<std::uint8_t*>(buffer.data());
            bytes[0] = static_cast<std::uint8_t>(i);
            bytes[bytes_per_iteration - 1] = static_cast<std::uint8_t>(i >> 8U);
            checksum += bytes[0] + bytes[bytes_per_iteration - 1];
        }
        const double gib = static_cast<double>(iterations) * static_cast<double>(bytes_per_iteration) /
                           (1024.0 * 1024.0 * 1024.0);
        return {"TC-1.1", true, "allocated and released " + std::to_string(iterations) +
                                  " aligned buffers (" + std::to_string(gib) + " GiB cumulative; checksum=" +
                                  std::to_string(checksum) + ")"};
    } catch (const std::exception& error) {
        return {"TC-1.1", false, std::string("allocation raised exception: ") + error.what()};
    }
}

EvaluationResult testEnergyCorrectness(std::size_t pixels) {
    const auto color = makeRandomRgb(pixels);
    std::vector<float> reference(pixels);
    std::vector<float> optimized(pixels);
    computeEnergyReference(color.data(), reference.data(), pixels);

    alvs::Atomizer atomizer;
    atomizer.computeEnergyInterleaved(color.data(), optimized.data(), pixels);
    const float error = maxAbsError(reference, optimized);
    const bool passed = error < kCorrectnessTolerance;
    return {"TC-1.3", passed,
            "backend=" + std::string(atomizer.simdBackend()) + "; pixels=" + std::to_string(pixels) +
                "; maximum absolute error=" + std::to_string(error) + "; threshold=" +
                std::to_string(kCorrectnessTolerance)};
}

EvaluationResult testDirectInterfaceEquivalence() {
    constexpr std::size_t width = 257;
    constexpr std::size_t height = 193;
    constexpr std::size_t pixels = width * height;
    const auto color = makeRandomRgb(pixels, 7U);

    std::vector<alvs::Pixel> legacy_color(pixels);
    for (std::size_t i = 0; i < pixels; ++i) {
        const std::size_t rgb = i * 3;
        legacy_color[i] = alvs::Pixel(color[rgb], color[rgb + 1], color[rgb + 2]);
    }

    alvs::Atomizer atomizer;
    const auto legacy = atomizer.atomize(legacy_color, width, height);
    std::vector<float> energy(pixels);
    std::vector<float> flow_x(pixels);
    std::vector<float> flow_y(pixels);
    atomizer.atomizeInterleaved(color.data(), width, height, energy.data(), flow_x.data(), flow_y.data());

    const float energy_error = maxAbsError(legacy.energy, energy);
    const float flow_x_error = maxAbsError(legacy.flow_x, flow_x);
    const float flow_y_error = maxAbsError(legacy.flow_y, flow_y);
    const float error = std::max({energy_error, flow_x_error, flow_y_error});
    return {"TC-1.4", error < kCorrectnessTolerance,
            "direct path equivalence maximum error=" + std::to_string(error) + "; threshold=" +
                std::to_string(kCorrectnessTolerance)};
}

EvaluationResult testDegenerateDimensions() {
    alvs::Atomizer atomizer;
    const std::vector<std::pair<std::size_t, std::size_t>> shapes = {{1, 1}, {1, 47}, {53, 1}};
    for (const auto& [width, height] : shapes) {
        const std::size_t pixels = width * height;
        const auto color = makeRandomRgb(pixels, static_cast<std::uint32_t>(pixels));
        std::vector<float> energy(pixels);
        std::vector<float> flow_x(pixels);
        std::vector<float> flow_y(pixels);
        atomizer.atomizeInterleaved(color.data(), width, height, energy.data(), flow_x.data(), flow_y.data());
        for (std::size_t i = 0; i < pixels; ++i) {
            if (!std::isfinite(energy[i]) || !std::isfinite(flow_x[i]) || !std::isfinite(flow_y[i])) {
                return {"TC-1.5", false, "non-finite result for degenerate shape " +
                                           std::to_string(width) + "x" + std::to_string(height)};
            }
        }
    }
    return {"TC-1.5", true, "1x1, 1x47, and 53x1 tensors atomized without out-of-bounds behavior"};
}

EvaluationResult benchmarkDirectPipeline(std::size_t iterations) {
    constexpr std::size_t width = 3840;
    constexpr std::size_t height = 2160;
    constexpr std::size_t pixels = width * height;
    const auto color = makeRandomRgb(pixels, 99U);
    std::vector<float> energy(pixels);
    std::vector<float> flow_x(pixels);
    std::vector<float> flow_y(pixels);
    alvs::Atomizer atomizer;

    atomizer.atomizeInterleaved(color.data(), width, height, energy.data(), flow_x.data(), flow_y.data());
    std::vector<double> measurements;
    measurements.reserve(iterations);
    for (std::size_t iteration = 0; iteration < iterations; ++iteration) {
        const auto start = std::chrono::steady_clock::now();
        atomizer.atomizeInterleaved(color.data(), width, height, energy.data(), flow_x.data(), flow_y.data());
        const auto stop = std::chrono::steady_clock::now();
        const std::chrono::duration<double, std::milli> elapsed = stop - start;
        measurements.push_back(elapsed.count());
    }
    std::sort(measurements.begin(), measurements.end());
    const double median_ms = measurements[measurements.size() / 2];
    const double p95_ms = measurements[static_cast<std::size_t>(std::ceil(measurements.size() * 0.95)) - 1];
    const double frames_per_second = 1000.0 / median_ms;

    // This is a characterization metric, not a portable hard gate. Hardware-normalized
    // pass/fail thresholds are recorded in the Stage 1 transition document.
    return {"TC-1.6", std::isfinite(median_ms) && median_ms > 0.0,
            "4K direct atomization: median=" + std::to_string(median_ms) + " ms; p95=" +
                std::to_string(p95_ms) + " ms; throughput=" + std::to_string(frames_per_second) + " FPS"};
}

void printResult(const EvaluationResult& result) {
    std::cout << '[' << (result.passed ? "PASS" : "FAIL") << "] " << result.id << " — " << result.detail << '\n';
}

} // namespace

int main(int argc, char** argv) {
    bool quick = false;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--quick") {
            quick = true;
        }
    }

    const std::size_t stress_iterations = quick ? 32 : 1024;
    const std::size_t stress_bytes = 4ULL * 1024ULL * 1024ULL;
    const std::size_t correctness_pixels = quick ? 1'000'000ULL : 10'000'000ULL;
    const std::size_t benchmark_iterations = quick ? 5 : 21;

    std::cout << "AGI-VS Stage 1 Native Evaluation Harness\n";
    std::cout << "Mode: " << (quick ? "quick" : "full") << "\n\n";

    std::vector<EvaluationResult> results;
    results.emplace_back(testAlignedAllocation(stress_iterations, stress_bytes));
    results.emplace_back(testEnergyCorrectness(correctness_pixels));
    results.emplace_back(testDirectInterfaceEquivalence());
    results.emplace_back(testDegenerateDimensions());
    results.emplace_back(benchmarkDirectPipeline(benchmark_iterations));

    bool all_passed = true;
    for (const auto& result : results) {
        printResult(result);
        all_passed = all_passed && result.passed;
    }

    std::cout << "\nStage 1 native harness: " << (all_passed ? "PASS" : "FAIL") << '\n';
    return all_passed ? 0 : 1;
}
