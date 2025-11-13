# AI Agent Framework - ReAct Architecture (V1)

A production-grade AI agent system implementing the ReAct (Reasoning + Acting) architecture from first principles. Built with modularity, extensibility, and cost-efficiency in mind.

---

## Project Overview

**What**: Autonomous AI agent that can reason about tasks, use external tools, and adapt strategies based on real-time feedback.

**Why**: Bridge the gap between LLM reasoning (Chain-of-Thought) and real-world action execution (tool use) to solve complex, multi-step problems requiring external data.

**Status**: Day 1 Complete - Sequential ReAct Agent (Production-Ready V1)

---

## Architecture

### Core Flow
```
┌─────────────────────────────────────────────────────────────┐
│                     REACT AGENT LOOP                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │   User Query     │
                   └────────┬─────────┘
                            │
                            ▼
          ┌─────────────────────────────────────┐
          │      Prompt Builder                 │
          │  • System instructions              │
          │  • Tool descriptions                │
          │  • Task + History                   │
          └────────────┬────────────────────────┘
                       │
                       ▼
          ┌─────────────────────────────────────┐
          │         LLM (Brain)                 │
          │  • Reasoning (Thought)              │
          │  • Planning (Action)                │
          │  • Input generation                 │
          └────────────┬────────────────────────┘
                       │
                       ▼
          ┌─────────────────────────────────────┐
          │         Parser                      │
          │  Extract: Thought, Action, Input    │
          └────────────┬────────────────────────┘
                       │
                       ├──────> Is Action "Finish"? ──> Return Answer
                       │
                       ▼
          ┌─────────────────────────────────────┐
          │      Tool Execution                 │
          │  • Calculator                       │
          │  • Search                           │
          │  • Web Browse                       │
          │  • Stock Price API                  │
          └────────────┬────────────────────────┘
                       │
                       ▼
          ┌─────────────────────────────────────┐
          │      Observation                    │
          │  Real-world result from tool        │
          └────────────┬────────────────────────┘
                       │
                       └──> Add to History ──> Loop Back to LLM
```

### Key Components

**Orchestrator** (`src/agent/orchestrator.py`)
- Manages the Thought-Action-Observation (TAO) loop
- Enforces step limits (circuit breaker pattern)
- Coordinates between prompt builder, LLM, parser, and tools

**Prompt Builder** (`src/agent/prompt_builder.py`)
- Constructs dynamic prompts with task, tools, and history
- Implements strategic guidelines (error recovery, tool usage patterns)
- Manages conversation state

**Parser** (`src/utils/parser.py`)
- Extracts structured output from LLM's freeform text
- Handles edge cases (malformed output, missing fields)
- Robust regex-based extraction

**Tool System** (`src/tools/`)
- **Base Class** (`base.py`): Common interface for all tools
- **General Tools** (`general_tools.py`): Calculator, Search
- **Web Tools** (`web_tools.py`): Web browsing with BeautifulSoup
- **Financial Tools** (`financial_tools.py`): Stock price API (yfinance)

**LLM Interface** (`src/utils/llm_interface.py`)
- Abstraction over LLM API calls (Ollama, OpenAI-compatible)
- Handles errors, retries, and response extraction

---

## Quick Start

### Installation
```bash
# Clone repository
git clone <repo-url>
cd ai-agent-framework

# Install dependencies
pip install -r requirements.txt

# Ensure Ollama is running (or configure your LLM endpoint)
ollama serve
```

### Run Agent
```bash
python run_agent.py
```

### Example Usage
```python
from src.agent.orchestrator import react_orchestrator
from src.tools import get_all_tools

task = "What's 15% of Apple's current stock price?"
tools = get_all_tools()

answer = react_orchestrator(task, tools, max_steps=10)
print(answer)
# Output: "15% of Apple's stock price ($275.25) is $41.29."
```

---

## Testing

### Run Unit Tests
```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_parser.py
pytest tests/tools/test_calculator.py

# With coverage
pytest --cov=src tests/
```

### Test Coverage (Day 1)
- ✅ Parser: Edge cases (malformed output, missing fields)
- ✅ Calculator: Currency symbols, commas, complex expressions
- ✅ Search: Query formatting, result parsing
- ✅ Web Browse: URL validation, content extraction
- ✅ LLM Interface: Error handling, response validation

### Manual Test Cases
```bash
# Test 1: Simple calculation (no external data)
Task: "What's 15% of 200?"
Expected: 2 steps (Calculate → Finish)

# Test 2: Multi-tool coordination
Task: "What's 15% of Apple's current stock price?"
Expected: 3 steps (Get stock price → Calculate → Finish)

# Test 3: Complex research
Task: "What's the weather on Mars right now?"
Expected: 4-6 steps (Search → Browse → Extract → Finish)
```

---

## Tool System

### Available Tools (Day 1)

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| **Calculator** | Mathematical expressions | `200 * 0.15` |
| **Search** | Web search (DuckDuckGo) | `"Apple stock price"` |
| **web_browse** | Read webpage content | `"https://example.com"` |
| **get_stock_price** | Real-time stock data | `"AAPL"` |
| **Finish** | Return final answer | `"The answer is 42"` |

### Adding New Tools

1. **Create tool file** in `src/tools/`
```python
from src.tools.base import Tool

def my_tool_function(input_data: str) -> str:
    # Your logic here
    return result

my_tool = Tool(
    name="MyTool",
    description="What this tool does and when to use it",
    function=my_tool_function
)
```

2. **Register in orchestrator**
```python
from src.tools.my_tool import my_tool

tools = [calculator, search, my_tool, finish]
```

3. **Tool will auto-format** for LLM prompt

### Tool Design Principles

✅ **Single Responsibility**: Each tool does ONE thing well  
✅ **Composability**: Tools can be chained (Search → Browse)  
✅ **Robustness**: Handle errors gracefully with helpful messages  
✅ **Self-Documenting**: Clear descriptions for LLM understanding  

---

## Performance & Cost

### Typical Query Costs (GPT-4 pricing)

| Task Type | Steps | Tokens | Cost |
|-----------|-------|--------|------|
| Simple Calc | 2 | ~1,500 | $0.05 |
| Stock Query | 3 | ~2,500 | $0.08 |
| Research Task | 5-7 | ~4,000 | $0.12 |

### Optimization Strategies (V1)

1. **Observation Truncation**: Limit web content to 400 chars (99% cost reduction on large pages)
2. **Strategic Guidelines**: Prevent unnecessary tool calls (error recovery patterns)
3. **Tool Specialization**: Use domain-specific tools (stock API vs generic search)

### Known Bottlenecks (Roadmap)

⚠️ **Prompt Reconstruction**: Full system prompt rebuilt every step (V2 priority)  
⚠️ **History Growth**: Context size increases linearly (message-based architecture needed)  
⚠️ **No Caching**: Repeated questions re-execute tools (caching layer planned)  

---

## Key Features (Day 1)

### Production-Ready Elements

✅ **Modular Architecture**: Clean separation (agent, tools, utils)  
✅ **Extensible Tool System**: Add new tools without touching core  
✅ **Structured Logging**: Trace agent reasoning with Python logging  
✅ **Error Recovery**: Strategic guidelines for handling failures  
✅ **Robust Parsing**: Handles malformed LLM output gracefully  
✅ **Unit Tests**: Core components covered  

### Prompt Engineering Innovations

**Strategic Guidelines**:
- Multi-step research patterns (Search → Browse workflow)
- Error recovery logic (try alternatives before re-searching)
- Content verification (prevent goal drift)
- Self-evaluation (quality checks before Finish)

**Example**:
```
STRATEGIC GUIDELINES:
1. Start with 'Search' to get overview and identify URLs
2. Use 'web_browse' to dig into promising URLs
3. If web_browse fails, try next URL from search results
4. Only re-search if all URLs exhausted
5. Verify content relevance before using it
```

---

## Roadmap

### Day 2: Architecture Comparison
- [ ] Implement Act-Only pattern (no reasoning)
- [ ] Implement Reflexion (self-correction)
- [ ] Benchmark: ReAct vs Act-Only vs Reflexion
- [ ] Refactor to message-based prompting (84% cost reduction)

### Day 3: Advanced Architectures
- [ ] Hybrid patterns (CoT + ReAct routing)
- [ ] Memory systems (episodic, semantic, procedural)
- [ ] Multi-agent coordination

### Day 4: Tool Abstraction Layer
- [ ] Retry logic with exponential backoff
- [ ] Rate limiting and circuit breakers
- [ ] Tool result caching
- [ ] Dynamic tool selection (context-aware)

### Day 5: Production Hardening
- [ ] Automated test suite (integration tests)
- [ ] Benchmarking framework
- [ ] Cost tracking and optimization
- [ ] Deployment configuration

---

## Known Issues & Limitations

### V1 Limitations

**Prompt Management**:
- System instructions regenerated every step (wasteful)
- History grows linearly (context window risk)
- **Impact**: 5-10x higher token costs than necessary
- **Fix Planned**: Message-based architecture (Day 2)

**Observation Handling**:
- Crude truncation (first 400 chars)
- May miss important info buried in content
- **Impact**: Reduced accuracy on complex pages
- **Fix Planned**: Intelligent extraction (embeddings, summarization)

**Tool Coordination**:
- No caching (repeated queries re-execute)
- No parallel execution (sequential only)
- **Impact**: Slower, more expensive on repeated queries
- **Fix Planned**: Cache layer + async tools (Day 4)

### Current Workarounds

✅ Truncate observations to 400 chars (prevents context overflow)  
✅ Strategic guidelines in prompt (error recovery patterns)  
✅ Specialized tools (stock API vs generic search)  

---

## Learning Resources

### Papers Implemented
- **ReAct**: [Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)

### Design Patterns Used
- **Circuit Breaker**: Max step limits prevent infinite loops
- **Strategy Pattern**: Pluggable tools with common interface
- **Builder Pattern**: Dynamic prompt construction
- **Observer Pattern**: Logging framework for debugging

---

## Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Document public functions
- Write unit tests for new tools

### Pull Request Process
1. Create feature branch
2. Add tests for new functionality
3. Update README if adding tools/features
4. Ensure all tests pass

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built following the ReAct paper methodology with production engineering best practices from FAANG systems design.

---

## Contact

- **GitHub Profile**: [ria-19](https://github.com/ria-19)

Feel free to open an issue for any bugs or feature requests

---

**Last Updated**: Day 1 Complete (Sequential ReAct V1)  
**Next Milestone**: Day 2 - Architecture Comparison & Message-Based Refactor