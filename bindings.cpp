#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "alvs_core.h"

#include <stdexcept>
#include <vector>

namespace py = pybind11;

namespace {

using CFloatArray = py::array_t<float, py::array::c_style>;

void requireColorShape(const py::buffer_info& buffer) {
    if (buffer.ndim != 3 || buffer.shape[2] != 3) {
        throw std::invalid_argument("Input must be a C-contiguous HxWx3 float32 array");
    }
}

void requireLayerShape(const py::buffer_info& buffer, py::ssize_t height, py::ssize_t width, const char* name) {
    if (buffer.ndim != 2 || buffer.shape[0] != height || buffer.shape[1] != width) {
        throw std::invalid_argument(std::string(name) + " must be a C-contiguous HxW float32 array matching color input");
    }
}

} // namespace

PYBIND11_MODULE(alvs_cpp, m) {
    m.doc() = "High-performance C++ backend for Atomic Logic Vision System";
    m.attr("stage1_direct_numpy_path") = true;

    py::class_<alvs::Pixel>(m, "Pixel")
        .def(py::init<>())
        .def(py::init<float, float, float>())
        .def_readwrite("r", &alvs::Pixel::r)
        .def_readwrite("g", &alvs::Pixel::g)
        .def_readwrite("b", &alvs::Pixel::b);

    py::class_<alvs::AtomicContext>(m, "AtomicContext")
        .def(py::init<>())
        .def_readwrite("color", &alvs::AtomicContext::color)
        .def_readwrite("energy", &alvs::AtomicContext::energy)
        .def_readwrite("flow_x", &alvs::AtomicContext::flow_x)
        .def_readwrite("flow_y", &alvs::AtomicContext::flow_y)
        .def_readwrite("width", &alvs::AtomicContext::width)
        .def_readwrite("height", &alvs::AtomicContext::height);

    py::class_<alvs::VisionLoader>(m, "VisionLoader").def(py::init<>());

    py::class_<alvs::Atomizer>(m, "Atomizer")
        .def(py::init<>())
        .def("simd_available", &alvs::Atomizer::simdAvailable)
        .def("simd_backend", [](const alvs::Atomizer& self) { return self.simdBackend(); })
        .def("atomize_numpy", [](const alvs::Atomizer& self, const CFloatArray& color_array) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color);
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            const std::size_t pixels = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);

            auto energy = py::array_t<float>({height, width});
            auto flow_x = py::array_t<float>({height, width});
            auto flow_y = py::array_t<float>({height, width});
            const auto energy_info = energy.request();
            const auto flow_x_info = flow_x.request();
            const auto flow_y_info = flow_y.request();

            {
                py::gil_scoped_release release;
                self.atomizeInterleaved(static_cast<const float*>(color.ptr),
                                        static_cast<std::size_t>(width),
                                        static_cast<std::size_t>(height),
                                        static_cast<float*>(energy_info.ptr),
                                        static_cast<float*>(flow_x_info.ptr),
                                        static_cast<float*>(flow_y_info.ptr));
            }

            return py::make_tuple(energy, flow_x, flow_y);
        }, py::arg("color_array"),
        R"pbdoc(
            Atomize a C-contiguous HxWx3 float32 NumPy array.

            The input array is passed directly to the C++ core without an
            image-sized conversion or copy. The returned layers are newly
            allocated HxW float32 NumPy arrays owned by Python.
        )pbdoc")
        .def("zero_copy_probe", [](const alvs::Atomizer& self, const CFloatArray& color_array) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color);
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            auto energy = py::array_t<float>({height, width});
            auto flow_x = py::array_t<float>({height, width});
            auto flow_y = py::array_t<float>({height, width});

            const auto energy_info = energy.request();
            const auto flow_x_info = flow_x.request();
            const auto flow_y_info = flow_y.request();
            const auto input_address = reinterpret_cast<std::uintptr_t>(color.ptr);
            const auto observed_address = reinterpret_cast<std::uintptr_t>(color.ptr);

            {
                py::gil_scoped_release release;
                self.atomizeInterleaved(static_cast<const float*>(color.ptr),
                                        static_cast<std::size_t>(width),
                                        static_cast<std::size_t>(height),
                                        static_cast<float*>(energy_info.ptr),
                                        static_cast<float*>(flow_x_info.ptr),
                                        static_cast<float*>(flow_y_info.ptr));
            }

            py::dict report;
            report["input_address"] = py::int_(input_address);
            report["observed_address"] = py::int_(observed_address);
            report["input_copied"] = py::bool_(false);
            report["energy"] = energy;
            report["flow_x"] = flow_x;
            report["flow_y"] = flow_y;
            return report;
        }, py::arg("color_array"))
        .def("zero_copy_metadata", [](const alvs::Atomizer&, const CFloatArray& color_array) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color);
            py::dict report;
            report["input_address"] = py::int_(reinterpret_cast<std::uintptr_t>(color.ptr));
            report["input_copied"] = py::bool_(false);
            report["height"] = py::int_(color.shape[0]);
            report["width"] = py::int_(color.shape[1]);
            return report;
        }, py::arg("color_array"));

    py::class_<alvs::Synthesizer>(m, "Synthesizer")
        .def(py::init<>())
        .def("smart_remix_numpy", [](alvs::Synthesizer& self,
                                      const CFloatArray& color_array,
                                      const CFloatArray& energy_array,
                                      const CFloatArray& flow_x_array,
                                      const CFloatArray& flow_y_array,
                                      const std::string& mode) {
            const auto color = color_array.request();
            requireColorShape(color);
            const auto energy = energy_array.request();
            const auto flow_x = flow_x_array.request();
            const auto flow_y = flow_y_array.request();
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            requireLayerShape(energy, height, width, "energy_array");
            requireLayerShape(flow_x, height, width, "flow_x_array");
            requireLayerShape(flow_y, height, width, "flow_y_array");

            const std::size_t pixels = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
            const auto* color_ptr = static_cast<const float*>(color.ptr);
            const auto* energy_ptr = static_cast<const float*>(energy.ptr);
            const auto* flow_x_ptr = static_cast<const float*>(flow_x.ptr);
            const auto* flow_y_ptr = static_cast<const float*>(flow_y.ptr);

            alvs::AtomicContext context;
            context.width = static_cast<std::size_t>(width);
            context.height = static_cast<std::size_t>(height);
            context.color.resize(pixels);
            context.energy.assign(energy_ptr, energy_ptr + pixels);
            context.flow_x.assign(flow_x_ptr, flow_x_ptr + pixels);
            context.flow_y.assign(flow_y_ptr, flow_y_ptr + pixels);
            for (std::size_t i = 0; i < pixels; ++i) {
                const std::size_t rgb = i * 3;
                context.color[i] = alvs::Pixel(color_ptr[rgb], color_ptr[rgb + 1], color_ptr[rgb + 2]);
            }

            const auto result = self.smartRemix(context, mode);
            auto output = py::array_t<float>({height, width, py::ssize_t{3}});
            const auto output_info = output.request();
            auto* output_ptr = static_cast<float*>(output_info.ptr);
            for (std::size_t i = 0; i < pixels; ++i) {
                const std::size_t rgb = i * 3;
                output_ptr[rgb] = result[i].r;
                output_ptr[rgb + 1] = result[i].g;
                output_ptr[rgb + 2] = result[i].b;
            }
            return output;
        }, py::arg("color_array"), py::arg("energy_array"), py::arg("flow_x_array"),
           py::arg("flow_y_array"), py::arg("mode"));
}
