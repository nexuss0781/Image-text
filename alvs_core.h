#ifndef ALVS_CORE_H
#define ALVS_CORE_H

#include <vector>
#include <string>
#include <stdexcept>
#include <cmath>
#include <algorithm>
#include <array>

namespace alvs {

// High-performance pixel structure
struct Pixel {
    float r, g, b;
    
    Pixel() : r(0), g(0), b(0) {}
    Pixel(float red, float green, float blue) : r(red), g(green), b(blue) {}
};

// Atomic context holding all computed layers
struct AtomicContext {
    std::vector<Pixel> color;           // RGB color layer
    std::vector<float> energy;          // Luminance/energy layer
    std::vector<float> flow_x;          // Horizontal gradient
    std::vector<float> flow_y;          // Vertical gradient
    size_t width;
    size_t height;
    
    AtomicContext() : width(0), height(0) {}
};

class VisionLoader {
public:
    VisionLoader() = default;
    
    // Load image from file path, returns normalized matrix (0.0-1.0)
    std::vector<Pixel> loadToMath(const std::string& file_path);
    
    // Save matrix to file
    void saveFromMath(const std::vector<Pixel>& matrix, size_t width, size_t height, 
                      const std::string& output_path);
    
private:
    std::vector<unsigned char> loadImageFile(const std::string& file_path, 
                                              size_t& width, size_t& height, int& channels);
    void saveImageFile(const std::vector<unsigned char>& data, size_t width, size_t height,
                       const std::string& output_path);
};

class Atomizer {
public:
    Atomizer() = default;
    
    // Convert raw color matrix to atomic context with energy and flow layers
    AtomicContext atomize(const std::vector<Pixel>& color_matrix, size_t width, size_t height);
    
    // Get smart atom at specific coordinate
    std::vector<float> getSmartAtom(const AtomicContext& ctx, size_t x, size_t y);
    
private:
    // Rec. 709 luminance coefficients
    static constexpr float LUMA_R = 0.2126f;
    static constexpr float LUMA_G = 0.7152f;
    static constexpr float LUMA_B = 0.0722f;
};

class Synthesizer {
public:
    Synthesizer() = default;
    
    // Reconstruct original color from atomic context
    std::vector<Pixel> reconstruct(const AtomicContext& ctx);
    
    // Apply smart remix transformations
    std::vector<Pixel> smartRemix(const AtomicContext& ctx, const std::string& mode);
    
private:
    std::vector<Pixel> visualizeFlow(const AtomicContext& ctx);
    std::vector<Pixel> quantumInverse(const AtomicContext& ctx);
    std::vector<Pixel> energyBoost(const AtomicContext& ctx);
};

} // namespace alvs

#endif // ALVS_CORE_H
