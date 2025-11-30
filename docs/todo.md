Version 3: The "Doer" Agent
The primary goal of V3 is to give the agent the ability to act upon and modify a user's digital environment in a secure and controlled manner.
Epic 1: Foundational Enhancements (Prerequisites for a "Doer" Agent)
This foundational work must be completed before we can safely add powerful, interactive tools.
1.1: Implement Security Sandbox Environment
Description: To safely execute code and modify files, the agent's actions MUST be confined to an isolated environment. This is a non-negotiable security prerequisite.
Implementation Details:
Utilize Docker to create a lightweight, ephemeral container for each task.
The File System and Code Interpreter tools will execute exclusively within this container.
Define a specific, mounted "workspace" directory (e.g., /agent_workspace) that the agent can read from and write to, preventing any access to the host file system.
1.2: Architect Two-Stage Tool Selection
Description: As the number of tools grows, the agent's prompt will become too large and the LLM's tool selection accuracy will decrease. We need a pre-filtering mechanism.
Implementation Details:
Create a "Tool Router" function that uses a fast, cheap LLM (e.g., groq/llama-3.1-8b-instant) or a vector embedding search.
The router will take the user's task and the full list of tools and produce a "shortlist" of the 5-10 most relevant tools.
The main Actor's prompt will only receive this shortlisted set of tools, improving efficiency and accuracy.
1.3: Implement Persistent Memory (Vector DB)
Description: Give the agent a long-term memory to recall user preferences, key facts, and important information across different sessions.
Implementation Details:
Create remember(fact_to_store) and recall(query) tools.
Use a local vector database library like ChromaDB or FAISS for simplicity and speed.
The remember tool will create an embedding of the fact and store it.
The recall tool will perform a similarity search to retrieve the most relevant stored facts.
Epic 2: Core Productivity Toolkit
With the sandbox in place, we can now safely add tools that interact with the user's environment.
2.1: Implement File System I/O Tools
Description: Allow the agent to read, write, and list files within its secure workspace, enabling tasks like report generation, data analysis, and code creation.
Implementation Details:
Create read_file(path), write_file(path, content), and list_files(directory) tools.
All file paths MUST be validated to be within the sandboxed /agent_workspace.
2.2: Implement Code Interpreter Tool
Description: Grant the agent a "superpower" to perform complex data analysis, generate plots, and run simulations by executing Python code.
Implementation Details:
Create an execute_python_code(code_string) tool.
The tool will execute the code within the Docker sandbox.
It MUST capture and return all outputs (stdout, stderr) and the final result as its observation.
2.3: Implement Human-in-the-Loop Tool
Description: Provide a critical "safety valve" that allows the agent to pause and ask for clarification when faced with an ambiguous or potentially risky task.
Implementation Details:
Create an ask_human_for_clarification(question) tool.
When called, the agent's execution loop will pause and print the question to the user.
The system will wait for the user's response, which will be returned as the observation.
Version 4: The "Connected" Platform
The goal of V4 is to transform the agent from a command-line script into a robust, user-friendly platform that integrates with external services.
Epic 3: Platformization & User Experience
3.1: Asynchronous Task Execution (Job Queue)
Description: Decouple task submission from execution so users are not blocked waiting for long-running tasks.
Implementation Details:
Use a task queue library like Celery with a Redis message broker.
User requests will add a job to the queue, which is processed by a separate background worker.
3.2: Stateful Sessions & Database
Description: Persist all agent sessions, including the initial task, full trajectory, and final result, for auditing and review.
Implementation Details:
Use a database like SQLite (for simplicity) or PostgreSQL (for production).
Create a "Session" model to store all relevant data for each agent run.
3.3: Web Interface (UI)
Description: Create an intuitive front-end to make the agent accessible to non-technical users.
Implementation Details:
Use a framework like Streamlit for rapid prototyping or React/Vue for a full application.
The UI will allow users to submit tasks, view a dashboard of past/present sessions, and watch an agent's trajectory in real-time.
3.4: Configuration Management
Description: Externalize all hard-coded settings to make the platform flexible and easy to configure.
Implementation Details:
Use a config.yaml or .env file to manage model names, API keys, enabled tools, and sandbox settings.
3.5: Pre-run Plan & Approval (Trust & Safety)
Description: Build user trust by having the agent present its plan for approval before executing any potentially sensitive actions.
Implementation Details:
Before execution, the agent will generate a high-level plan and list the tools it will use.
The UI will display this plan and require the user to click "Approve" before the agent proceeds.
3.6: Easy Deployment (Containerization)
Description: Package the entire multi-component platform for easy distribution and setup.
Implementation Details:
Create a docker-compose.yml file to define and link all services (web UI, agent worker, Redis, etc.).
Allow users to launch the entire platform with a single docker-compose up command.
Epic 4: Advanced Integrations & Power Tools
4.1: Implement Tier-2 Dynamic Web Reader
Description: Add a powerful browsing tool that can handle modern, JavaScript-heavy websites.
Implementation Details:
Create a dynamic_web_reader tool using a headless browser library like Playwright.
Update the agent's prompt to teach it a tiered strategy: start with the cheap tool, and escalate to the expensive tool only on failure.
4.2: Implement Productivity API Integrations
Description: Connect the agent to a user's daily applications.
Implementation Details:
google_calendar: create_event, find_available_time.
email: send_email.
slack: send_slack_message.
Version 5 and Beyond: The "Autonomous" Agent
This is a forward-looking vision for future development.
Hierarchical Agent Systems: Implement a "Manager" agent that can decompose large tasks and delegate sub-tasks to specialized "Worker" agents.
Generic API Client: A single http_request tool that allows the agent to learn how to use any REST API by reading its documentation.
Continuous Self-Improvement: An agent that can reflect on its successful trajectories (not just failures) to optimize its own internal strategies and heuristics over time.


        # 5. The Rules of Engagement: Cognitive Forcing and Negative Constraints
        # This is the most critical section for preventing common failure modes.
        rules_of_engagement = (
            "<rules>\n"
            "--- CORE STRATEGIC DIRECTIVES ---\n"
            "1.  **Analyze and Decompose**: Before acting, critically analyze the <task> and break it down into a sequence of smaller, logical steps. Always have a plan.\n"
            
            "2.  **Tiered Web Strategy (CRITICAL)**: You have two web browsing tools. You MUST use them in this order:\n"
            "    a. **Tier 1 (Default):** For any web-based question, ALWAYS start with the `inquisitive_web_browse` tool. It is fast, cheap, and effective for most websites. Do not trust search snippets alone; use this tool to get the real content.\n"
            "    b. **Tier 2 (Escalation):** Only if `inquisitive_web_browse` returns an error or 'Information not found', and you have strong reason to believe the answer exists on that page (e.g., it's a complex web application), you MUST escalate and try a second time using the `dynamic_web_reader` tool on the same URL. Do not use this tool as your first choice.\n"

            "3.  **Goal-Oriented Synthesis (CRITICAL)**: Before using the `finish` action, you MUST re-read the original <task> and review ALL previous `Observations`. Your final answer must be a complete synthesis of all gathered information, addressing every single part of the user's request. Do not fall victim to Recency Bias (only focusing on the last observation).\n"
            
            "\n--- OPERATIONAL PRINCIPLES ---\n"
            "4.  **Cyclical Reasoning**: Your life is a cycle of Thought -> Action -> Observation. After each observation, re-evaluate your plan and decide on the next logical step.\n"
            f"5.  **Strict Tool Adherence**: You MUST use one of the tools listed in the <tools> section: [{tool_names}]. Do not hallucinate or invent tools.\n"
            
            "\n--- FORMATTING PURITY (CRITICAL) ---\n"
            "6.  **Output Format**: Your response MUST strictly adhere to the following format. There must be no other text, comments, or explanations before or after this block.\n"
            "    Thought: [Your reasoning, plan, and self-correction. Be concise.]\n"
            "    Action: [A single tool name from the list]\n"
            "    Action Input: [The direct input for the chosen tool. For tools requiring JSON, this must be a valid, single-line JSON string.]\n"
            
            "7.  **Negative Constraints**: \n"
            "    a. **STOP IMMEDIATELY** after the `Action Input`. Your response must end after that line.\n"
            "    b. You MUST NOT write `Observation:` or `[SYSTEM FEEDBACK]` yourself. The system provides that.\n"
            "    c. You MUST NOT output more than one Thought/Action/Input block per turn.\n"
            "</rules>"
        )