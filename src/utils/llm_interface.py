import ollama

def prompt_llm(prompt_text):
    """ Sends a prompt to LLM model and returns the response."""
    try:
        response = ollama.chat(
            model='llama3',
            messages=[{
                "role": "user",
                "content": prompt_text
            }],
            stream=False,
        )
        return response['message']['content']
    
    except Exception as e:
        print(f"An error occurred while calling the LLM: {e}")
        return "Error: Could not get a response from the model."