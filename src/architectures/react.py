import logging
from typing import List, Dict, Any, Optional


from .base import BaseAgent
from src.agent import PromptBuilder 
from src.tools import Tool
from src.llm import LLMInterface, LLMConnectionError
from .constants import FINISH, ERROR

logger = logging.getLogger(__name__)

class ReactAgent(BaseAgent):
    """ ReAct architecture: Reasoning + Acting in loop."""
    
    def __init__(self, tools: List[Tool], llm_interface: LLMInterface, parser: Any, max_steps: int = 10):
        self.tools = tools
        self.tool_dict = {tool.name: tool for tool in self.tools} # A quick lookup dictionary for tools (name -> tool_instance)
        self.llm = llm_interface
        self.parser = parser
        self.max_steps = max_steps

    def run(self, task: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """ Runs the ReAct loop."""
        
        trajectory = []
        logger.info(f"Starting ReAct Agent with task: {task}")
                
        for step in range(self.max_steps):
            logger.info(f"--- Step {step + 1}/{self.max_steps} ---")

            # 1. Build the Message-Based Prompt: pass the CURRENT trajectory to the stateless builder
            messages = PromptBuilder.build_actor_prompt(
                task=task, 
                tools=self.tools, 
                trajectory=trajectory, 
                reflections=context
            )
            
            # 2. Call the LLM 
            logger.info(f"Step {step+1}: Calling LLM...")
            try:
                response_message = self.llm.get_chat_completion(messages)
            except LLMConnectionError as e:
                return self._handle_llm_error(e, trajectory)
            
            # Parse response and Normalize
            thought, action, action_input = self.parser(response_message['content'])
            logging.info(f"Parsed Thought: {thought}")
            logging.info(f"Parsed Action: '{action}' | Parsed Input: '{action_input}'")
            
            
            # Case 1: Terminal action - Finish
            if action == FINISH:
                return self._handle_finish_action(thought, action_input, trajectory)
            
            observation = self._execute_action(action, action_input)

            trajectory.append({
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation
            })
            
            logger.info(f"Observation: {observation}")
        
        # This block is only reached if the for loop completes without a "Finish" action.
        return self._handle_max_steps_reached(trajectory)
        
    def _truncate_observation(self, observation: str, max_length: int = 5000) -> str:
        """
        Truncates long observations to prevent context window overflow.
        Keeps the head and the tail, cutting out the middle.
        """
        if len(observation) <= max_length:
            return observation
        
        keep_head = max_length // 2
        keep_tail = max_length // 2
        
        head = observation[:keep_head]
        tail = observation[-keep_tail:]
        
        return f"{head}\n... [Content Truncated ({len(observation) - max_length} chars)] ...\n{tail}"

    def _handle_llm_error(self, error: LLMConnectionError, trajectory: List[Dict]) -> Dict[str, Any]:
        """ Handles a critical failure in the LLM call. """
        logger.error(f"LLM call failed: {error}")
        observation = f"Critical Error: The LLM call failed. Reason: {error}"
        trajectory.append({"thought": "LLM Error", "action": "error", "action_input": "", "observation": observation})
        return {
            "status": "error",
            "final_answer": None,
            "trajectory": trajectory,
            "error_message": str(error)
        }
        
    def _handle_finish_action(self, thought: str, action_input: str, trajectory: List[Dict]) -> Dict[str, Any]:
        """ Handles the terminal FINISH action. """
        final_answer = action_input
        observation = f"Agent finished with final answer: '{final_answer}'"
        trajectory.append({"thought": thought, "action": FINISH, "action_input": action_input, "observation": observation})
        logger.info("Action is 'Finish'. Task is complete.")
        return {
            "status": "finished",
            "final_answer": final_answer,
            "trajectory": trajectory,
            "error_message": None
        }
        
    def _handle_max_steps_reached(self, trajectory: List[Dict]) -> Dict[str, Any]:
        """ Handles the case where the agent runs out of steps. """
        logger.warning("ReAct Agent reached max steps without finishing.")
        return {
            "status": "max_steps_reached",
            "final_answer": None,
            "trajectory": trajectory,
            "error_message": f"Agent stopped after reaching the limit of {self.max_steps} steps."
        }
    
    def _execute_action(self, action: str, action_input: str) -> str:
        """ Dispatches to the correct action handler and returns the observation. """
        if action == ERROR:
            return f"Parsing Error: {action_input}"  # The parser returns the error details in action_input
        elif action in self.tool_dict:
            return self._handle_tool_action(action, action_input)
        else:
            return self._handle_unknown_action(action)

    def _handle_tool_action(self, action: str, action_input: str) -> str:
        """ Executes a known tool and handles potential errors. """
        try:
            tool = self.tool_dict[action]
            logger.info(f"Executing Tool: '{action}' with input: '{action_input}'")
            raw_observation = tool.execute(action_input)
            return self._truncate_observation(str(raw_observation))
        except Exception as e:
            logger.error(f"Tool execution for '{action}' failed: {e}", exc_info=True)
            return f"Error executing tool '{action}': {e}"

    def _handle_unknown_action(self, action: str) -> str:
        """ Handles the case where the LLM hallucinates an unknown tool. """
        logger.warning(f"Agent hallucinated an unknown tool: '{action}'")
        return f"Error: Tool '{action}' not found. Available tools: {list(self.tool_dict.keys())}"