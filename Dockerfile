# syntax=docker/dockerfile:1
# CPU-only production image. CUDA/TensorRT deployment is intentionally a separate,
# hardware-validated build path and is not implied by this artifact.
FROM debian:bookworm-slim AS builder

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3 \
    python3-dev \
    pybind11-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/agi-vision-substrate
COPY . .
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
      -DALVS_BUILD_PYTHON_MODULE=ON \
      -DALVS_BUILD_STAGE1_EVALUATION=ON \
      -DALVS_BUILD_STAGE2_EVALUATION=ON \
      -DALVS_BUILD_STAGE3_EVALUATION=ON \
      -DALVS_BUILD_STAGE4_EVALUATION=ON \
      -DALVS_BUILD_STAGE5_EVALUATION=ON \
    && cmake --build build --parallel \
    && cd build && ctest --output-on-failure

FROM debian:bookworm-slim AS runtime

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/agi-vision-substrate
COPY --from=builder /opt/agi-vision-substrate/build/stage5_evaluation /usr/local/bin/agi-vs-production-check
COPY --from=builder /opt/agi-vision-substrate/build/alvs_cpp*.so /opt/agi-vision-substrate/
COPY --from=builder /opt/agi-vision-substrate/alvs_core.h /opt/agi-vision-substrate/
COPY --from=builder /opt/agi-vision-substrate/alvs.py /opt/agi-vision-substrate/
COPY --from=builder /opt/agi-vision-substrate/atomizer.py /opt/agi-vision-substrate/
COPY --from=builder /opt/agi-vision-substrate/synthesizer.py /opt/agi-vision-substrate/
COPY --from=builder /opt/agi-vision-substrate/vision_loader.py /opt/agi-vision-substrate/

ENV PYTHONPATH=/opt/agi-vision-substrate
ENTRYPOINT ["/usr/local/bin/agi-vs-production-check"]
CMD ["--quick"]
