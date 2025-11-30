import json
import numpy as np
from vision_loader import VisionLoader
from atomizer import Atomizer
import sys

# Set numpy to print full arrays without truncation for text export
np.set_printoptions(threshold=sys.maxsize)

class TextConverter:
    def __init__(self):
        self.loader = VisionLoader()
        self.cortex = Atomizer()

    def image_to_text(self, image_path, output_txt_path):
        """
        Takes a Real Image -> Saves as Mathematical Text File (.json)
        """
        print(f"Converting {image_path} to PURE MATH TEXT...")
        
        # 1. Load to Matrix
        math_data = self.loader.load_to_math(image_path)
        matrix = math_data["matrix"]
        
        # 2. Convert Matrix to List (so we can save as text)
        # We save 5 decimal places to keep file size manageable but precise
        rounded_data = np.round(matrix, 5).tolist()
        
        # 3. Create the Logic Structure
        logic_packet = {
            "dimensions": math_data["shape"],
            "atoms": rounded_data  # This is the giant list of [R,G,B] vectors
        }

        # 4. Save to Text File
        with open(output_txt_path, 'w') as f:
            json.dump(logic_packet, f)
            
        print(f"Success! Math logic saved to {output_txt_path}")

    def text_to_image(self, txt_path, output_image_path):
        """
        Takes Mathematical Text File -> Rebuilds Real Image
        """
        print(f"Reading Logic from {txt_path}...")
        
        # 1. Read the Text
        with open(txt_path, 'r') as f:
            logic_packet = json.load(f)
            
        # 2. Extract Data
        raw_atoms = logic_packet["atoms"]
        
        # 3. Convert List back to Numpy Matrix
        matrix = np.array(raw_atoms, dtype=np.float64)
        
        # 4. Save as Image
        self.loader.save_from_math(matrix, output_image_path)
        print(f"Success! Reality rebuilt at {output_image_path}")

if __name__ == "__main__":
    converter = TextConverter()
    
    # UNCOMMENT THE OPERATION YOU WANT TO TEST:
    
    # TEST 1: Image -> Text
    # converter.image_to_text("input.jpg", "image_logic.json")
    
    # TEST 2: Text -> Image (The Rebuild)
    # converter.text_to_image("image_logic.json", "rebuilt_image.png")
