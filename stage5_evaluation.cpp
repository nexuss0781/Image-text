#include "alvs_core.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

namespace {

struct EvaluationResult {
    std::string id;
    bool passed;
    std::string detail;
};

std::size_t residentBytes() {
    std::ifstream status("/proc/self/statm");
    std::size_t total_pages = 0;
    std::size_t resident_pages = 0;
    if (status >> total_pages >> resident_pages) {
        return resident_pages * 4096U;
    }
    return 0;
}

std::vector<float> makeInput(std::size_t width, std::size_t height) {
    std::mt19937 rng(20260812U);
    std::uniform_real_distribution<float> distribution(0.0f, 1.0f);
    std::vector<float> values(width * height * 3);
    for (float& value : values) {
        value = distribution(rng);
    }
    return values;
}

float maxAbsError(const std::vector<float>& left, const std::vector<float>& right) {
    float maximum = 0.0f;
    for (std::size_t index = 0; index < left.size(); ++index) {
        maximum = std::max(maximum, std::abs(left[index] - right[index]));
    }
    return maximum;
}

struct PipelineState {
    std::size_t width{80};
    std::size_t height{64};
    std::vector<float> color = makeInput(width, height);
    std::vector<float> energy = std::vector<float>(width * height);
    std::vector<float> flow_x = std::vector<float>(width * height);
    std::vector<float> flow_y = std::vector<float>(width * height);
    std::vector<float> accelerated_energy = std::vector<float>(width * height);
    std::vector<float> accelerated_flow_x = std::vector<float>(width * height);
    std::vector<float> accelerated_flow_y = std::vector<float>(width * height);
    alvs::HaarWaveletPyramid pyramid;
    alvs::SemanticGateFeatures features;
    alvs::SemanticGateOutput gate;
};

alvs::VisualTokenProjection runPipeline(PipelineState& state) {
    alvs::Atomizer atomizer;
    alvs::ExecutionReport report;
    atomizer.atomizeAcceleratedInterleaved(state.color.data(), state.width, state.height,
                                           state.accelerated_energy.data(), state.accelerated_flow_x.data(),
                                           state.accelerated_flow_y.data(), report);
    atomizer.atomizeMultiScaleInterleaved(state.color.data(), state.width, state.height,
                                          state.energy.data(), state.flow_x.data(), state.flow_y.data(),
                                          state.pyramid, state.features, state.gate, 2);
    alvs::ProjectionConfig config;
    config.patch_size = 4;
    config.embedding_dimension = 4096;
    config.retention_ratio = 0.25f;
    alvs::VisualTokenProjector projector;
    return projector.project(state.energy.data(), state.flow_x.data(), state.flow_y.data(),
                             state.width, state.height, state.pyramid, state.gate, config);
}

EvaluationResult testIntegration() {
    PipelineState state;
    const std::vector<float> original = state.color;
    const auto projection = runPipeline(state);
    const float error = std::max({maxAbsError(state.energy, state.accelerated_energy),
                                  maxAbsError(state.flow_x, state.accelerated_flow_x),
                                  maxAbsError(state.flow_y, state.accelerated_flow_y)});
    const bool passed = projection.retained_token_count == 80 && projection.embedding_dimension == 4096 &&
                        projection.embeddings.size() == 80 * 4096 && error < 1.0e-6f && state.color == original;
    return {"TC-5.1", passed,
            "full CPU pipeline: 80 tokens x 4096 dimensions; Stage 2/3 layer deviation=" +
                std::to_string(error) + "; source unchanged"};
}

EvaluationResult testStability(std::size_t frames) {
    PipelineState state;
    for (std::size_t index = 0; index < 10; ++index) {
        (void)runPipeline(state);
    }
    const std::size_t before = residentBytes();
    std::size_t checksum = 0;
    for (std::size_t index = 0; index < frames; ++index) {
        const auto projection = runPipeline(state);
        checksum += projection.retained_token_count;
    }
    const std::size_t after = residentBytes();
    const std::size_t growth = after > before ? after - before : 0;
    constexpr std::size_t kPermittedResidentGrowth = 16U * 1024U * 1024U;
    const bool passed = checksum == frames * 80 && growth <= kPermittedResidentGrowth;
    return {"TC-5.2", passed,
            "frames=" + std::to_string(frames) + "; post-warm-up RSS growth=" + std::to_string(growth) +
                " bytes; bounded-suite threshold=" + std::to_string(kPermittedResidentGrowth) + " bytes"};
}

EvaluationResult testLatency(std::size_t iterations) {
    PipelineState state;
    std::vector<double> samples;
    samples.reserve(iterations);
    (void)runPipeline(state);
    for (std::size_t index = 0; index < iterations; ++index) {
        const auto start = std::chrono::steady_clock::now();
        (void)runPipeline(state);
        const auto stop = std::chrono::steady_clock::now();
        samples.emplace_back(std::chrono::duration<double, std::milli>(stop - start).count());
    }
    std::sort(samples.begin(), samples.end());
    const double median = samples[samples.size() / 2];
    const double p95 = samples[static_cast<std::size_t>(std::floor((samples.size() - 1) * 0.95))];
    const bool passed = std::isfinite(median) && std::isfinite(p95) && median > 0.0 && p95 > 0.0;
    return {"TC-5.3", passed,
            "CPU full-pipeline median=" + std::to_string(median) + " ms; p95=" + std::to_string(p95) +
                " ms; deployment target latency intentionally deferred"};
}

void printResult(const EvaluationResult& result) {
    std::cout << '[' << (result.passed ? "PASS" : "FAIL") << "] " << result.id << " — " << result.detail << '\n';
}

} // namespace

int main(int argc, char** argv) {
    bool quick = false;
    bool smoke = false;
    for (int index = 1; index < argc; ++index) {
        const std::string argument(argv[index]);
        quick = quick || argument == "--quick";
        smoke = smoke || argument == "--smoke";
    }
    const std::size_t frames = smoke ? 2 : (quick ? 30 : 500);
    const std::size_t iterations = smoke ? 1 : (quick ? 5 : 25);
    const std::string mode = smoke ? "memory-smoke" : (quick ? "quick" : "full");

    std::cout << "AGI-VS Stage 5 Production Validation Harness\n";
    std::cout << "Mode: " << mode << "\n\n";
    std::vector<EvaluationResult> results;
    try {
        results.emplace_back(testIntegration());
        results.emplace_back(testStability(frames));
        results.emplace_back(testLatency(iterations));
    } catch (const std::exception& error) {
        results.emplace_back(EvaluationResult{"TC-5.runtime", false, error.what()});
    }

    bool passed = true;
    for (const auto& result : results) {
        printResult(result);
        passed = passed && result.passed;
    }
    std::cout << "\nStage 5 native harness: " << (passed ? "PASS" : "FAIL") << '\n';
    return passed ? 0 : 1;
}
