# AI Agent Framework – Hybrid Architecture TODOs

> Production-grade AI Agent implementing **ReAct (Reasoning + Acting)** and **Reflexion (Self-Correction)** from first principles.  
> Modular, low-latency, and cost-efficient. Python 3.9+ | MIT License | Status: v0.2 Stable

---

## 🎯 Core Goals
- Build an autonomous agent with:
  - **System 1 (ReAct)**: Fast, reactive execution for simple tasks
  - **System 2 (Reflexion)**: Self-reflective retry for multi-step, high-stakes tasks
- Full control over:
  - Context management
  - Prompt construction
  - Retry & error handling strategies
  - Cost-latency trade-offs
- Maintain transparency and extensibility at every layer

---

## 🏗️ V3+ Development Roadmap

### Core Architecture & Logic (The Agent Brain)
- [ ] **Hierarchical Agent System (Planner-Executor)**
  - Break complex user queries into structured sub-tasks
  - JSON-based plan for Executor
  - Prevents goal drift on long tasks
- [ ] **Dynamic Tool Selection (Tool Router)**
  - Pre-filter tools to top 3-5 relevant ones per task
  - Use cheap LLM or vector search
  - Keeps prompts concise → reduces cost & improves accuracy
- [ ] **Context Manager for Long Conversations**
  - Automatically summarize past messages when approaching context window limit
  - Windowed approach: first message + last N messages + summary of intermediate messages

### Component Upgrades (The Lego Bricks)
- [ ] **V2 Memory – Semantic Archive (VectorMemory)**
  - Persistent, long-term memory for past tasks
  - Use local vector DB (ChromaDB) or production-grade (Pinecone/Weaviate)
  - Retrieval via semantic search (task_summary, heuristics, tags)
- [ ] **V2 Evaluator – Grounded Judge**
  - Open-book evaluation: judge agent output using reference documents
  - Ensures factual correctness
- [ ] **Fine-tune Specialized Actor Model**
  - Use dataset of successful agent trajectories
  - Fine-tune smaller models (e.g., Llama 3 8B, Mistral 7B)
  - Optimize cost & task-specific performance

### Production & Operations (Factory)
- [ ] **Configuration Management**
  - Remove hard-coded numbers, model names, thresholds
  - Use `config.yaml` or Pydantic for runtime settings
- [ ] **Comprehensive Observability**
  - Trace every step of each agent run
  - Capture LLM I/O, token counts, cost, latency
- [ ] **Full Test Suite & CI/CD**
  - Unit + Integration + Regression tests
  - Benchmark 10-20 challenging tasks
  - Prevent regressions during development

### Advanced Capabilities (Future)
- [ ] **Human-in-the-Loop / Uncertainty Protocol**
  - Pause execution when confidence is low
  - Ask user for clarification or approval
- [ ] **Multi-Modal Agents**
  - Add image/audio input handling
  - Integrate vision-capable LLMs
- [ ] **Stateful Tools**
  - Persistent sessions (Jupyter Notebook, active DB connection, open files)
  - Enables complex, long-horizon tasks

---

## 🧩 V2 Tool Layer – Current & Future TODOs

| Tool | Status | Notes / Action Items |
|------|--------|--------------------|
| `sandbox_exec` | ✅ Implemented | Stateful Python execution in Docker/MicroVM; persists variables; replaces Calculator & API wrappers |
| `code_verification` | ✅ Implemented | Run linters/type checks/unit tests; mandatory before finalizing code; integrate into reflexion loop |
| `codebase_search` | ✅ Implemented | Semantic + exact search; hybrid mode for both conceptual and exact queries |
| `browser_fetch` | ✅ Implemented | Headless JS-capable web reader; scroll + extract markdown text; replace `requests.get` for SPA sites |
| `file_manager` | ✅ Implemented | CRUD + patching for large files; patch preferred to avoid rewriting large files |
| `ask_human` | ⚠ Recommended | Human interruption mechanism; essential for high-risk actions |
| **Planned Enhancements** | ⏳ Future | <ul><li>Stateful tool sessions (e.g., persist open files, notebook cells)</li><li>Automatic tool output summarization for context efficiency</li><li>Dynamic tool discovery & registration</li></ul> |

---

## ⚡ Production Lessons / Known Issues
- **Model Drift**: LLMs sometimes add chatter/markdown → hardened parser with regex stripping required
- **Context Firehose**: Tools (web_browse) can dump 50k+ tokens → truncate/summarize outputs
- **API Reliability**: Exponential backoff + provider abstraction needed for Groq / Gemini / Ollama
- **Cost vs Latency Trade-offs**:
  - ReAct fast, low-cost for simple tasks
  - Reflexion slower, higher-cost but more reliable for complex queries
  - Plan adaptive routing based on query complexity

---

## 📅 Roadmap Snapshot
- ✅ **v0.1 Foundation**: Sequential ReAct, basic tools, LLM interface, error handling
- ✅ **v0.2 Stable**: Hybrid ReAct + Reflexion, parser, benchmarks
- 🚧 **v0.3 Intelligence Layer**: Long-term memory, adaptive routing, semantic caching, tool output compression, observability
- 📅 **v0.4 Production Hardening**: Horizontal scaling, tool marketplace, automated evaluation, Docker + Kubernetes deployment, security & audit logs

---

## 📚 References
- ReAct: Yao et al., 2022
- Reflexion: Shinn et al., 2023
- LangChain / AutoGPT: For inspiration & anti-patterns
- DSPy: Evaluation patterns

---

## 🤝 Contribution Notes
- Extend `Tool` class in `src/tools/base.py` for new capabilities
- Tests go in `tests/` using `pytest`
- Benchmark new tasks in `benchmarks/results/`
- Use PR template: describe feature, include performance/latency/cost metrics
