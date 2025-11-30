import logging
import sys 
import argparse
import json
from dataclasses import is_dataclass, asdict

# --- Interfaces & Types ---
from src.architectures import BaseAgent
# --- Concrete Implementations ---
from src.architectures import ReactAgent, ReflexionAgent
from src.llm import get_llm_interface, LLMConnectionError
from src.components.evaluators import LLMJudgeEvaluator
from src.components.reflectors import LLMReflector
from src.components.memory import SimpleMemory
from src.utils import parse_llm_output
from src.tools import all_tools
from enum import Enum

# --- Configure Logging  git ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- Custom JSON Encoder for Dataclasses ---
class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        # Handle Enums (Like EvaluationStatus)
        if isinstance(o, Enum):
            return o.value  # Returns the string value (e.g., "success")
        
        # Handle Pydantic models or objects with __dict__
        if hasattr(o, '__dict__'):
            return o.__dict__
            
        # Handle Sets (JSON doesn't support sets)
        if isinstance(o, set):
            return list(o)
            
        return super().default(o)
    
def main():
    # Define the Task and Tools
    
    #task = "What is 15% of the current price of NVDA stock, and what were their last quarter earnings?"
    #task = "What's 15% of the current stock price of Apple (AAPL)?"
    #task = "What's 15% of 200?"
    # task = "What's the weather on Mars right now?"
    
    # --- 1. Command-Line Argument Parsing ---
    parser = argparse.ArgumentParser(description="Run an agent architecture.")
    parser.add_argument("task", type=str, help="The task for the agent to perform.")
    parser.add_argument(
        "--agent",
        type=str,
        choices=["react", "reflexion"],
        default="reflexion",
        help="The agent architecture to run ('react' or 'reflexion')."
    )
    args = parser.parse_args()
    task = args.task
    agent_choice = args.agent
    
    logger.info(f"STARTING AGENT '{agent_choice.upper()}' WITH Task: '{task}'")
    
    # --- 2. Shared Component Initialization ---
    # ------ Parser ------   
    # single function we can pass it directly
    
    # ------ Define the list of Tools ------
    tools = all_tools
    
    try:
        # actor_llm = get_llm_interface(provider="Ollama", model="llama3")
        # judge_llm = get_llm_interface(provider="Ollama", model="llama3")

        actor_llm = get_llm_interface(provider="Groq", model="llama-3.3-70b-versatile")  #qwen/qwen3-32b,openai/gpt-oss-120b
        judge_llm = get_llm_interface(provider="google", model="gemini-2.5-flash")
    except (ValueError, LLMConnectionError) as e:
        logger.error(f"CRITICAL: Failed to initialize LLM interfaces. {e}")
        sys.exit(1)
 
      
    # --- 3. Agent Assembly based on Choice ---
    agent: BaseAgent  # Type hint to show that all agents conform to the interface

    if agent_choice == "reflexion":
        memory = SimpleMemory(max_size=5)
        actor = ReactAgent(llm_interface=actor_llm, parser=parse_llm_output, tools=tools, max_steps=7)
        evaluator = LLMJudgeEvaluator(llm_interface=judge_llm)
        reflector = LLMReflector(llm_interface=judge_llm)
        
        agent = ReflexionAgent(
            actor=actor,
            evaluator=evaluator,
            reflector=reflector,
            memory=memory,
            max_trials=3,
            success_threshold=0.95,
            failure_threshold=0.80,
            uncertainty_policy="accept"
        )
        
    elif agent_choice == "react":
        # The ReactAgent is now the same as the Reflexion's Actor
        agent = ReactAgent(
            llm_interface=actor_llm,
            parser=parse_llm_output,
            tools=tools,
            max_steps=10 # Allow more steps if not reflecting
        )
    else:
        # This case is technically handled by argparse's `choices`, but it's good practice
        logger.error(f"Unknown agent type '{agent_choice}'. Exiting.")
        sys.exit(1)

    # --- 4. Run the Agent ---
    result = agent.run(task)
    
    # --- 5. Display the Final Result ---
    print("\n" + "="*50)
    print(f"----- FINAL RESULT ({agent_choice.upper()}) -----")
    print("="*50)
    print(json.dumps(result, indent=2, cls=CustomEncoder))
    print("="*50)

if __name__ == "__main__":
    main()
    