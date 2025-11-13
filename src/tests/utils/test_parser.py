# src/tests/utils/test_parser.py

from src.utils.parser import parse_llm_output

def test_parse_llm_output_happy_path():
    """
    Tests the ideal case where the input string is perfectly formatted
    and contains all expected sections.
    """
    llm_output = """
    Thought: The user wants to know the weather in a city. I should use the search tool for this.
    Action: Search
    Action Input: weather in San Francisco
    """
    expected_thought = "The user wants to know the weather in a city. I should use the search tool for this."
    expected_action = "Search"
    expected_action_input = "weather in San Francisco"
    
    thought, action, action_input = parse_llm_output(llm_output)
    
    assert thought == expected_thought
    assert action == expected_action
    assert action_input == expected_action_input

def test_parse_llm_output_missing_action():
    """
    Tests the critical failure case where the 'Action' keyword is missing.
    The parser should return a specific error message.
    """
    llm_output = "Thought: I am not sure what to do here."
    
    thought, action, action_input = parse_llm_output(llm_output)
    
    assert thought == ""  
    assert action == "Error"
    assert "Could not parse action from" in action_input

def test_parse_llm_output_multiline_action_input():
    """
    Tests that the parser correctly handles multiline 'Action Input',
    which is common for inputs like code snippets or detailed queries.
    """
    llm_output = """
    Thought: I need to write a multi-line json string to a file.
    Action: WriteFile
    Action Input: {
    "name": "test_file.json",
    "content": "{\\"key\\": \\"value\\"}"
    }
    """
    expected_action_input = """{
    "name": "test_file.json",
    "content": "{\\"key\\": \\"value\\"}"
    }"""
    
    _, _, action_input = parse_llm_output(llm_output)
    
    assert action_input == expected_action_input

def test_parse_llm_output_only_action_is_present():
    """
    Tests the case where only the Action is present, without a Thought
    or Action Input. This should still be parsed correctly.
    """
    llm_output = "Action: Finish"
    
    thought, action, action_input = parse_llm_output(llm_output)
    
    assert thought == ""
    assert action == "Finish"
    assert action_input == ""

def test_parse_llm_output_extra_whitespace():
    """
    Tests that leading/trailing whitespace in fields is correctly handled.
    """
    llm_output = """
    Thought:   I should be able to handle extra spaces.  
    Action:  Search  
    Action Input:   some query with spaces  
    """
    expected_thought = "I should be able to handle extra spaces."
    expected_action = "Search"
    expected_action_input = "some query with spaces"

    thought, action, action_input = parse_llm_output(llm_output)
    
    assert thought == expected_thought
    assert action == expected_action
    assert action_input == expected_action_input