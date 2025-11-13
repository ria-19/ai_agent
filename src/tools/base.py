class Tool:
    """
    Base class for all tools. Encapsulates the tool's data and logic.
    Each tool has a name, description, and a function to execute.
    """
    def __init__(self, name, description, function):
        self.name = name
        self.description = description
        self.function = function
        
    
    def execute(self, args: str) -> str:
        """Executes the tool's function with error handling."""
        # The Finish tool is a special case handled by the orchestrator
        if self.function is None:
            return "No function to execute for this tool."
        try:
            return self.function(args)
        except Exception as e:
            return f"Error executing tool '{self.name}': {e}"
            
    def format_for_prompt(self) -> str:
        """
        Creates the string representation of the tool for the LLM's prompt.
        """
        return f"- {self.name}: {self.description}"