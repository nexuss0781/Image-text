"""
Production-ready Python interface for ALVS.

This module provides a unified interface that automatically uses the 
high-performance C++ backend when available, with fallback to pure Python.
"""

import numpy as np
from typing import Dict, Optional, Tuple, Any
import os

# Try to import the high-performance C++ backend
try:
    import alvs_cpp
    _HAS_CPP_BACKEND = True
except ImportError:
    _HAS_CPP_BACKEND = False
    alvs_cpp = None


class VisionLoader:
    """
    The Intelligent Eye (Module A).
    
    Production-ready image loader with automatic C++ acceleration.
    """
    
    def __init__(self, use_cpp: bool = True):
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
        self.use_cpp = use_cpp and _HAS_CPP_BACKEND
        
        if self.use_cpp:
            self._backend = alvs_cpp.VisionLoader()
        else:
            from PIL import Image
            self._pil = Image
    
    def load_to_math(self, file_path: str) -> Dict[str, Any]:
        """
        Load image and convert to normalized mathematical matrix.
        
        Args:
            file_path: Path to input image
            
        Returns:
            Dictionary containing:
                - 'matrix': Normalized numpy array (0.0-1.0)
                - 'shape': Image dimensions
                - 'original_format': Source file type
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image not found: {file_path}")
        
        # Use PIL for loading (most reliable cross-platform)
        from PIL import Image
        with Image.open(file_path) as img:
            img = img.convert('RGB')
            raw_data = np.asarray(img)
            math_matrix = raw_data.astype(np.float32) / 255.0
            
            return {
                "matrix": math_matrix,
                "shape": math_matrix.shape,
                "original_format": img.format
            }
    
    def save_from_math(self, matrix: np.ndarray, output_path: str) -> None:
        """
        Save mathematical matrix back to image file.
        
        Args:
            matrix: Float matrix (0.0-1.0)
            output_path: Output file path
        """
        # Use PIL for saving (most reliable)
        from PIL import Image
        matrix = np.clip(matrix, 0.0, 1.0)
        visual_data = (matrix * 255.0).astype(np.uint8)
        img = Image.fromarray(visual_data)
        img.save(output_path)


class Atomizer:
    """
    The Logic Converter (Module B).
    
    High-performance atomizer with C++ acceleration.
    """
    
    def __init__(self, use_cpp: bool = True):
        self.use_cpp = use_cpp and _HAS_CPP_BACKEND
        
        if self.use_cpp:
            self._backend = alvs_cpp.Atomizer()
    
    def atomize(self, math_matrix: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Convert raw color matrix to atomic context.
        
        Args:
            math_matrix: Input RGB matrix (0.0-1.0)
            
        Returns:
            Dictionary containing color, energy, flow_x, flow_y layers
        """
        if self.use_cpp:
            # Use optimized C++ backend with numpy arrays
            energy, flow_x, flow_y = self._backend.atomize_numpy(math_matrix.astype(np.float32))
            
            return {
                "color": math_matrix.astype(np.float32),
                "energy": energy,
                "flow_x": flow_x,
                "flow_y": flow_y
            }
        else:
            # Pure Python implementation (existing code)
            color_layer = math_matrix
            energy_layer = np.dot(color_layer[..., :3], [0.2126, 0.7152, 0.0722])
            grad_y, grad_x, _ = np.gradient(color_layer)
            flow_x = np.mean(grad_x, axis=2)
            flow_y = np.mean(grad_y, axis=2)
            
            return {
                "color": color_layer,
                "energy": energy_layer,
                "flow_x": flow_x,
                "flow_y": flow_y
            }
    
    def get_smart_atom(self, atomic_context: Dict, x: int, y: int) -> Optional[Dict]:
        """Get smart atom at specific coordinate."""
        try:
            if self.use_cpp and 'color' in atomic_context:
                # Build context for C++
                height, width = atomic_context['color'].shape[:2]
                pixels = []
                for yy in range(height):
                    for xx in range(width):
                        pixels.append(alvs_cpp.Pixel(
                            float(atomic_context['color'][yy, xx, 0]),
                            float(atomic_context['color'][yy, xx, 1]),
                            float(atomic_context['color'][yy, xx, 2])
                        ))
                
                ctx = alvs_cpp.AtomicContext()
                ctx.color = pixels
                ctx.width = width
                ctx.height = height
                ctx.energy = atomic_context['energy'].flatten().tolist()
                ctx.flow_x = atomic_context['flow_x'].flatten().tolist()
                ctx.flow_y = atomic_context['flow_y'].flatten().tolist()
                
                atom_data = self._backend.get_smart_atom(ctx, x, y)
                if atom_data:
                    return {
                        "coordinate": (x, y),
                        "vector_rgb": [atom_data[2], atom_data[3], atom_data[4]],
                        "energy_val": atom_data[5],
                        "logic_flow": [atom_data[6], atom_data[7]]
                    }
            
            # Fallback
            return {
                "coordinate": (x, y),
                "vector_rgb": atomic_context["color"][y, x].tolist(),
                "energy_val": float(atomic_context["energy"][y, x]),
                "logic_flow": [
                    float(atomic_context["flow_x"][y, x]),
                    float(atomic_context["flow_y"][y, x])
                ]
            }
        except (IndexError, KeyError):
            return None


class Synthesizer:
    """
    The Reality Builder (Module C).
    
    High-performance synthesizer with C++ acceleration.
    """
    
    def __init__(self, use_cpp: bool = True):
        self.use_cpp = use_cpp and _HAS_CPP_BACKEND
        
        if self.use_cpp:
            self._backend = alvs_cpp.Synthesizer()
    
    def reconstruct(self, atomic_context: Dict) -> np.ndarray:
        """Reconstruct original image from atomic context."""
        return atomic_context["color"].copy()
    
    def smart_remix(self, atomic_context: Dict, mode: str = "edge_glow") -> np.ndarray:
        """
        Apply logic-based transformations.
        
        Args:
            atomic_context: Data from Atomizer
            mode: Transformation mode
            
        Returns:
            Transformed image matrix
        """
        if self.use_cpp:
            # Use optimized C++ backend with numpy arrays
            color = atomic_context['color'].astype(np.float32)
            energy = atomic_context['energy'].astype(np.float32)
            flow_x = atomic_context['flow_x'].astype(np.float32)
            flow_y = atomic_context['flow_y'].astype(np.float32)
            
            result = self._backend.smart_remix_numpy(color, energy, flow_x, flow_y, mode)
            return result
        else:
            # Pure Python implementation
            color = atomic_context["color"].copy()
            energy = atomic_context["energy"]
            flow_x = atomic_context["flow_x"]
            flow_y = atomic_context["flow_y"]
            
            if mode == "visualize_flow":
                flow_magnitude = np.sqrt(flow_x**2 + flow_y**2)
                flow_visual = np.clip(flow_magnitude * 5.0, 0.0, 1.0)
                return np.dstack((flow_visual, flow_visual, flow_visual))
            
            elif mode == "quantum_inverse":
                return 1.0 - color
            
            elif mode == "energy_boost":
                boost_mask = (energy > 0.5).astype(np.float64)
                boost_mask = np.dstack((boost_mask, boost_mask, boost_mask))
                return color + (boost_mask * 0.2)
            
            else:
                return color


def get_backend_info() -> Dict[str, Any]:
    """Get information about the current backend configuration."""
    return {
        "has_cpp_backend": _HAS_CPP_BACKEND,
        "backend_type": "C++ (pybind11)" if _HAS_CPP_BACKEND else "Pure Python",
        "numpy_version": np.__version__
    }
