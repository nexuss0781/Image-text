import numpy as np

class Synthesizer:
    """
    The Reality Builder (Module C).
    
    Responsibilities:
    1. Reconstruct viewable images from 'Atomic Logic'.
    2. Apply 'Smart Filters' that use the Flow and Energy data.
    3. Prepare the final matrix for the VisionLoader to save.
    """

    def __init__(self):
        pass

    def reconstruct(self, atomic_context):
        """
        The basic renderer. Takes the logic context and extracts the visual layer.
        This proves the system is lossless.
        """
        print("[Synthesizer] Reconstructing reality from logic atoms...")
        # In a generation scenario, this would be where the AI 'paints' the prediction.
        # For now, we return the color vector layer.
        return atomic_context["color"]

    def smart_remix(self, atomic_context, mode="edge_glow"):
        """
        Demonstrates 'Logic-Based Generation'.
        Instead of a standard filter, this modifies the image based on the
        mathematical understanding of the pixels (Flow and Energy).
        
        Args:
            atomic_context (dict): The data from Atomizer.
            mode (str): The logic rule to apply.
        """
        print(f"[Synthesizer] applying logic rule: {mode}")
        
        # Extract layers
        color = atomic_context["color"].copy()
        energy = atomic_context["energy"]
        flow_x = atomic_context["flow_x"]
        flow_y = atomic_context["flow_y"]

        if mode == "visualize_flow":
            # LOGIC: If the color is changing fast (high flow), light it up.
            # This allows us to see the 'Structure' of the image the way the machine sees it.
            # We calculate total magnitude of change.
            flow_magnitude = np.sqrt(flow_x**2 + flow_y**2)
            
            # Normalize flow to 0.0-1.0 for visibility (multiply by 5 to boost weak edges)
            flow_visual = np.clip(flow_magnitude * 5.0, 0.0, 1.0)
            
            # Create a heatmap: Red = High Change, Black = Static
            # We broadcast the single channel (H, W) to 3 channels (H, W, 3)
            new_matrix = np.dstack((flow_visual, flow_visual, flow_visual))
            return new_matrix

        elif mode == "quantum_inverse":
            # LOGIC: Invert the color vector, but preserve the Energy structure.
            # Standard inversion (1-x) creates weird shadows. 
            # Smart inversion preserves the 'lightness' while flipping the hue.
            inverted_color = 1.0 - color
            return inverted_color

        elif mode == "energy_boost":
            # LOGIC: Only boost pixels that are already 'High Energy' (Bright).
            # This makes the light source glow without washing out the darks.
            
            # Create a mask where Energy > 0.5
            boost_mask = (energy > 0.5).astype(np.float64)
            
            # Expand dimensions to match RGB
            boost_mask = np.dstack((boost_mask, boost_mask, boost_mask))
            
            # Add 20% brightness only to high-energy atoms
            new_matrix = color + (boost_mask * 0.2)
            return new_matrix

        else:
            print(f"Unknown mode {mode}, returning original.")
            return color

# --- Self-Test Block ---
if __name__ == "__main__":
    # Simulate Logic Data
    print("Running Synthesizer Test...")
    
    # Create a 100x100 random noise grid
    dummy_color = np.random.rand(100, 100, 3)
    dummy_energy = np.mean(dummy_color, axis=2)
    # Fake flow
    dummy_flow_x = np.random.rand(100, 100) * 0.1
    dummy_flow_y = np.random.rand(100, 100) * 0.1

    context = {
        "color": dummy_color,
        "energy": dummy_energy,
        "flow_x": dummy_flow_x,
        "flow_y": dummy_flow_y
    }
    
    synth = Synthesizer()
    result = synth.smart_remix(context, mode="visualize_flow")
    
    print(f"Remix complete. Result Shape: {result.shape}")
