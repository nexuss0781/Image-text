#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "alvs_core.h"

namespace py = pybind11;

PYBIND11_MODULE(alvs_cpp, m) {
    m.doc() = "High-performance C++ backend for Atomic Logic Vision System";
    
    // Pixel struct
    py::class_<alvs::Pixel>(m, "Pixel")
        .def(py::init<>())
        .def(py::init<float, float, float>())
        .def_readwrite("r", &alvs::Pixel::r)
        .def_readwrite("g", &alvs::Pixel::g)
        .def_readwrite("b", &alvs::Pixel::b);
    
    // AtomicContext struct
    py::class_<alvs::AtomicContext>(m, "AtomicContext")
        .def(py::init<>())
        .def_readwrite("color", &alvs::AtomicContext::color)
        .def_readwrite("energy", &alvs::AtomicContext::energy)
        .def_readwrite("flow_x", &alvs::AtomicContext::flow_x)
        .def_readwrite("flow_y", &alvs::AtomicContext::flow_y)
        .def_readwrite("width", &alvs::AtomicContext::width)
        .def_readwrite("height", &alvs::AtomicContext::height);
    
    // VisionLoader class - use PIL in Python, just provide save
    py::class_<alvs::VisionLoader>(m, "VisionLoader")
        .def(py::init<>());
    
    // Atomizer class - optimized numpy version
    py::class_<alvs::Atomizer>(m, "Atomizer")
        .def(py::init<>())
        .def("atomize_numpy", [](alvs::Atomizer& self, py::array_t<float> color_array) {
            auto buf = color_array.request();
            if (buf.ndim != 3 || buf.shape[2] != 3) {
                throw std::runtime_error("Input must be HxWx3 array");
            }
            
            size_t height = buf.shape[0];
            size_t width = buf.shape[1];
            float* ptr = static_cast<float*>(buf.ptr);
            
            // Convert to vector of Pixel
            std::vector<alvs::Pixel> pixels(height * width);
            for (size_t i = 0; i < height * width; ++i) {
                pixels[i].r = ptr[i * 3];
                pixels[i].g = ptr[i * 3 + 1];
                pixels[i].b = ptr[i * 3 + 2];
            }
            
            // Process
            auto ctx = self.atomize(pixels, width, height);
            
            // Convert back to numpy arrays
            auto energy_arr = py::array_t<float>({height, width});
            auto flow_x_arr = py::array_t<float>({height, width});
            auto flow_y_arr = py::array_t<float>({height, width});
            
            auto e_ptr = static_cast<float*>(energy_arr.request().ptr);
            auto fx_ptr = static_cast<float*>(flow_x_arr.request().ptr);
            auto fy_ptr = static_cast<float*>(flow_y_arr.request().ptr);
            
            for (size_t i = 0; i < height * width; ++i) {
                e_ptr[i] = ctx.energy[i];
                fx_ptr[i] = ctx.flow_x[i];
                fy_ptr[i] = ctx.flow_y[i];
            }
            
            return py::make_tuple(energy_arr, flow_x_arr, flow_y_arr);
        }, "Atomize numpy array, returns (energy, flow_x, flow_y)");
    
    // Synthesizer class - optimized numpy version
    py::class_<alvs::Synthesizer>(m, "Synthesizer")
        .def(py::init<>())
        .def("smart_remix_numpy", [](alvs::Synthesizer& self, 
                                      py::array_t<float> color_array,
                                      py::array_t<float> energy_array,
                                      py::array_t<float> flow_x_array,
                                      py::array_t<float> flow_y_array,
                                      const std::string& mode) {
            auto cbuf = color_array.request();
            auto ebuf = energy_array.request();
            auto fxbuf = flow_x_array.request();
            auto fybuf = flow_y_array.request();
            
            size_t height = cbuf.shape[0];
            size_t width = cbuf.shape[1];
            float* cptr = static_cast<float*>(cbuf.ptr);
            float* eptr = static_cast<float*>(ebuf.ptr);
            float* fxptr = static_cast<float*>(fxbuf.ptr);
            float* fyptr = static_cast<float*>(fybuf.ptr);
            
            // Build context
            alvs::AtomicContext ctx;
            ctx.width = width;
            ctx.height = height;
            ctx.color.resize(height * width);
            ctx.energy.resize(height * width);
            ctx.flow_x.resize(height * width);
            ctx.flow_y.resize(height * width);
            
            for (size_t i = 0; i < height * width; ++i) {
                ctx.color[i].r = cptr[i * 3];
                ctx.color[i].g = cptr[i * 3 + 1];
                ctx.color[i].b = cptr[i * 3 + 2];
                ctx.energy[i] = eptr[i];
                ctx.flow_x[i] = fxptr[i];
                ctx.flow_y[i] = fyptr[i];
            }
            
            // Process
            auto result = self.smartRemix(ctx, mode);
            
            // Convert back to numpy
            std::vector<ssize_t> shape = {static_cast<ssize_t>(height), static_cast<ssize_t>(width), 3};
            auto result_arr = py::array_t<float>(shape);
            auto rptr = static_cast<float*>(result_arr.request().ptr);
            
            for (size_t i = 0; i < height * width; ++i) {
                rptr[i * 3] = result[i].r;
                rptr[i * 3 + 1] = result[i].g;
                rptr[i * 3 + 2] = result[i].b;
            }
            
            return result_arr;
        }, "Apply smart remix to numpy arrays");
}
