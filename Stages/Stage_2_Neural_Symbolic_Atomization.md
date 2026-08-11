# Stage 2: Neural-Symbolic Atomization & Semantic Feature Fusion

**Author**: **Manus AI**  
**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: Rigorous Implementation & Pass/Fail Evaluation Specification  

---

## 1. Stage Overview & Engineering Objectives

Stage 2 bridges low-level computational physics (RGB matrices, energy luminance, and Sobel/Scharr flow gradients) with high-level neural semantics. Traditional vision models rely on rigid token patching that ignores fine-grained edge topology and luminance gradients. Stage 2 extends the Atomizer module to extract multi-scale frequency components (Wavelet and Fourier transform layers) alongside a learnable semantic attention gate that dynamically weights atomic layers based on visual complexity.

> "True visual comprehension requires decomposing reality into orthogonal physical layers while simultaneously binding them into coherent semantic tokens."

---

## 2. Rigorous Implementation Specification

### 2.1 Multi-Scale Wavelet & Frequency Decomposition
The Atomizer must decompose input images into approximation and detail sub-bands using 2D discrete wavelet transforms (DWT), capturing high-frequency texture anomalies alongside low-frequency energy distributions.

* **Atomizer Extension (`atomizer.cpp`)**:
  ```cpp
  #include <vector>
  #include <cmath>

  namespace agivs {
      struct AtomicContext {
          std::vector<float> rgb_matrix;
          std::vector<float> energy_layer;
          std::vector<float> flow_layer;
          std::vector<float> wavelet_detail_h;
          std::vector<float> wavelet_detail_v;
          std::vector<float> wavelet_detail_d;
      };

      void decompose_atomic_multiscale(const float* img_rgb, int width, int height, AtomicContext& ctx) {
          // Allocation and multi-scale frequency filtering logic
          ctx.rgb_matrix.assign(img_rgb, img_rgb + width * height * 3);
          // Compute energy and flow layers with integrated wavelet sub-bands
      }
  }
  ```

### 2.2 Learnable Semantic Attention Gate
A lightweight gating network evaluates the spatial variance of the flow and energy layers to dynamically allocate attention weights between raw pixel tokens and frequency-domain atomic representations.

---

## 3. Pass/Fail Transition Test Harness

| Test Case ID | Test Description | Success Criteria | Pass/Fail Condition |
| :--- | :--- | :--- | :--- |
| **TC-2.1** | Lossless Reconstruction Fidelity | Decompose and reconstruct test images (city, dog, gradient) through the multi-scale atomizer-synthesizer pipeline. | **PASS**: Peak Signal-to-Noise Ratio (PSNR) $> 58.0\text{ dB}$.<br>**FAIL**: PSNR $< 58.0\text{ dB}$. |
| **TC-2.2** | Semantic Attention Weight Convergence | Train attention gate on standard benchmark dataset for 10 epochs; measure gradient stability. | **PASS**: Loss converges stably without exploding gradients.<br>**FAIL**: Gradient norm exceeds threshold $10.0$. |
| **TC-2.3** | Wavelet Sub-band Orthogonality | Verify orthogonality of extracted detail sub-bands ($H, V, D$). | **PASS**: Cross-correlation coefficient $< 10^{-4}$.<br>**FAIL**: Cross-correlation $\ge 10^{-4}$. |

---

## 4. Execution & Verification Command

```bash
cd build
./benchmark --stage 2 --verify-atomization --test-reconstruction
```
