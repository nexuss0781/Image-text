#include "alvs_core.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

namespace {

struct EvaluationResult {
    std::string id;
    bool passed;
    std::string detail;
};

struct TestContext {
    std::size_t width{80};
    std::size_t height{64};
    std::vector<float> interleaved;
    std::vector<float> energy;
    std::vector<float> flow_x;
    std::vector<float> flow_y;
    alvs::HaarWaveletPyramid pyramid;
    alvs::SemanticGateFeatures features;
    alvs::SemanticGateOutput gate;
};

TestContext buildContext() {
    TestContext context;
    const std::size_t pixels = context.width * context.height;
    context.interleaved.resize(pixels * 3);
    for (std::size_t y = 0; y < context.height; ++y) {
        for (std::size_t x = 0; x < context.width; ++x) {
            const std::size_t rgb = (y * context.width + x) * 3;
            const float checker = ((x / 5 + y / 5) % 2 == 0) ? 0.85f : 0.15f;
            context.interleaved[rgb] = checker;
            context.interleaved[rgb + 1] = static_cast<float>(x) / static_cast<float>(context.width - 1);
            context.interleaved[rgb + 2] = static_cast<float>(y) / static_cast<float>(context.height - 1);
        }
    }
    context.energy.resize(pixels);
    context.flow_x.resize(pixels);
    context.flow_y.resize(pixels);
    alvs::Atomizer atomizer;
    atomizer.atomizeMultiScaleInterleaved(context.interleaved.data(), context.width, context.height,
                                          context.energy.data(), context.flow_x.data(), context.flow_y.data(),
                                          context.pyramid, context.features, context.gate, 2);
    return context;
}

float rms(const std::vector<float>& values, std::size_t offset, std::size_t count) {
    float sum = 0.0f;
    for (std::size_t index = 0; index < count; ++index) {
        const float value = values[offset + index];
        sum += value * value;
    }
    return std::sqrt(sum / static_cast<float>(count));
}

alvs::ProjectionConfig defaultConfig() {
    alvs::ProjectionConfig config;
    config.patch_size = 4;
    config.embedding_dimension = 4096;
    config.retention_ratio = 0.25f;
    return config;
}

EvaluationResult testEmbeddingShapeAndNormalization(const TestContext& context) {
    alvs::VisualTokenProjector projector;
    const auto projection = projector.project(context.energy.data(), context.flow_x.data(), context.flow_y.data(),
                                              context.width, context.height, context.pyramid, context.gate,
                                              defaultConfig());
    const bool shaped = projection.embedding_dimension == 4096 &&
                        projection.embeddings.size() == projection.retained_token_count * 4096 &&
                        projection.retained_token_count > 0;
    float max_rms_error = 0.0f;
    for (std::size_t token = 0; token < projection.retained_token_count; ++token) {
        max_rms_error = std::max(max_rms_error,
                                 std::abs(rms(projection.embeddings, token * 4096, 4096) - 1.0f));
    }
    return {"TC-4.1", shaped && max_rms_error < 1.0e-4f,
            "shape=[" + std::to_string(projection.retained_token_count) + ",4096]; max RMSNorm error=" +
                std::to_string(max_rms_error)};
}

EvaluationResult testTokenBudget(const TestContext& context) {
    alvs::VisualTokenProjector projector;
    const auto projection = projector.project(context.energy.data(), context.flow_x.data(), context.flow_y.data(),
                                              context.width, context.height, context.pyramid, context.gate,
                                              defaultConfig());
    const std::size_t expected_source = (context.width + 3) / 4 * ((context.height + 3) / 4);
    const std::size_t expected_retained = static_cast<std::size_t>(std::ceil(expected_source * 0.25f));
    const bool ordered = std::is_sorted(projection.importance.begin(), projection.importance.end(),
                                        std::greater_equal<float>());
    const float reduction = 1.0f - static_cast<float>(projection.retained_token_count) /
                                      static_cast<float>(projection.source_patch_count);
    return {"TC-4.2", projection.source_patch_count == expected_source &&
                           projection.retained_token_count == expected_retained && ordered && reduction >= 0.75f,
            "source patches=" + std::to_string(projection.source_patch_count) + "; retained=" +
                std::to_string(projection.retained_token_count) + "; reduction=" + std::to_string(reduction)};
}

EvaluationResult testDeterminismAndInputIntegrity(const TestContext& context) {
    alvs::VisualTokenProjector projector;
    const std::vector<float> input_before = context.interleaved;
    const auto first = projector.project(context.energy.data(), context.flow_x.data(), context.flow_y.data(),
                                         context.width, context.height, context.pyramid, context.gate, defaultConfig());
    const auto second = projector.project(context.energy.data(), context.flow_x.data(), context.flow_y.data(),
                                          context.width, context.height, context.pyramid, context.gate, defaultConfig());
    const bool deterministic = first.patch_x == second.patch_x && first.patch_y == second.patch_y &&
                               first.importance == second.importance && first.embeddings == second.embeddings;
    return {"TC-4.3", deterministic && context.interleaved == input_before,
            "projection is byte-deterministic; source RGB tensor remains unchanged"};
}

EvaluationResult testBudgetCapAndInvalidConfiguration(const TestContext& context) {
    alvs::VisualTokenProjector projector;
    auto capped = defaultConfig();
    capped.max_tokens = 7;
    const auto projection = projector.project(context.energy.data(), context.flow_x.data(), context.flow_y.data(),
                                              context.width, context.height, context.pyramid, context.gate, capped);
    bool rejected = false;
    try {
        auto invalid = defaultConfig();
        invalid.retention_ratio = 0.0f;
        (void)projector.project(context.energy.data(), context.flow_x.data(), context.flow_y.data(),
                                context.width, context.height, context.pyramid, context.gate, invalid);
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    return {"TC-4.4", projection.retained_token_count == 7 && rejected,
            "max-token cap honored; invalid retention ratio explicitly rejected"};
}

void printResult(const EvaluationResult& result) {
    std::cout << '[' << (result.passed ? "PASS" : "FAIL") << "] " << result.id << " — " << result.detail << '\n';
}

} // namespace

int main() {
    std::cout << "AGI-VS Stage 4 Native Evaluation Harness\n\n";
    std::vector<EvaluationResult> results;
    try {
        const TestContext context = buildContext();
        results.emplace_back(testEmbeddingShapeAndNormalization(context));
        results.emplace_back(testTokenBudget(context));
        results.emplace_back(testDeterminismAndInputIntegrity(context));
        results.emplace_back(testBudgetCapAndInvalidConfiguration(context));
    } catch (const std::exception& error) {
        results.emplace_back(EvaluationResult{"TC-4.runtime", false, error.what()});
    }

    bool passed = true;
    for (const auto& result : results) {
        printResult(result);
        passed = passed && result.passed;
    }
    std::cout << "\nStage 4 native harness: " << (passed ? "PASS" : "FAIL") << '\n';
    return passed ? 0 : 1;
}
