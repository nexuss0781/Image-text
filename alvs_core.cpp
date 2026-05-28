#include "alvs_core.h"
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

namespace alvs {

std::vector<unsigned char> VisionLoader::loadImageFile(const std::string& file_path,
                                                        size_t& width, size_t& height, int& channels) {
    unsigned char* data = stbi_load(file_path.c_str(), 
                                     reinterpret_cast<int*>(&width),
                                     reinterpret_cast<int*>(&height),
                                     &channels, 3); // Force RGB
    
    if (!data) {
        throw std::runtime_error("Failed to load image: " + file_path);
    }
    
    size_t num_pixels = width * height;
    std::vector<unsigned char> result(data, data + num_pixels * 3);
    stbi_image_free(data);
    
    return result;
}

void VisionLoader::saveImageFile(const std::vector<unsigned char>& data, size_t width, size_t height,
                                  const std::string& output_path) {
    int success = stbi_write_png(output_path.c_str(), 
                                  static_cast<int>(width),
                                  static_cast<int>(height),
                                  3, data.data(), 
                                  static_cast<int>(width * 3));
    
    if (!success) {
        throw std::runtime_error("Failed to save image: " + output_path);
    }
}

std::vector<Pixel> VisionLoader::loadToMath(const std::string& file_path) {
    size_t width, height;
    int channels;
    
    auto raw_data = loadImageFile(file_path, width, height, channels);
    
    // Convert to normalized float pixels (0.0 - 1.0)
    std::vector<Pixel> matrix(width * height);
    const float norm_factor = 1.0f / 255.0f;
    
    for (size_t i = 0; i < width * height; ++i) {
        matrix[i].r = static_cast<float>(raw_data[i * 3]) * norm_factor;
        matrix[i].g = static_cast<float>(raw_data[i * 3 + 1]) * norm_factor;
        matrix[i].b = static_cast<float>(raw_data[i * 3 + 2]) * norm_factor;
    }
    
    return matrix;
}

void VisionLoader::saveFromMath(const std::vector<Pixel>& matrix, size_t width, size_t height,
                                 const std::string& output_path) {
    // Clip and quantize to uint8
    std::vector<unsigned char> data(width * height * 3);
    
    for (size_t i = 0; i < width * height; ++i) {
        float r = std::max(0.0f, std::min(1.0f, matrix[i].r));
        float g = std::max(0.0f, std::min(1.0f, matrix[i].g));
        float b = std::max(0.0f, std::min(1.0f, matrix[i].b));
        
        data[i * 3] = static_cast<unsigned char>(r * 255.0f + 0.5f);
        data[i * 3 + 1] = static_cast<unsigned char>(g * 255.0f + 0.5f);
        data[i * 3 + 2] = static_cast<unsigned char>(b * 255.0f + 0.5f);
    }
    
    saveImageFile(data, width, height, output_path);
}

AtomicContext Atomizer::atomize(const std::vector<Pixel>& color_matrix, size_t width, size_t height) {
    AtomicContext ctx;
    ctx.width = width;
    ctx.height = height;
    ctx.color = color_matrix;
    
    size_t num_pixels = width * height;
    ctx.energy.resize(num_pixels);
    ctx.flow_x.resize(num_pixels);
    ctx.flow_y.resize(num_pixels);
    
    // Compute energy (luminance) layer using Rec. 709
    for (size_t i = 0; i < num_pixels; ++i) {
        ctx.energy[i] = color_matrix[i].r * LUMA_R + 
                        color_matrix[i].g * LUMA_G + 
                        color_matrix[i].b * LUMA_B;
    }
    
    // Compute flow (gradient) layer using central differences
    // For boundary pixels, use forward/backward differences
    for (size_t y = 0; y < height; ++y) {
        for (size_t x = 0; x < width; ++x) {
            size_t idx = y * width + x;
            
            // Horizontal gradient (dx)
            float grad_x_r, grad_x_g, grad_x_b;
            
            if (x == 0) {
                // Forward difference
                size_t right_idx = idx + 1;
                grad_x_r = color_matrix[right_idx].r - color_matrix[idx].r;
                grad_x_g = color_matrix[right_idx].g - color_matrix[idx].g;
                grad_x_b = color_matrix[right_idx].b - color_matrix[idx].b;
            } else if (x == width - 1) {
                // Backward difference
                size_t left_idx = idx - 1;
                grad_x_r = color_matrix[idx].r - color_matrix[left_idx].r;
                grad_x_g = color_matrix[idx].g - color_matrix[left_idx].g;
                grad_x_b = color_matrix[idx].b - color_matrix[left_idx].b;
            } else {
                // Central difference
                size_t right_idx = idx + 1;
                size_t left_idx = idx - 1;
                grad_x_r = (color_matrix[right_idx].r - color_matrix[left_idx].r) * 0.5f;
                grad_x_g = (color_matrix[right_idx].g - color_matrix[left_idx].g) * 0.5f;
                grad_x_b = (color_matrix[right_idx].b - color_matrix[left_idx].b) * 0.5f;
            }
            
            // Vertical gradient (dy)
            float grad_y_r, grad_y_g, grad_y_b;
            
            if (y == 0) {
                // Forward difference
                size_t down_idx = (y + 1) * width + x;
                grad_y_r = color_matrix[down_idx].r - color_matrix[idx].r;
                grad_y_g = color_matrix[down_idx].g - color_matrix[idx].g;
                grad_y_b = color_matrix[down_idx].b - color_matrix[idx].b;
            } else if (y == height - 1) {
                // Backward difference
                size_t up_idx = (y - 1) * width + x;
                grad_y_r = color_matrix[idx].r - color_matrix[up_idx].r;
                grad_y_g = color_matrix[idx].g - color_matrix[up_idx].g;
                grad_y_b = color_matrix[idx].b - color_matrix[up_idx].b;
            } else {
                // Central difference
                size_t down_idx = (y + 1) * width + x;
                size_t up_idx = (y - 1) * width + x;
                grad_y_r = (color_matrix[down_idx].r - color_matrix[up_idx].r) * 0.5f;
                grad_y_g = (color_matrix[down_idx].g - color_matrix[up_idx].g) * 0.5f;
                grad_y_b = (color_matrix[down_idx].b - color_matrix[up_idx].b) * 0.5f;
            }
            
            // Average RGB gradients
            ctx.flow_x[idx] = (grad_x_r + grad_x_g + grad_x_b) / 3.0f;
            ctx.flow_y[idx] = (grad_y_r + grad_y_g + grad_y_b) / 3.0f;
        }
    }
    
    return ctx;
}

std::vector<float> Atomizer::getSmartAtom(const AtomicContext& ctx, size_t x, size_t y) {
    if (x >= ctx.width || y >= ctx.height) {
        return {};
    }
    
    size_t idx = y * ctx.width + x;
    std::vector<float> atom;
    atom.reserve(7); // x, y, r, g, b, energy, flow_x, flow_y
    
    atom.push_back(static_cast<float>(x));
    atom.push_back(static_cast<float>(y));
    atom.push_back(ctx.color[idx].r);
    atom.push_back(ctx.color[idx].g);
    atom.push_back(ctx.color[idx].b);
    atom.push_back(ctx.energy[idx]);
    atom.push_back(ctx.flow_x[idx]);
    atom.push_back(ctx.flow_y[idx]);
    
    return atom;
}

std::vector<Pixel> Synthesizer::reconstruct(const AtomicContext& ctx) {
    return ctx.color;
}

std::vector<Pixel> Synthesizer::smartRemix(const AtomicContext& ctx, const std::string& mode) {
    if (mode == "visualize_flow") {
        return visualizeFlow(ctx);
    } else if (mode == "quantum_inverse") {
        return quantumInverse(ctx);
    } else if (mode == "energy_boost") {
        return energyBoost(ctx);
    } else {
        return ctx.color;
    }
}

std::vector<Pixel> Synthesizer::visualizeFlow(const AtomicContext& ctx) {
    size_t num_pixels = ctx.width * ctx.height;
    std::vector<Pixel> result(num_pixels);
    
    for (size_t i = 0; i < num_pixels; ++i) {
        // Calculate flow magnitude
        float magnitude = std::sqrt(ctx.flow_x[i] * ctx.flow_x[i] + 
                                    ctx.flow_y[i] * ctx.flow_y[i]);
        
        // Normalize and boost for visibility
        float flow_visual = std::min(1.0f, magnitude * 5.0f);
        
        result[i].r = flow_visual;
        result[i].g = flow_visual;
        result[i].b = flow_visual;
    }
    
    return result;
}

std::vector<Pixel> Synthesizer::quantumInverse(const AtomicContext& ctx) {
    size_t num_pixels = ctx.width * ctx.height;
    std::vector<Pixel> result(num_pixels);
    
    for (size_t i = 0; i < num_pixels; ++i) {
        result[i].r = 1.0f - ctx.color[i].r;
        result[i].g = 1.0f - ctx.color[i].g;
        result[i].b = 1.0f - ctx.color[i].b;
    }
    
    return result;
}

std::vector<Pixel> Synthesizer::energyBoost(const AtomicContext& ctx) {
    size_t num_pixels = ctx.width * ctx.height;
    std::vector<Pixel> result(num_pixels);
    
    for (size_t i = 0; i < num_pixels; ++i) {
        // Only boost high-energy pixels (> 0.5)
        if (ctx.energy[i] > 0.5f) {
            result[i].r = std::min(1.0f, ctx.color[i].r + 0.2f);
            result[i].g = std::min(1.0f, ctx.color[i].g + 0.2f);
            result[i].b = std::min(1.0f, ctx.color[i].b + 0.2f);
        } else {
            result[i] = ctx.color[i];
        }
    }
    
    return result;
}

} // namespace alvs
