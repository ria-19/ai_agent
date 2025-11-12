import ollama
import re
from ddgs import DDGS
import logging
import sys 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout  
)

# 1. Orchestrator (Main Loop)
def react_orchestrator(task, tools, max_steps=10):
    """
    Orchestrates the ReAct agent loop
    """
    logging.info("======== Starting New Task ========")
    logging.info(f"Task: {task}")
    logging.info(f"Tools Available: {[tool['name'] for tool in tools]}")
    
    prompt_builder = PromptBuilder(task, tools)
    tool_dict = {tool['name']: tool for tool in tools}
    
    for step in range(max_steps):
        logging.info(f"---------- Step {step + 1}/{max_steps} ----------")

        # Build prompt
        if step == 0:
            prompt = prompt_builder.build_initial_prompt()
        else:
            prompt = prompt_builder.build_continuation_prompt()
            
        logging.debug(f"Full Prompt Sent to LLM:\n{prompt}")
        
        # Get LLM response
        response = prompt_llm(prompt)
        logging.info(f"LLM Raw Response:\n{response}")
        
        # Parse response
        thought, action, action_input = parse_llm_output(response)
        logging.info(f"Parsed Thought: {thought}")
        logging.info(f"Parsed Action: '{action}' | Parsed Input: '{action_input}'")
        
        # Check if finished
        if action == "Finish":
            logging.info("Action is 'Finish'. Task is complete.")
            final_answer = action_input
            logging.info(f"Final Answer: {final_answer}")
            return final_answer
        
        if action == "Error":
            logging.error(f"Parser failed. Agent cannot continue. Reason: {action_input}")
            return f"Agent failed: {action_input}"
        
        # Execute a tool
        observation = ""
        if action not in tool_dict:
            logging.warning(f"Agent hallucinated an unknown tool: '{action}'")
            observation = f"Error: Unknown tool '{action}'. Please use one of the available tools."
        else:
            logging.info(f"Executing Tool: '{action}'")
            tool = tool_dict[action]
            observation = execute_tool(tool, action_input)
        
        logging.info(f"Observation: {observation}")
        
        #TODO: Tool errors need to be handled before adding
        # Update history
        prompt_builder.add_step(thought, action, observation)
    
    logging.warning("Max steps reached. Task could not be completed.")
    return "Max steps reached. Task incomplete."

# 2. LLM Interface
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

# 3. Parser
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

# 4. Tool Executor (V2: move in tool class: encapsulates all tool logic and data)
def execute_tool(tool, args):
    try:
        return tool['function'](args)
    except Exception as e:
        return f"Error executing tool {tool['name']}: {e}"

# 5. Error Detector
class ErrorPatternDetector:
    def __init__(self):
        self.action_history = []
        self.observation_history = []
    
    def is_stuck(self, action, observation):
        # Your Strategy #2 logic
        pass
    
    def handle_failure(self):
        # Fallback strategy
        pass

# 6. Prompt Builder 
class PromptBuilder:
    def __init__(self, task, tools):
        self.task = task
        self.tools = tools
        self.history = []  # Stores (thought, action, observation) tuples
    
    def build_initial_prompt(self):
        # ---
        # REVIEW COMMENT (Minor Issue)
        # What: The ReAct example text ('Thought: I need to find...') is hardcoded.
        # Why: This is a minor form of "brittleness." If you change the tool names
        #      (e.g., rename 'Search' to 'web_search'), this example becomes outdated.
        #      An outdated example can confuse the LLM and lead to it generating
        #      incorrect or malformed actions.
        # How to Fix: A more robust solution would make the example generic or, in an
        #      advanced system, dynamically generate a relevant example based on the
        #      tools provided.
        # When to Fix: Low priority. Can be addressed after fixing the critical issues.
        # ---
        """First prompt with task + tool descriptions"""

        return f"""You are an agent that solves tasks step-by-step using available tools.

        Task: {self.task}

        Available tools:
        {self._format_tools()}
        
        CRITICAL RULES:
        1. You must output EXACTLY ONE action per response
        2. After writing "Action Input:", STOP IMMEDIATELY
        3. Do NOT write "Observation:" - I will provide that in my next message
        4. Do NOT predict future steps
        5. Wait for me to give you the observation before continuing

        Format:
        Thought: [your reasoning about the NEXT step only]
        Action: [choose ONE: {', '.join([t['name'] for t in self.tools])}]
        Action Input: [input for that action]

        CORRECT example (generates only ONE action):
        Thought: I need to calculate 15% of 200
        Action: Calculator  
        Action Input: 200 * 0.15

        WRONG example (DO NOT DO THIS):
        Thought: I need to calculate 15% of 200
        Action: Calculator
        Action Input: 200 * 0.15
        Observation: 30    ← WRONG! Don't write this!
        Thought: Now I'll finish  ← WRONG! Stop after first Action Input!

        Now solve this task:
        """
    
    def add_step(self, thought, action, observation):
        """Add T-A-O to history"""
        self.history.append((thought, action, observation))
    
    def build_continuation_prompt(self):
        # ---
        # REVIEW COMMENT (Critical Architectural Flaw): Monolithic prompt construction and lack of state separation
        # What: This method rebuilds the entire prompt string from scratch on every turn.
        #      It re-generates the instructions and then loops through the *entire* past
        #      history to append it to the string.
        #
        # Why: This is a major scalability bottleneck and is unacceptable for a production system.
        #      1. High Cost: LLM APIs are priced per token. Re-sending the same static
        #         instructions and old history in every call is extremely wasteful and
        #         will dramatically increase the cost of running the agent.
        #      2. High Latency: More tokens = longer processing time. The agent will get
        #         progressively slower with every step it takes.
        #      3. Context Window Limits: Every LLM has a maximum token limit. This method
        #         ensures you will hit that limit very quickly on any complex task,
        #         causing the agent to fail.
        #
        # How to Fix: Separate the static prompt components from the dynamic history.
        #      1. Create a single "System Prompt" containing the core instructions and
        #         tool definitions. This is created only ONCE.
        #      2. Store the history as a list of messages (e.g., `[{'role': 'assistant', ...},
        #         {'role': 'user', ...}]`), which is the standard for modern chat models.
        #      3. On each turn, simply append the latest agent action and tool observation
        #         to this list. Do not rebuild the entire history.
        #
        # When to Fix: Immediately. This is a foundational flaw. Building any more
        #      features on top of this design will lead to expensive refactoring later.
        # ---
        """Prompt for next iteration with full history"""
        prompt = self.build_initial_prompt()
        
        for thought, action, obs in self.history:
            prompt += f"\nThought: {thought}"
            prompt += f"\nAction: {action}"
            prompt += f"\nObservation: {obs}"
        
        prompt += "\nThought:"  # Prompt for next thought
        return prompt
    
    def _format_tools(self):
        """Format tool descriptions for LLM"""
        tool_descriptions = []
        for tool in self.tools:
            desc = f"- {tool['name']}: {tool['description']}"
            tool_descriptions.append(desc)
        return "\n".join(tool_descriptions)

# Tool: Calculator
def calculator_function(expression: str) -> str:
    """Evaluates a python mathematical expression"""
    print(f"Calculator Expression: {expression}")
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Invalid expression: {e}"
    
# Tool: Simple Search
def search_function(query: str) -> str:
    """A simple search tool placeholder."""
    print(f"Search Query: {query}")
    try:
        with DDGS() as ddgs:
            results = [result for result in ddgs.text(query, max_results=3)]
            if not results:
                return f"No information found for '{query}'."
            
            formatted_results = "\n".join([f"[{i+1}] {res['title']}: {res['body']}" for i, res in enumerate(results)])
            return formatted_results
        
    except Exception as e:
        return f"Error during search: {e}"

if __name__ == "__main__":
    task = "What's 15% of the current stock price of Apple (AAPL)?"
    #task = "What's 15% of 200?"
    #task = "What's the weather on Mars right now?"


    # TODO: Refactor tools into a Tool class for better organization and scalability.
    tools = [
    {
        "name": "Search",
        "description": "A tool to search the internet for up-to-date information.",
        "function": search_function 
    },
    {
        "name": "Calculator",
        "description": "A tool to perform mathematical calculations.",
        "function": calculator_function
    },
    {
    "name": "Finish",
    "description": "Use this action to signal you are done. The Action Input MUST be the final, complete answer to the user's original question.",
    "function": None # No function needed, handled by the orchestrator
    }]
    
    final_answer = react_orchestrator(task, tools)
    
    print("\n----- FINAL ANSWER -----")
    print(final_answer)