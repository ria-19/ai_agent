import re

def parse_llm_output(output_text):
    """Parse LLM output"""
    thought = ""
    action = ""
    action_input = ""
    
    # Extract each field separately
    thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|$)", output_text, re.DOTALL)
    action_match = re.search(r"Action:\s*(\w+)", output_text)
    input_match = re.search(r"Action Input:\s*(.*?)(?=Observation:|$)", output_text, re.DOTALL)
    
    if thought_match:
        thought = thought_match.group(1).strip()
    if action_match:
        action = action_match.group(1).strip()
    if input_match:
        action_input = input_match.group(1).strip()
    
    # Validation
    if not action:
        return ("", "Error", f"Could not parse action from: '{output_text}'")
    
    return thought, action, action_input
