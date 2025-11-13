class PromptBuilder:
    def __init__(self, task, tools, max_obs_length=400):
        self.task = task
        self.tools = tools
        self.history = []  # Stores (thought, action, observation) tuples
        self.max_obs_length = max_obs_length
      
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
        """Builds the first prompt with task, tools, and formatting rules."""
        
        tool_names = ", ".join(self._get_tool_names())

        return f"""You are an agent that solves tasks step-by-step using available tools.

        Task: {self.task}

        Available tools:
        {self._format_tools()}
        
        STRATEGIC GUIDELINES:
        1. Your primary goal is to gather specific, detailed information. Start with 'Search' to get an overview and identify promising URLs. Then, use 'web_browse' to dig into those URLs.
        2. **Error Recovery:** If the 'web_browse' tool fails on a URL (e.g., returns an error or forbidden access), DO NOT immediately search again. Instead, review your last 'Search' results and try the next most promising URL. Only use 'Search' again if all promising URLs have been exhausted.
        3. **Content Verification:** After browsing a page, verify that the content is relevant to the original task. For example, if the task is about the planet Mars, ensure the page content is not about a city named Mars.
        
        CRITICAL RULES FOR FORMATTING:
        1. Output EXACTLY ONE action per response.
        2. After writing "Action Input:", STOP IMMEDIATELY. Do not write anything else.
        3. NEVER write "Observation:" yourself; the system will provide it.
        4. NEVER write multiple Thought/Action pairs in one response.
        
        QUALITY CHECKS BEFORE USING "Finish":
        - Do I have specific, concrete data to answer the question (e.g., numbers, names, specific facts)?
        - Is my information free from placeholders like "° C" or error messages?
        - If the answer to either of the above is no, I MUST try a different approach (browse a different URL, refine my search query, or use another tool).
        
        Format:
        Thought: [your reasoning about the NEXT step only]
        Action: [choose ONE: {tool_names}]
        Action Input: [input for that action]

        CORRECT example (one action, stops immediately):
        Thought: I need to find the current temperature in Paris
        Action: Search
        Action Input: Paris weather today

        WRONG examples:
        Thought: I need weather data
        Action: Search
        Action Input: weather
        Observation: [Weather is ...]  ← NEVER write this yourself!

        Thought: First I'll search
        Action: Search
        Action Input: weather
        Thought: Then I'll browse  ← NEVER plan multiple steps!

        Thought: The observation shows "Temp: ° C" which is empty, so I'll finish anyway
        Action: Finish  ← NEVER finish with incomplete data!

        Now solve this task. Think carefully and take one step at a time.
        """
    
    def add_step(self, thought, action, observation):
        """Add T-A-O to history"""
        truncated_obs = self._truncate_observation(str(observation))
        self.history.append((thought, action, truncated_obs))
    
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
    
    def _get_tool_names(self) -> list[str]:
        """Returns a simple list of tool names."""
        
        return [tool.name for tool in self.tools]
   
    def _format_tools(self):
        """Format tool descriptions for LLM"""
        
        return "\n".join([tool.format_for_prompt() for tool in self.tools])
           
    def _truncate_observation(self, obs: str) -> str:
        """
        Intelligently truncate observations to save tokens while preserving quality.
        
        Strategies:
        1. Keep first portion (usually contains key info)
        2. Keep last portion (often has conclusions)
        3. Add truncation marker
        """
        if len(obs) <= self.max_obs_length:
            return obs
        
        # Take 70% from start, 30% from end
        start_chars = int(self.max_obs_length * 0.7)
        end_chars = self.max_obs_length - start_chars - 20  # Reserve 20 for marker
        
        truncated = (
            obs[:start_chars] + 
            "\n...[truncated]...\n" + 
            obs[-end_chars:]
        )
        return truncated