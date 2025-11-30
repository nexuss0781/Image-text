import numpy as np

class Atomizer:
    """
    The Logic Converter (Module B).
    
    Responsibilities:
    1. Analyze the mathematical relationship between pixels.
    2. Calculate 'Hidden' data: Luminance (Energy) and Gradients (Flow).
    3. Serve 'Smart Atoms' to the Generator/Synthesizer.
    """

    def __init__(self):
        pass

    def atomize(self, math_matrix):
        """
        Converts a raw color matrix into a 'Logic Tensor'.
        
        Instead of just RGB, every pixel becomes a multi-dimensional logic unit:
        [R, G, B, Luminance, Gradient_X, Gradient_Y]
        
        Args:
            math_matrix (numpy array): Input from VisionLoader (0.0 - 1.0).
            
        Returns:
            dict: The 'AtomicContext' containing the analyzed layers.
        """
        print("[Atomizer] Initializing Logic Analysis...")
        
        # 1. Base Layer: The Vector Color (R, G, B)
        # This is the exact truth of the image.
        color_layer = math_matrix

        # 2. Energy Layer: Luminance Calculation
        # Smart Logic: We calculate how 'energetic' (bright) a pixel is using 
        # human perception physics (Rec. 709 standard).
        # Formula: 0.2126*R + 0.7152*G + 0.0722*B
        energy_layer = np.dot(color_layer[...,:3], [0.2126, 0.7152, 0.0722])

        # 3. Flow Layer: Gradient Analysis (The Derivative)
        # Smart Logic: We calculate the 'Speed' of color change. 
        # If the flow is 0, it's a flat color. If flow is high, it's an edge or texture.
        # axis=0 is vertical change (dy), axis=1 is horizontal change (dx)
        grad_y, grad_x, _ = np.gradient(color_layer)
        
        # We average the RGB flow into a single 'Magnitude' of change per pixel
        flow_x = np.mean(grad_x, axis=2)
        flow_y = np.mean(grad_y, axis=2)

        print("[Atomizer] Logic Layers Calculated:")
        print(f"           - Energy Matrix (Brightness Physics)")
        print(f"           - Flow Matrix (Vector Derivatives)")

        return {
            "color": color_layer,  # The Visuals
            "energy": energy_layer, # The Brightness Map
            "flow_x": flow_x,       # Horizontal Color Velocity
            "flow_y": flow_y        # Vertical Color Velocity
        }

    def get_smart_atom(self, atomic_context, x, y):
        """
        Extracts a single 'Lexical Atom' from the logic context.
        This is used when the machine needs to focus on a specific point.
        """
        try:
            atom = {
                "coordinate": (x, y),
                "vector_rgb": atomic_context["color"][y, x].tolist(),
                "energy_val": float(atomic_context["energy"][y, x]),
                "logic_flow": [
                    float(atomic_context["flow_x"][y, x]),
                    float(atomic_context["flow_y"][y, x])
                ]
            }
            return atom
        except IndexError:
            return None

# --- Self-Test Block ---
if __name__ == "__main__":
    # Simulate a 2x2 Image input (Normalized Floats)
    # Top Row: Black -> White
    # Bottom Row: Red -> Blue
    dummy_input = np.array([
        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
        [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    ])
    
    machine = Atomizer()
    logic_data = machine.atomize(dummy_input)
    
    # Inspect a specific atom (Top Right - White Pixel)
    print("\n--- Inspecting Atom at (1, 0) ---")
    atom_data = machine.get_smart_atom(logic_data, 1, 0)
    
    import json
    print(json.dumps(atom_data, indent=2))
    
    # The 'logic_flow' should show a positive change because Black -> White
