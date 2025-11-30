import numpy as np
from PIL import Image
import os

class VisionLoader:
    """
    The Intelligent Eye (Module A).
    
    Responsibilities:
    1. Ingest raw visual data from user formats (.jpg, .png).
    2. Convert 'Visual Data' (Integers) into 'Mathematical Data' (High-precision Floats).
    3. Handle the reconstruction of math back into visual formats.
    """

    def __init__(self):
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

    def load_to_math(self, file_path):
        """
        Loads an image and converts it into a Normalized Mathematical Matrix.
        
        Args:
            file_path (str): Path to the input image.
            
        Returns:
            dict: A 'Smart Context' containing:
                - 'matrix': The 3D numpy array of floats (0.0 to 1.0).
                - 'shape': Dimensions (height, width, channels).
                - 'original_format': The source file type.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"System cannot find visual input at: {file_path}")

        try:
            # Open image using standard lib
            with Image.open(file_path) as img:
                
                # SMART LOGIC 1: Standardization
                # We force convert to RGB. If we feed Grayscale or CMYK to the logic engine,
                # the math will break. We standardize the universe here.
                img = img.convert('RGB')
                
                # SMART LOGIC 2: Vectorization
                # Convert the image object into a raw number array
                raw_data = np.asarray(img)

                # SMART LOGIC 3: Normalization (The most important step)
                # Computers struggle with integers (0-255) for complex logic like gradients.
                # We convert to Float64 (0.00000 to 1.00000).
                # This allows for infinite precision in color logic.
                math_matrix = raw_data.astype(np.float64) / 255.0

                print(f"[VisionLoader] Successfully atomized {file_path}")
                print(f"               Dimensions: {math_matrix.shape}")
                print(f"               Precision: 64-bit Floating Point")

                return {
                    "matrix": math_matrix,
                    "shape": math_matrix.shape,
                    "original_format": img.format
                }

        except Exception as e:
            raise RuntimeError(f"VisionLoader failed to process image: {e}")

    def save_from_math(self, matrix, output_path):
        """
        Converts Mathematical Logic back into a Real Image.
        
        Args:
            matrix (numpy array): The modified/generated float matrix.
            output_path (str): Where to save the result.
        """
        try:
            # SMART LOGIC 4: Safety Clipping
            # If the logic engine generated a color value of 1.5 (super bright),
            # standard screens can't show it. We clip it to 1.0 logically.
            matrix = np.clip(matrix, 0.0, 1.0)

            # SMART LOGIC 5: Quantization
            # Convert the continuous math (0.0-1.0) back to discrete bytes (0-255).
            visual_data = (matrix * 255.0).astype(np.uint8)

            # Reconstruct Image Object
            img = Image.fromarray(visual_data)
            
            # Save
            img.save(output_path)
            print(f"[VisionLoader] Reconstructed reality saved to: {output_path}")

        except Exception as e:
            raise RuntimeError(f"VisionLoader failed to render image: {e}")

# --- Self-Test Block (Runs if you execute this file directly) ---
if __name__ == "__main__":
    # Create a dummy image to test the logic
    loader = VisionLoader()
    
    # Generate a pure math gradient (0.0 to 1.0)
    print("Running Logic Test...")
    width, height = 256, 256
    test_matrix = np.zeros((height, width, 3), dtype=np.float64)
    
    for y in range(height):
        for x in range(width):
            # Create a logical Red/Blue gradient
            test_matrix[y, x] = [x/255.0, y/255.0, 0.0]

    # Save it to prove the system works
    loader.save_from_math(test_matrix, "system_check_gradient.png")
    print("Test Complete. Check 'system_check_gradient.png'.")
