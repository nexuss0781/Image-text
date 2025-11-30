import argparse
import sys
import time

# Import our Custom Smart Modules
from vision_loader import VisionLoader
from atomizer import Atomizer
from synthesizer import Synthesizer

def main():
    # 1. Setup the Command Line Interface
    parser = argparse.ArgumentParser(
        description="Atomic Logic Vision System (ALVS) - Pure Math Image Processor"
    )
    
    parser.add_argument("input", help="Path to the input image (jpg/png)")
    parser.add_argument("output", help="Path to save the result")
    parser.add_argument(
        "--mode", 
        choices=["reconstruct", "visualize_flow", "quantum_inverse", "energy_boost"],
        default="reconstruct",
        help="The logic operation to perform."
    )

    args = parser.parse_args()

    # 2. Initialize the Machines
    print("\n--- Booting ALVS Core Systems ---")
    try:
        loader = VisionLoader()
        cortex = Atomizer()
        renderer = Synthesizer()
    except Exception as e:
        print(f"CRITICAL ERROR: System modules failed to load. {e}")
        sys.exit(1)

    # 3. Execution Pipeline
    start_time = time.time()

    # Step A: Ingestion (Eye)
    print(f"\n[Phase 1] Ingesting Reality: {args.input}")
    try:
        math_data = loader.load_to_math(args.input)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Step B: Logic Analysis (Brain)
    print(f"\n[Phase 2] Atomizing Logic...")
    # This turns raw numbers into 'Smart Atoms' with flow and energy
    logic_context = cortex.atomize(math_data["matrix"])

    # Step C: Synthesis (Hand)
    print(f"\n[Phase 3] Synthesizing Output (Mode: {args.mode})...")
    
    if args.mode == "reconstruct":
        # Pure reconstruction to prove lossless math
        result_matrix = renderer.reconstruct(logic_context)
    else:
        # Applying Smart Logic
        result_matrix = renderer.smart_remix(logic_context, mode=args.mode)

    # Step D: Materialization (Output)
    print(f"\n[Phase 4] Materializing to Disk: {args.output}")
    loader.save_from_math(result_matrix, args.output)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n--- Operation Complete in {elapsed:.4f} seconds ---")
    print(f"Logic used: {args.mode}")
    print(f"File saved: {args.output}\n")

if __name__ == "__main__":
    main()
