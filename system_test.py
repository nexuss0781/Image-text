.import os
import sys
import time
import json
import numpy as np
from vision_loader import VisionLoader
from atomizer import Atomizer
from synthesizer import Synthesizer

# ANSI Colors for CLI output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(status, message):
    if status == "PASS":
        print(f"[{GREEN}PASS{RESET}] {message}")
    elif status == "FAIL":
        print(f"[{RED}FAIL{RESET}] {message}")
    else:
        print(f"[INFO] {message}")

def run_full_diagnostic():
    print("========================================")
    print("   ALVS AUTOMATED DIAGNOSTIC SEQUENCE   ")
    print("========================================")

    # 1. Initialize Modules
    try:
        loader = VisionLoader()
        cortex = Atomizer()
        renderer = Synthesizer()
        log("PASS", "Modules Loaded: VisionLoader, Atomizer, Synthesizer")
    except Exception as e:
        log("FAIL", f"Module Load Error: {e}")
        sys.exit(1)

    # 2. Check Resources
    required_images = ["city.jpg", "dog.jpg", "gradient.jpg"]
    missing = [img for img in required_images if not os.path.exists(img)]
    
    if missing:
        log("FAIL", f"Missing images: {missing}")
        print("Please download images and rename them exactly: city.jpg, dog.jpg, gradient.jpg")
        sys.exit(1)
    else:
        log("PASS", "Test Resources Found")

    # ---------------------------------------------------------
    # TEST A: The Mirror Test (city.jpg)
    # ---------------------------------------------------------
    print("\n--- Running Test A: Mirror Reconstruction ---")
    try:
        t0 = time.time()
        # Load
        data = loader.load_to_math("city.jpg")
        # Pass through Logic (No changes)
        logic = cortex.atomize(data["matrix"])
        reconstruction = renderer.reconstruct(logic)
        # Save
        loader.save_from_math(reconstruction, "test_result_mirror.png")
        
        log("PASS", f"Mirror Test Complete ({time.time()-t0:.2f}s) -> 'test_result_mirror.png'")
    except Exception as e:
        log("FAIL", f"Mirror Test Failed: {e}")

    # ---------------------------------------------------------
    # TEST B: The Cortex/Flow Test (dog.jpg)
    # ---------------------------------------------------------
    print("\n--- Running Test B: Logic Flow Analysis ---")
    try:
        t0 = time.time()
        # Load
        data = loader.load_to_math("dog.jpg")
        # Atomize (Calculate Logic)
        logic = cortex.atomize(data["matrix"])
        # Remix (Visualize the Math)
        flow_map = renderer.smart_remix(logic, mode="visualize_flow")
        # Save
        loader.save_from_math(flow_map, "test_result_flow.png")
        
        log("PASS", f"Flow Analysis Complete ({time.time()-t0:.2f}s) -> 'test_result_flow.png'")
    except Exception as e:
        log("FAIL", f"Flow Test Failed: {e}")

    # ---------------------------------------------------------
    # TEST C: The Physics/Energy Test (gradient.jpg)
    # ---------------------------------------------------------
    print("\n--- Running Test C: Energy Physics ---")
    try:
        t0 = time.time()
        data = loader.load_to_math("gradient.jpg")
        logic = cortex.atomize(data["matrix"])
        energy_map = renderer.smart_remix(logic, mode="energy_boost")
        loader.save_from_math(energy_map, "test_result_energy.png")
        
        log("PASS", f"Energy Physics Complete ({time.time()-t0:.2f}s) -> 'test_result_energy.png'")
    except Exception as e:
        log("FAIL", f"Energy Test Failed: {e}")

    # ---------------------------------------------------------
    # TEST D: The Lexical Conversion (Math Text Cycle)
    # ---------------------------------------------------------
    print("\n--- Running Test D: Image -> Text -> Image ---")
    try:
        t0 = time.time()
        # 1. Load Image
        data = loader.load_to_math("gradient.jpg") # Use gradient as it's cleaner for text
        matrix = data["matrix"]
        
        # 2. Convert to JSON (Text)
        # We round to 4 decimals to keep the test fast
        log("INFO", "Serializing to JSON Text...")
        text_packet = {
            "shape": data["shape"],
            "atoms": np.round(matrix, 4).tolist()
        }
        
        json_path = "test_data.json"
        with open(json_path, "w") as f:
            json.dump(text_packet, f)
            
        # 3. Read back from JSON
        log("INFO", "Deserializing back to Matrix...")
        with open(json_path, "r") as f:
            loaded_packet = json.load(f)
            
        rebuilt_matrix = np.array(loaded_packet["atoms"], dtype=np.float64)
        
        # 4. Save Image
        loader.save_from_math(rebuilt_matrix, "test_result_text_reborn.png")
        
        log("PASS", f"Text Cycle Complete ({time.time()-t0:.2f}s) -> 'test_result_text_reborn.png'")
        
    except Exception as e:
        log("FAIL", f"Lexical Test Failed: {e}")

    print("\n========================================")
    print("       ALL DIAGNOSTICS COMPLETED        ")
    print("========================================")

if __name__ == "__main__":
    run_full_diagnostic()
