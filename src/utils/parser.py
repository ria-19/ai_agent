import re

def parse_llm_output(output_text):
    """
    Parses the raw text output from an LLM into a structured tuple.
    This function now also normalizes the action to be lowercase and stripped.
    """
    output_text = output_text.strip()
    
    thought = ""
    action = ""
    action_input = ""
    
    # Extract each field separately
    # 1. Extract Thought
    # We look for "Thought:" and capture everything until "Action:" or End of String
    thought_match = re.search(r"Thought:\s*(.*?)(?=\n?Action:|$)", output_text, re.DOTALL | re.IGNORECASE)
    thought = thought_match.group(1).strip() if thought_match else ""
    
    # 2. Extract Action
    # We look for "Action:" and capture the word immediately following it
    action_match = re.search(r"Action:\s*(\w+)", output_text, re.IGNORECASE)
    action = action_match.group(1).strip().lower() if action_match else ""
    
    # 3. Extract Action Input
    # We look for "Action Input:" and capture everything until "Observation:" or End of String
    input_match = re.search(r"Action Input:\s*(.*?)(?=\n?Observation:|$)", output_text, re.DOTALL | re.IGNORECASE)
    action_input = input_match.group(1).strip() if input_match else ""
    
    # --- CLEANUP LOGIC ---
    
    # Remove common LLM artifacts like "---" or "```" at the end of the input
    # Many models (Qwen, Llama) add these separators.
    
    # Remove trailing Markdown block markers
    action_input = action_input.replace("```json", "").replace("```", "")
    
    # Remove trailing dashes often used as separators (e.g., "\n---")
    # This regex removes a newline followed by 3 or more dashes at the end of the string
    action_input = re.sub(r"\n\s*-{3,}\s*$", "", action_input)
    
    # Strip again just in case
    action_input = action_input.strip()
    
    
    # Validation
    if not action:
        return ("", "error", f"Could not parse action from: '{output_text}'")
    
    return thought, action, action_input
