#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "alvs_core.h"

#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;

namespace {

void requireFloat32CArray(const py::array& array, const char* name) {
    if (!array.dtype().is(py::dtype::of<float>())) {
        throw std::invalid_argument(std::string(name) + " must have dtype float32");
    }
    if ((array.flags() & py::array::c_style) == 0) {
        throw std::invalid_argument(std::string(name) + " must be C-contiguous; implicit copies are prohibited");
    }
}

void requireColorShape(const py::array& array, const py::buffer_info& buffer) {
    requireFloat32CArray(array, "color_array");
    if (buffer.ndim != 3 || buffer.shape[2] != 3) {
        throw std::invalid_argument("color_array must be a C-contiguous HxWx3 float32 array");
    }
}

void requireLayerShape(const py::array& array,
                       const py::buffer_info& buffer,
                       py::ssize_t height,
                       py::ssize_t width,
                       const char* name) {
    requireFloat32CArray(array, name);
    if (buffer.ndim != 2 || buffer.shape[0] != height || buffer.shape[1] != width) {
        throw std::invalid_argument(std::string(name) + " must be a C-contiguous HxW float32 array matching color input");
    }
}

} // namespace

PYBIND11_MODULE(alvs_cpp, m) {
    m.doc() = "High-performance C++ backend for Atomic Logic Vision System";
    m.attr("stage1_direct_numpy_path") = true;
    m.attr("implicit_input_copies_prohibited") = true;

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
        .def("atomize_numpy", [](const alvs::Atomizer& self, const py::array& color_array) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color_array, color);
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];

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

            The input array is passed directly to the C++ core without image-
            sized conversion or copying. Non-float32 or non-contiguous arrays
            are rejected rather than silently copied.
        )pbdoc")
        .def("atomize_accelerated_numpy", [](const alvs::Atomizer& self, const py::array& color_array) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color_array, color);
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            auto energy = py::array_t<float>({height, width});
            auto flow_x = py::array_t<float>({height, width});
            auto flow_y = py::array_t<float>({height, width});
            const auto energy_info = energy.request();
            const auto flow_x_info = flow_x.request();
            const auto flow_y_info = flow_y.request();
            alvs::ExecutionReport report;
            {
                py::gil_scoped_release release;
                self.atomizeAcceleratedInterleaved(static_cast<const float*>(color.ptr),
                                                   static_cast<std::size_t>(width),
                                                   static_cast<std::size_t>(height),
                                                   static_cast<float*>(energy_info.ptr),
                                                   static_cast<float*>(flow_x_info.ptr),
                                                   static_cast<float*>(flow_y_info.ptr), report);
            }
            py::dict result;
            result["energy"] = energy;
            result["flow_x"] = flow_x;
            result["flow_y"] = flow_y;
            result["backend"] = report.backend;
            result["worker_threads"] = report.worker_threads;
            result["simd_enabled"] = report.simd_enabled;
            result["parallel_enabled"] = report.parallel_enabled;
            result["gpu_available"] = report.gpu_available;
            return result;
        }, py::arg("color_array"),
        R"pbdoc(
            Run the Stage 3 hardware-aware dispatch path over a C-contiguous
            HxWx3 float32 tensor. The returned backend metadata identifies
            CPU parallel, CPU reference, or future GPU execution explicitly.
        )pbdoc")
        .def("atomize_multiscale_numpy", [](const alvs::Atomizer& self,
                                             const py::array& color_array,
                                             std::size_t max_levels) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color_array, color);
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            auto energy = py::array_t<float>({height, width});
            auto flow_x = py::array_t<float>({height, width});
            auto flow_y = py::array_t<float>({height, width});
            const auto energy_info = energy.request();
            const auto flow_x_info = flow_x.request();
            const auto flow_y_info = flow_y.request();
            alvs::HaarWaveletPyramid pyramid;
            alvs::SemanticGateFeatures features;
            alvs::SemanticGateOutput gate;
            {
                py::gil_scoped_release release;
                self.atomizeMultiScaleInterleaved(static_cast<const float*>(color.ptr),
                                                   static_cast<std::size_t>(width),
                                                   static_cast<std::size_t>(height),
                                                   static_cast<float*>(energy_info.ptr),
                                                   static_cast<float*>(flow_x_info.ptr),
                                                   static_cast<float*>(flow_y_info.ptr),
                                                   pyramid, features, gate, max_levels);
            }

            auto copyBand = [](const std::vector<float>& values, std::size_t height, std::size_t width) {
                auto array = py::array_t<float>({static_cast<py::ssize_t>(height), static_cast<py::ssize_t>(width)});
                auto* destination = static_cast<float*>(array.request().ptr);
                std::copy(values.begin(), values.end(), destination);
                return array;
            };
            py::list levels;
            for (const alvs::WaveletLevel& level : pyramid.levels) {
                py::dict item;
                item["input_shape"] = py::make_tuple(level.input_height, level.input_width);
                item["approximation"] = copyBand(level.approximation, level.output_height, level.output_width);
                item["detail_horizontal"] = copyBand(level.detail_horizontal, level.output_height, level.output_width);
                item["detail_vertical"] = copyBand(level.detail_vertical, level.output_height, level.output_width);
                item["detail_diagonal"] = copyBand(level.detail_diagonal, level.output_height, level.output_width);
                levels.append(std::move(item));
            }
            auto feature_array = py::array_t<float>(std::vector<py::ssize_t>{4});
            auto weight_array = py::array_t<float>(std::vector<py::ssize_t>{6});
            std::copy(features.values.begin(), features.values.end(), static_cast<float*>(feature_array.request().ptr));
            std::copy(gate.weights.begin(), gate.weights.end(), static_cast<float*>(weight_array.request().ptr));
            py::dict result;
            result["energy"] = energy;
            result["flow_x"] = flow_x;
            result["flow_y"] = flow_y;
            result["wavelet_levels"] = levels;
            result["gate_features"] = feature_array;
            result["gate_weights"] = weight_array;
            result["complexity"] = gate.complexity;
            result["entropy"] = gate.entropy;
            return result;
        }, py::arg("color_array"), py::arg("max_levels") = 2,
        R"pbdoc(
            Perform direct Stage 2 atomization on a C-contiguous HxWx3
            float32 NumPy tensor, returning base layers, a Haar pyramid, and
            deterministic semantic gate metadata without copying the RGB input.
        )pbdoc")
        .def("project_multimodal_numpy", [](const alvs::Atomizer& self,
                                             const py::array& color_array,
                                             std::size_t max_levels,
                                             std::size_t patch_size,
                                             float retention_ratio,
                                             std::size_t max_tokens,
                                             std::size_t embedding_dimension) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color_array, color);
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            auto energy = py::array_t<float>({height, width});
            auto flow_x = py::array_t<float>({height, width});
            auto flow_y = py::array_t<float>({height, width});
            const auto energy_info = energy.request();
            const auto flow_x_info = flow_x.request();
            const auto flow_y_info = flow_y.request();
            alvs::HaarWaveletPyramid pyramid;
            alvs::SemanticGateFeatures features;
            alvs::SemanticGateOutput gate;
            alvs::VisualTokenProjection projection;
            alvs::ProjectionConfig config;
            config.patch_size = patch_size;
            config.retention_ratio = retention_ratio;
            config.max_tokens = max_tokens;
            config.embedding_dimension = embedding_dimension;
            {
                py::gil_scoped_release release;
                self.atomizeMultiScaleInterleaved(static_cast<const float*>(color.ptr),
                                                   static_cast<std::size_t>(width),
                                                   static_cast<std::size_t>(height),
                                                   static_cast<float*>(energy_info.ptr),
                                                   static_cast<float*>(flow_x_info.ptr),
                                                   static_cast<float*>(flow_y_info.ptr),
                                                   pyramid, features, gate, max_levels);
                alvs::VisualTokenProjector projector;
                projection = projector.project(static_cast<const float*>(energy_info.ptr),
                                               static_cast<const float*>(flow_x_info.ptr),
                                               static_cast<const float*>(flow_y_info.ptr),
                                               static_cast<std::size_t>(width),
                                               static_cast<std::size_t>(height),
                                               pyramid, gate, config);
            }
            auto embeddings = py::array_t<float>({static_cast<py::ssize_t>(projection.retained_token_count),
                                                   static_cast<py::ssize_t>(projection.embedding_dimension)});
            std::copy(projection.embeddings.begin(), projection.embeddings.end(),
                      static_cast<float*>(embeddings.request().ptr));
            auto patch_y = py::array_t<std::size_t>(std::vector<py::ssize_t>{static_cast<py::ssize_t>(projection.retained_token_count)});
            auto patch_x = py::array_t<std::size_t>(std::vector<py::ssize_t>{static_cast<py::ssize_t>(projection.retained_token_count)});
            auto importance = py::array_t<float>(std::vector<py::ssize_t>{static_cast<py::ssize_t>(projection.retained_token_count)});
            std::copy(projection.patch_y.begin(), projection.patch_y.end(), static_cast<std::size_t*>(patch_y.request().ptr));
            std::copy(projection.patch_x.begin(), projection.patch_x.end(), static_cast<std::size_t*>(patch_x.request().ptr));
            std::copy(projection.importance.begin(), projection.importance.end(), static_cast<float*>(importance.request().ptr));
            py::dict result;
            result["embeddings"] = embeddings;
            result["patch_y"] = patch_y;
            result["patch_x"] = patch_x;
            result["importance"] = importance;
            result["source_patch_count"] = projection.source_patch_count;
            result["retained_token_count"] = projection.retained_token_count;
            result["embedding_dimension"] = projection.embedding_dimension;
            result["input_address"] = py::int_(reinterpret_cast<std::uintptr_t>(color.ptr));
            result["input_copied"] = py::bool_(false);
            return result;
        }, py::arg("color_array"), py::arg("max_levels") = 2, py::arg("patch_size") = 4,
           py::arg("retention_ratio") = 0.25f, py::arg("max_tokens") = 0,
           py::arg("embedding_dimension") = 4096,
        R"pbdoc(
            Convert a direct HxWx3 float32 vision tensor into deterministic,
            RMS-normalized visual-token embeddings with adaptive token pruning.
            This function does not claim alignment with a pretrained VLM.
        )pbdoc")
        .def("zero_copy_probe", [](const alvs::Atomizer& self, const py::array& color_array) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color_array, color);
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            auto energy = py::array_t<float>({height, width});
            auto flow_x = py::array_t<float>({height, width});
            auto flow_y = py::array_t<float>({height, width});

            const auto energy_info = energy.request();
            const auto flow_x_info = flow_x.request();
            const auto flow_y_info = flow_y.request();
            const auto input_address = reinterpret_cast<std::uintptr_t>(color.ptr);

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
            report["observed_address"] = py::int_(input_address);
            report["input_copied"] = py::bool_(false);
            report["energy"] = energy;
            report["flow_x"] = flow_x;
            report["flow_y"] = flow_y;
            return report;
        }, py::arg("color_array"))
        .def("zero_copy_metadata", [](const alvs::Atomizer&, const py::array& color_array) {
            const py::buffer_info color = color_array.request();
            requireColorShape(color_array, color);
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
                                      const py::array& color_array,
                                      const py::array& energy_array,
                                      const py::array& flow_x_array,
                                      const py::array& flow_y_array,
                                      const std::string& mode) {
            const auto color = color_array.request();
            requireColorShape(color_array, color);
            const auto energy = energy_array.request();
            const auto flow_x = flow_x_array.request();
            const auto flow_y = flow_y_array.request();
            const py::ssize_t height = color.shape[0];
            const py::ssize_t width = color.shape[1];
            requireLayerShape(energy_array, energy, height, width, "energy_array");
            requireLayerShape(flow_x_array, flow_x, height, width, "flow_x_array");
            requireLayerShape(flow_y_array, flow_y, height, width, "flow_y_array");

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
