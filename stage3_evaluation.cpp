#include "alvs_core.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <vector>

namespace {

constexpr float kTolerance = 1.0e-6f;

struct EvaluationResult {
    std::string id;
    bool passed;
    std::string detail;
};

std::vector<float> makeRgb(std::size_t pixels) {
    std::mt19937 generator(20260812U);
    std::uniform_real_distribution<float> distribution(0.0f, 1.0f);
    std::vector<float> tensor(pixels * 3);
    for (float& value : tensor) {
        value = distribution(generator);
    }
    return tensor;
}

float maxAbsError(const std::vector<float>& expected, const std::vector<float>& actual) {
    float maximum = 0.0f;
    for (std::size_t index = 0; index < expected.size(); ++index) {
        maximum = std::max(maximum, std::abs(expected[index] - actual[index]));
    }
    return maximum;
}

template <typename Callable>
double medianMilliseconds(Callable&& callable, std::size_t iterations) {
    std::vector<double> samples;
    samples.reserve(iterations);
    callable();
    for (std::size_t iteration = 0; iteration < iterations; ++iteration) {
        const auto start = std::chrono::steady_clock::now();
        callable();
        const auto stop = std::chrono::steady_clock::now();
        samples.emplace_back(std::chrono::duration<double, std::milli>(stop - start).count());
    }
    std::sort(samples.begin(), samples.end());
    return samples[samples.size() / 2];
}

EvaluationResult testReferenceEquivalence(std::size_t width, std::size_t height) {
    const std::size_t pixels = width * height;
    const auto color = makeRgb(pixels);
    std::vector<float> energy_reference(pixels), flow_x_reference(pixels), flow_y_reference(pixels);
    std::vector<float> energy_accelerated(pixels), flow_x_accelerated(pixels), flow_y_accelerated(pixels);

    alvs::Atomizer atomizer;
    atomizer.atomizeInterleaved(color.data(), width, height, energy_reference.data(),
                                flow_x_reference.data(), flow_y_reference.data());
    alvs::ExecutionReport report;
    atomizer.atomizeAcceleratedInterleaved(color.data(), width, height, energy_accelerated.data(),
                                           flow_x_accelerated.data(), flow_y_accelerated.data(), report);

    const float error = std::max({maxAbsError(energy_reference, energy_accelerated),
                                  maxAbsError(flow_x_reference, flow_x_accelerated),
                                  maxAbsError(flow_y_reference, flow_y_accelerated)});
    return {"TC-3.1", error < kTolerance,
            "maximum reference deviation=" + std::to_string(error) + "; threshold=" +
                std::to_string(kTolerance) + "; backend=" + report.backend +
                "; workers=" + std::to_string(report.worker_threads)};
}

EvaluationResult testDeterminism(std::size_t width, std::size_t height) {
    const std::size_t pixels = width * height;
    const auto color = makeRgb(pixels);
    std::vector<float> energy_a(pixels), flow_x_a(pixels), flow_y_a(pixels);
    std::vector<float> energy_b(pixels), flow_x_b(pixels), flow_y_b(pixels);
    alvs::Atomizer atomizer;
    alvs::ExecutionReport report_a;
    alvs::ExecutionReport report_b;
    atomizer.atomizeAcceleratedInterleaved(color.data(), width, height, energy_a.data(), flow_x_a.data(),
                                           flow_y_a.data(), report_a);
    atomizer.atomizeAcceleratedInterleaved(color.data(), width, height, energy_b.data(), flow_x_b.data(),
                                           flow_y_b.data(), report_b);
    const float error = std::max({maxAbsError(energy_a, energy_b),
                                  maxAbsError(flow_x_a, flow_x_b),
                                  maxAbsError(flow_y_a, flow_y_b)});
    return {"TC-3.2", error == 0.0f && report_a.backend == report_b.backend,
            "repeat-run deviation=" + std::to_string(error) + "; backend=" + report_a.backend};
}

EvaluationResult testDispatchReport() {
    alvs::Atomizer atomizer;
    const bool parallel = atomizer.parallelAvailable();
    const std::size_t workers = atomizer.availableWorkerThreads();
    const bool passed = workers >= 1 && (!parallel || workers > 1);
    return {"TC-3.3", passed,
            "parallel_available=" + std::string(parallel ? "true" : "false") +
                "; workers=" + std::to_string(workers) + "; SIMD=" + atomizer.simdBackend() +
                "; CUDA runtime unavailable on validation host"};
}

EvaluationResult benchmarkDispatch(std::size_t width, std::size_t height, std::size_t iterations) {
    const std::size_t pixels = width * height;
    const auto color = makeRgb(pixels);
    std::vector<float> energy(pixels), flow_x(pixels), flow_y(pixels);
    alvs::Atomizer atomizer;
    alvs::ExecutionReport report;
    const double reference_ms = medianMilliseconds([&]() {
        atomizer.atomizeInterleaved(color.data(), width, height, energy.data(), flow_x.data(), flow_y.data());
    }, iterations);
    const double accelerated_ms = medianMilliseconds([&]() {
        atomizer.atomizeAcceleratedInterleaved(color.data(), width, height, energy.data(), flow_x.data(),
                                               flow_y.data(), report);
    }, iterations);
    const double speedup = reference_ms / accelerated_ms;
    const double fps = 1000.0 / accelerated_ms;
    const bool finite = std::isfinite(speedup) && std::isfinite(fps) && accelerated_ms > 0.0;
    return {"TC-3.4", finite,
            std::to_string(width) + "x" + std::to_string(height) + "; reference=" +
                std::to_string(reference_ms) + " ms; dispatched=" + std::to_string(accelerated_ms) +
                " ms; speedup=" + std::to_string(speedup) + "x; throughput=" + std::to_string(fps) +
                " FPS; backend=" + report.backend};
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
    const std::size_t width = quick ? 640 : 1920;
    const std::size_t height = quick ? 480 : 1080;
    const std::size_t iterations = quick ? 5 : 15;

    std::cout << "AGI-VS Stage 3 Native Evaluation Harness\n";
    std::cout << "Mode: " << (quick ? "quick" : "full") << "\n\n";
    std::vector<EvaluationResult> results;
    try {
        results.emplace_back(testReferenceEquivalence(width, height));
        results.emplace_back(testDeterminism(width, height));
        results.emplace_back(testDispatchReport());
        results.emplace_back(benchmarkDispatch(width, height, iterations));
    } catch (const std::exception& error) {
        results.emplace_back(EvaluationResult{"TC-3.runtime", false, error.what()});
    }

    bool passed = true;
    for (const EvaluationResult& result : results) {
        printResult(result);
        passed = passed && result.passed;
    }
    std::cout << "\nStage 3 native harness: " << (passed ? "PASS" : "FAIL") << '\n';
    return passed ? 0 : 1;
}
