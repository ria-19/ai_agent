import logging
import time
import os
from dotenv import load_dotenv

# Import Architectures
from src.architectures import ReactAgent, ReflexionAgent

# Import Components
from src.components.evaluators import LLMJudgeEvaluator
from src.components.reflectors import LLMReflector
from src.components.memory import SimpleMemory

# Import Interfaces and Tools
from src.tools import all_tools
from src.llm import get_llm_interface
from src.utils import parse_llm_output


# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# We silence the noisy libraries to keep the output clean
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("ComparisonRunner")

# Load Env Vars (API Keys)
load_dotenv()

def measure_time(func):
    """Decorator to measure execution time"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper

@measure_time
def test_react_simple():
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 1: ReAct Agent - Simple Math")
    logger.info("Task: 'What is 15% of 200?'")
    logger.info("="*60)
    
    tools = all_tools
    # Use Fast LLM for ReAct
    llm = get_llm_interface("groq") 
    
    agent = ReactAgent(llm_interface=llm, parser=parse_llm_output, tools=tools, max_steps=5)
    
    task = "What is 15% of 200?"
    result = agent.run(task=task)
    
    return result

@measure_time
def test_reflexion_simple():
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 2: Reflexion Agent - Simple Math")
    logger.info("Task: 'What is 15% of 200?'")
    logger.info("="*60)
    
    tools = all_tools
    # Hybrid Setup: Groq for Acting, Google for Thinking
    actor_llm = get_llm_interface("groq")
    evaluator_llm = get_llm_interface("google") 
    
    actor = ReactAgent(llm_interface=actor_llm, parser=parse_llm_output, tools=tools, max_steps=5)
    evaluator = LLMJudgeEvaluator(llm_interface=evaluator_llm)
    reflector = LLMReflector(llm_interface=evaluator_llm)
    memory = SimpleMemory(max_size=3)
    
    agent = ReflexionAgent(
        actor=actor,
        evaluator=evaluator,
        reflector=reflector,
        memory=memory,
        max_trials=3,
        uncertainty_policy="accept"
    )
    
    task = "What is 15% of 200?"
    result = agent.run(task=task)
    
    return result

@measure_time
def test_react_multipart():
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 3: ReAct Agent - Finance Logic")
    logger.info("Task: Apple Stock Calculation")
    logger.info("="*60)
    
    tools = all_tools
    llm = get_llm_interface("groq")
    agent = ReactAgent(llm_interface=llm, parser=parse_llm_output, tools=tools, max_steps=5)

    
    task = "What is 15% of Apple's (AAPL) current stock price, and is it more or less than $50?"
    result = agent.run(task=task)
    
    return result

@measure_time
def test_reflexion_multipart():
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 4: Reflexion Agent - Finance Logic")
    logger.info("Task: Apple Stock Calculation")
    logger.info("="*60)
    
    tools = all_tools
    actor_llm = get_llm_interface("groq")
    evaluator_llm = get_llm_interface("google")
    
    actor = ReactAgent(llm_interface=actor_llm, parser=parse_llm_output, tools=tools, max_steps=5)
    evaluator = LLMJudgeEvaluator(llm_interface=evaluator_llm)
    reflector = LLMReflector(llm_interface=evaluator_llm)
    memory = SimpleMemory(max_size=3)
    
    agent = ReflexionAgent(
        actor=actor,
        evaluator=evaluator,
        reflector=reflector,
        memory=memory,
        max_trials=3,
        uncertainty_policy="accept"
    )
    
    task = "What is 15% of Apple's (AAPL) current stock price, and is it more or less than $50?"
    result = agent.run(task=task)
    
    return result

def print_summary(results):
    print("\n\n")
    print("="*100)
    print(f"{'AGENT':<15} | {'TASK TYPE':<15} | {'STATUS':<10} | {'TIME':<8} | {'STEPS/TRIALS':<15} | {'RESULT START'}")
    print("-" * 100)
    
    metrics = [
        ("ReAct", "Simple Math", results["test1"]),
        ("Reflexion", "Simple Math", results["test2"]),
        ("ReAct", "Finance", results["test3"]),
        ("Reflexion", "Finance", results["test4"]),
    ]
    
    for agent_name, task_type, (data, duration) in metrics:
        status = "✅ " + data.get('status', 'unknown') if 'error' not in data.get('status', '') else "❌ " + data.get('status')
        time_str = f"{duration:.2f}s"
        
        # Determine Complexity Metric
        if agent_name == "ReAct":
            # Count trajectory steps
            steps = len(data.get('trajectory', []))
            complexity = f"{steps} Steps"
        else:
            # Count Trials
            trials = data.get('metadata', {}).get('trials_taken', 1)
            reflections = len(data.get('metadata', {}).get('final_reflections', []))
            complexity = f"{trials} Try / {reflections} Refl"

        final_ans = str(data.get('final_answer', 'No Answer'))[:30].replace("\n", " ") + "..."

        print(f"{agent_name:<15} | {task_type:<15} | {status:<10} | {time_str:<8} | {complexity:<15} | {final_ans}")
    print("="*100)
    print("\n")

if __name__ == "__main__":
    # Container for results
    results = {}
    
    try:
        results["test1"] = test_react_simple()
    except Exception as e:
        logger.error(f"Test 1 Failed: {e}")
        results["test1"] = ({"status": "error", "final_answer": str(e)}, 0.0)

    try:
        results["test2"] = test_reflexion_simple()
    except Exception as e:
        logger.error(f"Test 2 Failed: {e}")
        results["test2"] = ({"status": "error", "final_answer": str(e)}, 0.0)

    try:
        results["test3"] = test_react_multipart()
    except Exception as e:
        logger.error(f"Test 3 Failed: {e}")
        results["test3"] = ({"status": "error", "final_answer": str(e)}, 0.0)

    try:
        results["test4"] = test_reflexion_multipart()
    except Exception as e:
        logger.error(f"Test 4 Failed: {e}")
        results["test4"] = ({"status": "error", "final_answer": str(e)}, 0.0)

    # Print Comparison Table
    print_summary(results)