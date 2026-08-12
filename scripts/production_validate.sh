#!/usr/bin/env bash
# Reproducible CPU-path production validation for AGI-VS.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build-production"

cmake -S "${ROOT_DIR}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DALVS_BUILD_PYTHON_MODULE=ON \
  -DALVS_BUILD_STAGE1_EVALUATION=ON \
  -DALVS_BUILD_STAGE2_EVALUATION=ON \
  -DALVS_BUILD_STAGE3_EVALUATION=ON \
  -DALVS_BUILD_STAGE4_EVALUATION=ON \
  -DALVS_BUILD_STAGE5_EVALUATION=ON
cmake --build "${BUILD_DIR}" --parallel
ctest --test-dir "${BUILD_DIR}" --output-on-failure
"${BUILD_DIR}/stage5_evaluation" | tee "${ROOT_DIR}/Stages/stage5_native_full_results.txt"
PYTHONPATH="${BUILD_DIR}${PYTHONPATH:+:${PYTHONPATH}}" python3 "${ROOT_DIR}/stage4_python_evaluation.py"
PYTHONPATH="${BUILD_DIR}${PYTHONPATH:+:${PYTHONPATH}}" python3 "${ROOT_DIR}/stage5_python_evaluation.py"
python3 "${ROOT_DIR}/scripts/release_manifest.py" \
  --repository "${ROOT_DIR}" \
  --output "${ROOT_DIR}/Stages/stage5_release_manifest.json"

echo "Stage 5 CPU production validation completed successfully."
