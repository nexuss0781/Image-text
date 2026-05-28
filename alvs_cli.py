#!/usr/bin/env python3
"""
Production-ready CLI for Atomic Logic Vision System (ALVS).

Uses high-performance C++ backend when available.
"""

import argparse
import sys
import time
from pathlib import Path

# Import production modules
from alvs import VisionLoader, Atomizer, Synthesizer, get_backend_info


def main():
    # Setup CLI
    parser = argparse.ArgumentParser(
        description="Atomic Logic Vision System (ALVS) - Production Image Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.jpg output.png --mode reconstruct
  %(prog)s city.jpg flow.png --mode visualize_flow
  %(prog)s photo.png boosted.png --mode energy_boost
  %(prog)s image.jpg inverse.jpg --mode quantum_inverse
        """
    )
    
    parser.add_argument("input", type=str, nargs="?", help="Path to input image")
    parser.add_argument("output", type=str, nargs="?", help="Path to save output image")
    parser.add_argument(
        "--mode",
        choices=["reconstruct", "visualize_flow", "quantum_inverse", "energy_boost"],
        default="reconstruct",
        help="Logic operation to perform (default: reconstruct)"
    )
    parser.add_argument(
        "--pure-python",
        action="store_true",
        help="Force use of pure Python backend (no C++ acceleration)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show backend information and exit"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark and show performance metrics"
    )
    
    args = parser.parse_args()
    
    # Show info if requested (doesn't require input/output)
    if args.info:
        info = get_backend_info()
        print("\n=== ALVS Backend Information ===")
        print(f"Backend Type: {info['backend_type']}")
        print(f"C++ Acceleration: {'Enabled' if info['has_cpp_backend'] else 'Disabled'}")
        print(f"NumPy Version: {info['numpy_version']}")
        print()
        return 0
    
    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1
    
    # Initialize pipeline
    use_cpp = not args.pure_python
    
    print("\n=== ALVS Production Pipeline ===")
    print(f"Backend: {'C++ Accelerated' if use_cpp and get_backend_info()['has_cpp_backend'] else 'Pure Python'}")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Mode: {args.mode}")
    print()
    
    # Initialize components
    loader = VisionLoader(use_cpp=use_cpp)
    atomizer = Atomizer(use_cpp=use_cpp)
    synthesizer = Synthesizer(use_cpp=use_cpp)
    
    # Execute pipeline
    start_time = time.perf_counter()
    
    # Phase 1: Load
    print("[Phase 1/4] Loading image...")
    try:
        math_data = loader.load_to_math(args.input)
    except Exception as e:
        print(f"Error loading image: {e}", file=sys.stderr)
        return 1
    
    # Phase 2: Atomize
    print("[Phase 2/4] Computing atomic context (Energy + Flow)...")
    logic_context = atomizer.atomize(math_data["matrix"])
    
    # Phase 3: Synthesize
    print(f"[Phase 3/4] Applying transformation ({args.mode})...")
    if args.mode == "reconstruct":
        result_matrix = synthesizer.reconstruct(logic_context)
    else:
        result_matrix = synthesizer.smart_remix(logic_context, mode=args.mode)
    
    # Phase 4: Save
    print("[Phase 4/4] Saving output...")
    loader.save_from_math(result_matrix, args.output)
    
    # Report
    elapsed = time.perf_counter() - start_time
    print(f"\n=== Complete ===")
    print(f"Time: {elapsed:.4f}s")
    print(f"Input shape: {math_data['shape']}")
    print(f"Output: {args.output}")
    
    # Benchmark if requested
    if args.benchmark:
        print("\n=== Benchmark Mode ===")
        
        # Run multiple iterations
        n_iterations = 5
        times = []
        
        for i in range(n_iterations):
            iter_start = time.perf_counter()
            
            math_data = loader.load_to_math(args.input)
            logic_context = atomizer.atomize(math_data["matrix"])
            
            if args.mode == "reconstruct":
                result_matrix = synthesizer.reconstruct(logic_context)
            else:
                result_matrix = synthesizer.smart_remix(logic_context, mode=args.mode)
            
            iter_elapsed = time.perf_counter() - iter_start
            times.append(iter_elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        pixels = math_data['shape'][0] * math_data['shape'][1]
        throughput = pixels / avg_time / 1e6  # MPixels/s
        
        print(f"Iterations: {n_iterations}")
        print(f"Average: {avg_time:.4f}s")
        print(f"Min: {min_time:.4f}s")
        print(f"Max: {max_time:.4f}s")
        print(f"Throughput: {throughput:.2f} MPixels/s")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
