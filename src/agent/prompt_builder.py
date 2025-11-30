import logging
import json

from typing import List, Dict, Any
from src.components import EvaluationReport, EvaluationStatus

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    A stateless utility for building message-based prompts for the agent.
    """

    @staticmethod
    def build_actor_prompt(task: str, tools: List[Any], trajectory: List[Dict[str, Any]], reflections: List[str] = None) -> List[Dict[str, str]]:
        """
        Builds the prompt for the ReAct agent (the Actor) as a message list.
        Args:
            task: User's task
            tools: Available tools
            trajectory: Current attempt history (for continuation)
            context: Additional context (e.g., reflections from past attempts)
        
        Returns:
            List of Dictionaries 
        """
        # Extract tool names
        tool_names_list = [t.name for t in tools]
        search_tool_name = next((name for name in tool_names_list if 'search' in name.lower()), 'search')
        browse_tool_name = next((name for name in tool_names_list if 'inquisitive' in name.lower()), 'web_browse') 
        finish_tool_name = next((name for name in tool_names_list if 'finish' in name.lower()), 'finish')
        
        tool_names_str = ", ".join([f"`{name}`" for name in tool_names_list])
        tools_definition = PromptBuilder._format_tools_to_string(tools)

        # ============================================================
        # SYSTEM PROMPT CONSTRUCTION
        # ============================================================
        
        system_role = (
            "You are an autonomous reasoning agent that solves tasks by using tools. "
            "You think step-by-step, verify information before concluding, and follow the exact response format."
        )
        
        task_section = (
            "<task>\n"
            f"{task}\n"
            "</task>"
        )
        
        # Reflections from previous failed attempts
        reflections_section = ""
        if reflections:
            reflection_items = "\n".join(f"  • {r}" for r in reflections)
            reflections_section = (
                "\n<past_failures>\n"
                "You have attempted this task before. Learn from these mistakes:\n"
                f"{reflection_items}\n"
                "</past_failures>"
            )
        
        tools_section = (
            f"<tools>\n"
            f"{tools_definition}\n"
            "</tools>"
        )
        
        # Core strategy rules
        strategy_section = (
            "<reasoning_strategy>\n"
            "**Step 1: Decompose the Task**\n"
            "Break down the user's request into logical sub-tasks. Identify what information you need.\n\n"
            
            "**Step 2: Information Gathering Protocol**\n"
            f"  • Use `{search_tool_name}` to discover relevant sources (returns URLs and snippets)\n"
            "   • NEVER trust search snippets alone - they are often outdated or incomplete\n"
            f"  • ALWAYS verify by browsing: Use `{browse_tool_name}` with the URL and a specific question\n"
            f"  • Only use `dynamic_web_reader` if `{browse_tool_name}` fails (JavaScript-heavy sites)\n\n"
            
            "**Step 3: CRITICAL RULES FOR Action Input**\n"
            "   1. **NO CONVERSATIONAL TEXT**: The 'Action Input' must contain ONLY the arguments for the tool. Do NOT add notes, explanations, or 'I will now...' before or after the input."
            "   2. **NO MARKDOWN**: Do NOT wrap the input in markdown code blocks (like ```json or ```).\n"
            "   3. **RAW CONTENT**: "
            "       - If the tool requires JSON, output **raw JSON only** (e.g., {{'key': 'value'}}).\n"
            "       - If the tool requires a string, output **the raw string only**.\n"
            "       - Any extra text will cause the system parser to CRASH\n\n "
                       
            "**Step 4: Synthesis & Completion**\n"
            f"Review all observations. Ensure you've answered the COMPLETE task. Use `{finish_tool_name}` with your final answer.\n"
            "</reasoning_strategy>"
        )
        
        
        # Output format specification
        format_section = (
            "<output_format>\n"
            "You must respond using EXACTLY this structure:\n\n"
            "```\n"
            "Thought: [your reasoning about what to do next]\n"
            f"Action: [one tool name from: {tool_names_str}]\n"
            "Action Input: [the input value for the tool]\n"
            "```\n\n"
            "**CRITICAL FORMATTING RULES:**\n"
            "1. Output ONLY these three lines: Thought, Action, Action Input\n"
            "2. The 'Action Input' line contains ONLY the input value - no extra text\n"
            "3. STOP immediately after the Action Input line\n"
            "4. Do NOT write 'Observation:' - the system will add it automatically\n"
            "5. Do NOT add explanatory comments after your Action Input\n"
            "6. For JSON inputs, write valid JSON on a single line\n"
            "</output_format>"
        )
        
        # Examples showing correct behavior
        examples_section = (
            "<examples>\n"
            "Example 1: Simple tool call\n"
            "---\n"
            "Thought: I need to get NVIDIA's current stock price.\n"
            "Action: get_stock_price\n"
            "Action Input: NVDA\n"
            "---\n"
            "Observation: Current price of NVDA is $142.50\n\n"
            
            "Example 2: JSON input\n"
            "---\n"
            "Thought: I found a relevant URL. I'll browse it to extract specific information.\n"
            f"Action: {browse_tool_name}\n"
            'Action Input: {"url": "https://example.com/article", "question": "What is the latest version number?"}\n'
            "---\n"
            "Observation: The latest version is 2.5.0\n\n"
            
            "Example 3: Calculation\n"
            "---\n"
            "Thought: I have the stock price ($142.50). Now I'll calculate 25% of it.\n"
            "Action: calculator\n"
            "Action Input: 0.25 * 142.50\n"
            "---\n"
            "Observation: 35.625\n\n"
            
            "Example 4: Search then verify workflow\n"
            "---\n"
            "Thought: I'll search for Python's latest version.\n"
            f"Action: {search_tool_name}\n"
            "Action Input: Python latest stable version\n"
            "---\n"
            "Observation: [Snippet suggests 3.12] URL: https://python.org/downloads\n\n"
            "Thought: The snippet suggests 3.12, but I must verify from the official source.\n"
            f"Action: {browse_tool_name}\n"
            'Action Input: {"url": "https://python.org/downloads", "question": "What is the current stable version number?"}\n'
            "---\n"
            "Observation: Python 3.12.1 is the latest stable release.\n"
            "</examples>"
        )
        
        # Anti-patterns to avoid
        anti_patterns_section = (
            "<common_mistakes>\n"
            "❌ WRONG: Adding explanatory text after input\n"
            "Action Input: NVDA (I will now wait for the result)\n\n"
            
            "✓ CORRECT: Just the input value\n"
            "Action Input: NVDA\n\n"
            
            "---\n"
            "❌ WRONG: Writing the Observation yourself\n"
            "Action Input: 0.25 * 142.50\n"
            "Observation: [don't write this]\n\n"
            
            "✓ CORRECT: Stop after Action Input\n"
            "Action Input: 0.25 * 142.50\n"
            "[system adds observation automatically]\n\n"
            
            "---\n"
            "❌ WRONG: Trusting search snippets\n"
            "Thought: The search says the price is $878. I'll use that.\n\n"
            
            "✓ CORRECT: Verify with browse tool\n"
            "Thought: The search suggests $878, but I need to verify this from the actual source.\n"
            "</common_mistakes>"
        )
        
        # Final instruction
        final_instruction = (
            "\n<instruction>\n"
            "Now begin solving the task. Start by analyzing what needs to be done, then take your first action.\n"
            "Remember: Output ONLY Thought/Action/Action Input, then stop.\n"
            "</instruction>"
        )
        
        # Assemble complete system message
        system_content = "\n".join([
            system_role,
            task_section,
            reflections_section,
            tools_section,
            strategy_section,
            format_section,
            examples_section,
            anti_patterns_section,
            final_instruction
        ])
        
        messages = [{"role": "system", "content": system_content}]

        # ============================================================
        # CONVERSATION HISTORY
        # ============================================================
        # Convert trajectory into alternating assistant/user messages
        for turn in trajectory:
            # What the agent did
            assistant_msg = (
                f"Thought: {turn['thought']}\n"
                f"Action: {turn['action']}\n"
                f"Action Input: {turn['action_input']}"
            )
            messages.append({"role": "assistant", "content": assistant_msg})
            
            # What happened (observation)
            user_msg = f"Observation: {turn['observation']}"
            messages.append({"role": "user", "content": user_msg})

        return messages

    @staticmethod
    def build_evaluator_prompt(task: str, actor_result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Builds prompt for LLM to evaluate agent's attempt.
        
        Args:
            task: Original goal
            answer: Agent's final answer
            trajectory: Agent's full reasoning trace
        
        Returns:
        Builds evaluation prompt with sophisticated confidence calibration and partial success detection        
        """
        trajectory = actor_result.get("trajectory", [])
        answer = actor_result.get("final_answer", "")
        actor_status = actor_result.get("status", "unknown")
        
        # --- SYSTEM MESSAGE: The Evaluator's "Constitution" ---
        system_content = """
            You are an expert AI evaluator. Your role is to judge whether an AI agent successfully completed its assigned task by providing a structured JSON report.

            # EVALUATION FRAMEWORK

            ## Status Definitions
            - **FULL_SUCCESS**: The agent completely fulfilled all requirements of the task. The answer is correct, complete, and directly addresses the user's intent.
            - **PARTIAL_SUCCESS**: The agent fulfilled some but not all requirements. For multi-part tasks, some sub-goals were achieved. The answer is partially correct or incomplete.
            - **FAILURE**: The agent did not fulfill the task requirements. The answer is incorrect, incomplete, or irrelevant.

            ## Critical Evaluation Rules
            1.  **Focus on Correctness**: Your primary judgment must be on whether the answer satisfies the core requirements of the task.
            2.  **Permit Verbosity**: Do NOT penalize the agent for providing extra, correct information unless the task explicitly demanded conciseness (e.g., "answer in one word").
            3.  **Multi-Part Tasks**: If the task has multiple implicit sub-goals, you must decompose them in your reasoning.
            4.  **Completion Over Efficiency**: Judge the final answer's correctness, not the efficiency of the agent's process (unless efficiency was a specific task requirement).

            ## Confidence Calibration (CRITICAL)
            Your confidence score must be a reasoned conclusion, not a guess. To ensure this, you must complete the required `confidence_reasoning` field in your JSON output by following this template: "I am this confident because... The primary risk or uncertainty in my evaluation is..."

            **Confidence Guidelines**:
            - **0.95-1.0**: The answer is objectively verifiable as correct.
            - **0.80-0.95**: The answer appears correct based on strong evidence, but minor uncertainty exists.
            - **0.60-0.80**: The answer is plausible but has notable uncertainties.
            - **Below 0.60**: High uncertainty; make a definitive judgment but flag the low confidence.

            # YOUR TASK
            You will be given the user's task, the agent's final answer, and its execution context. Follow the thinking process below to construct your JSON response.

            **Thinking Process:**
            1.  **Task Decomposition**: (For multi-part tasks) What are the distinct sub-goals?
            2.  **Correctness Check**: Does the agent's answer satisfy each requirement?
            3.  **Status Determination**: Based on the check, choose FULL_SUCCESS, PARTIAL_SUCCESS, or FAILURE.
            4.  **Confidence Reasoning**: Construct the justification for your confidence score.

            **Important**: Return ONLY the JSON object, with no additional text or explanations.
            **Output your evaluation in this EXACT JSON format**:
            ```json
            {{
                "status": "FULL_SUCCESS" | "PARTIAL_SUCCESS" | "FAILURE",
                "reason": "A clear, specific explanation of your judgment. For multi-part tasks, state 'X of Y sub-goals completed.' For PARTIAL_SUCCESS or FAILURE, identify what was missing or incorrect.",
                "confidence": 0.0-1.0,
                "confidence_reasoning": "I am this confident because... [and if < 1.0] The primary risk is...",
                "metadata": {{}}
            }}
            """

        # --- USER MESSAGE: The Specific "Work Ticket" ---
        # This part changes with every evaluation.
        trajectory_summary = f"Agent took {len(trajectory)} steps to reach this answer."
        user_content = f"""
            # TASK GIVEN TO AGENT
            {task}

            # AGENT'S FINAL ANSWER
            {answer}

            # AGENT'S EXECUTION CONTEXT
            - **Final Status**: {actor_status}
            - **Execution Length**: {trajectory_summary}

            ---
            # YOUR EVALUATION (JSON ONLY)
            """

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

    @staticmethod
    def build_reflector_prompt(task: str, trajectory: List[Dict], eval_report: EvaluationReport) -> List[Dict]:
        """
        Builds the appropriate reflection prompt based on the evaluation status.
        This acts as a router to the correct specialized prompt.
        """
        status = eval_report.status

        if status == EvaluationStatus.PARTIAL_SUCCESS:
            logger.debug("Building a 'Preserve & Correct' prompt for PARTIAL_SUCCESS.")
            return PromptBuilder._build_partial_success_prompt(task, trajectory, eval_report)
        else: # Default to FAILURE
            logger.debug("Building a 'Find the Flaw' prompt for FAILURE.")
            return PromptBuilder._build_failure_prompt(task, trajectory, eval_report)
        
    @staticmethod
    def _build_failure_prompt(task: str, trajectory: List[Dict[str, Any]], eval_report: EvaluationReport) -> List[Dict[str, str]]:
        """
        Builds the prompt for reflecting on a complete failure.
        This prompt is designed to force a deep, strategic, root-cause analysis.
        """
        
        system_content = """
            # ROLE: You are a Master Debugger and Root-Cause Analyst.
            # TASK: The AI agent you are mentoring has FAILED a task. Its core strategy was flawed. Your job is to perform a deep root-cause analysis and produce a single, powerful, and generalizable heuristic that will prevent this entire CLASS of error in the future.
            # ANALYSIS FRAMEWORK
            You MUST follow the "Cause, Impact, Heuristic" framework for your analysis:
            1.  **Cause**: What was the single, fundamental, and incorrect assumption in the agent's strategy? Look past the surface-level errors to find the deep, faulty logic.
            2.  **Impact**: How did this flawed assumption lead directly to the agent's failure, as seen in the trajectory?
            3.  **Heuristic**: What is the new, generalizable strategic rule the agent must follow to avoid this entire CLASS of error in the future? This must be an actionable instruction.
            # METADATA: As part of your analysis, populate the metadata field. The 'impact' field should be a concise summary of your detailed 'Impact' analysis above.
            # OUTPUT FORMAT
            You MUST respond ONLY with a valid JSON object in the following format:```json
            {{
                "root_cause_analysis": "The core flawed assumption was...",   
                "actionable_heuristic": "Heuristic: A single, powerful, and generalizable rule.",
                "confidence": 0.0-1.0,
                "metadata": {{"impact": "This led to the agent incorrectly..."}}
            }} 
            """
        user_content = PromptBuilder._create_user_prompt(task, trajectory, eval_report)
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        
    @staticmethod
    def _build_partial_success_prompt(task: str, trajectory: List[Dict], eval_report: EvaluationReport) -> List[Dict]:
        """
        Builds the prompt for reflecting on a partial success.
        This prompt is designed to be surgical, preserving the successful parts of the
        agent's strategy while correcting the specific point of failure.
        """
        
        system_content = """
        # ROLE: You are a Senior AI Agent Troubleshooter.
        # TASK: The agent you are mentoring achieved PARTIAL SUCCESS. Its core strategy is sound, but it failed on a specific sub-task. Your job is to provide a targeted, tactical fix WITHOUT discarding the successful parts of the agent's plan.
        # ANALYSIS FRAMEWORK: You MUST follow the "Cause, Impact, Heuristic" framework, adapted for a tactical problem.
        1.  **Cause**: What was the specific, technical reason for the failure at the exact point it occurred? (e.g., unexpected data format, tool limitation).
        2.  **Impact**: How did this specific error prevent the agent from completing the final part of its otherwise successful plan?
        3.  **Heuristic**: What is a concise, tactical rule the agent should add to its existing strategy to handle this specific exception in the future?
        # METADATA: Populate the metadata field. The 'impact' field should be a concise summary of your detailed 'Impact' analysis.
        # OUTPUT FORMAT: You MUST respond ONLY with a valid JSON object mapping to this schema:
        ```json
            {{
                "root_cause_analysis": "The specific technical error was...",
                "actionable_heuristic": "Heuristic: A targeted rule to fix the specific error.",
                "confidence": 0.0-1.0,
                "metadata": {{"impact": "This prevented the agent from processing the final sub-task because..."}}
            }}
        ```"""
        user_content = PromptBuilder._create_user_prompt(task, trajectory, eval_report)
        return [{"role": "system", "content": system_content}, {"role": "user", "content": user_content}]
    
    @staticmethod    # A helper function to format tools into a string.
    def _format_tools_to_string(tools: List[Any]) -> str:
        """Formats a list of Tool objects into a string for the prompt."""
        if not tools:
            return "You have no tools available."
        return "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])

    @staticmethod
    def _create_user_prompt(task: str, trajectory: List[Dict], eval_report: EvaluationReport) -> str:
        """ A private helper to create the user-facing part of the reflection prompt. """
        
        # Convert metadata to a clean JSON string for the prompt
        metadata_str = json.dumps(eval_report.metadata, indent=2) if eval_report.metadata else "None"    
       
        return (
            f"# TASK ANALYSIS\n\n"
            f"## Original Task\n{task}\n\n"
            f"## Evaluator's Report\n"
            f"- **Verdict**: {eval_report.status.value}\n"
            f"- **Reason**: {eval_report.reason}\n"
            f"- **Confidence**: {eval_report.confidence:.2f}\n\n"
            f"- **Metadata**: {metadata_str}\n\n"
            f"## Agent's Full Trajectory\n"
            f"{PromptBuilder._format_trajectory(trajectory)}\n\n"
            f"---\n# YOUR ANALYSIS (JSON ONLY)"
        )
        
        #         (
        #     "You are an agent that solves tasks step-by-step using available tools.\n\n"
        #     f"Available tools:\n{tools_string}\n\n"
            
        #     "STRATEGIC GUIDELINES:\n"
        #     "1. Your primary task is to gather specific, detailed information. Start with 'Search' to get an overview and identify promising URLs. Then, use 'web_browse' to dig into those URLs.\n"
        #     "2. **Error Recovery:** If the 'web_browse' tool fails on a URL (e.g., returns an error or forbidden access), DO NOT immediately search again. Instead, review your last 'Search' results and try the next most promising URL. Only use 'Search' again if all promising URLs have been exhausted.\n"
        #     "3. **Content Verification:** After browsing a page, verify that the content is relevant to the original task. For example, if the task is about the planet Mars, ensure the page content is not about a city named Mars.\n\n"

        #     "CRITICAL RULES FOR FORMATTING:\n"
        #     "1. Output EXACTLY ONE action per response.\n"
        #     "2. After writing \"Action Input:\", STOP IMMEDIATELY. Do not write anything else.\n"
        #     "3. NEVER write \"Observation:\" yourself; the system will provide it.\n"
        #     "4. NEVER write multiple Thought/Action pairs in one response.\n\n"

        #     "QUALITY CHECKS BEFORE USING \"Finish\":\n"
        #     "- Do I have specific, concrete data to answer the question (e.g., numbers, names, specific facts)?\n"
        #     "- Is my information free from placeholders like \"° C\" or error messages?\n"
        #     "- If the answer to either of the above is no, I MUST try a different approach (browse a different URL, refine my search query, or use another tool).\n\n"

        #     "Format:\n"
        #     "Thought: [your reasoning about the NEXT step only]\n"
        #     f"Action: [choose ONE from: {tool_names}]\n"
        #     "Action Input: [input for that action]\n\n"

        #     "CORRECT example (one action, stops immediately):\n"
        #     "Thought: I need to find the current temperature in Paris\n"
        #     "Action: Search\n"
        #     "Action Input: Paris weather today"
        # )
        
        
        #         if reflections:
        #     reflection_str = "\n".join(f"- {r}" for r in reflections)
        #     system_content += (
        #         "\n\n## Lessons from Past Attempts:\n"
        #         "You have failed before. Remember these lessons to avoid repeating mistakes:\n"
        #         f"{reflection_str}\n"
        #     )
            
        # system_content += f"\nYour main task is: {task}. Now solve this task. Think carefully and take one step at a time."
        
        # messages = [{"role": "system", "content": system_content}]
    
    @staticmethod
    def _format_trajectory(trajectory: List[Dict]) -> str:
        """ A private helper to format the trajectory into a concise, readable string. """
        if not trajectory:
            return "The agent took no actions."
        
        formatted_steps = []
        for i, step in enumerate(trajectory, 1):
            thought = step.get("thought", "N/A")
            action = step.get("action", "N/A")
            action_input = step.get("action_input", "N/A")
            observation = step.get("observation", "N/A")

            if len(observation) > 250:
                observation = observation[:250] + " ... [Truncated]"

            step_str = (
                f"--- Step {i} ---\n"
                f"Thought: {thought}\n"
                f"Action: {action}({repr(action_input)})\n"
                f"Observation: {observation}"
            )
            formatted_steps.append(step_str)
        
        return "\n".join(formatted_steps)