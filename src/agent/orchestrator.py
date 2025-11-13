import logging

from .prompt_builder import PromptBuilder 
from ..tools import Tool
from ..utils import prompt_llm, parse_llm_output

logger = logging.getLogger(__name__)

def react_orchestrator(task: str, tools: list[Tool], max_steps: int = 10):
    """
    Orchestrates the ReAct agent loop
    """
    logging.info("======== Starting New Task ========")
    logging.info(f"Task: {task}")
    logging.info(f"Tools Available: {[tool.name for tool in tools]}")
    
    prompt_builder = PromptBuilder(task, tools)
    tool_dict = {tool.name: tool for tool in tools}
    
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
            observation = tool.execute(action_input)
        
        logging.info(f"Observation: {observation}")
        
        #TODO: Tool errors need to be handled before adding
        # Update history
        prompt_builder.add_step(thought, action, observation)
    
    logging.warning("Max steps reached. Task could not be completed.")
    return "Max steps reached. Task incomplete."
