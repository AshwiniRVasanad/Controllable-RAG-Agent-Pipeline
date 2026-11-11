# Controllable RAG Agent Pipeline — Execution Studio 🧠📚

[![License](https://shields.io)](https://opensource.org)
[![Python 3.11+](https://shields.io)](https://python.org)
[![LangGraph](https://shields.io)](https://github.com)
[![Streamlit](https://shields.io)](https://streamlit.io)

An advanced Retrieval-Augmented Generation (RAG) pipeline powered by a deterministic **LangGraph** state machine and an interactive **Streamlit Execution Studio** designed for complex, multi-hop question answering with entity anonymization, multi-source vector retrieval, and self-correction loops.

---

## ✨ What's New & Core Capabilities
- **Streamlit Execution Studio (`simulate_agent.py`):** Features custom UI cards, live PyVis graph state telemetry, structured reasoning tabs, and sidebar sample prompts.
- **Deterministic Architecture & Anonymization:** Decomposes queries, masks named entities to prevent LLM bias, and routes tasks across three FAISS vector stores (`chunks_vector_store`, `chapter_summaries_vector_store`, `book_quotes_vectorstore`).
- **Self-Correction & Evaluation:** Iteratively verifies outputs against retrieved evidence and includes Ragas evaluation workflows.

---

## 🚀 Getting Started

### Prerequisites
- Python **3.11+**
- OpenAI or Groq API keys

### Installation & Local Run
```bash
git clone https://github.com
cd Controllable-RAG-Agent-Pipeline
cp .env.example .env
# Add your OPENAI_API_KEY and GROQ_API_KEY in .env
pip install -r requirements.txt
streamlit run simulate_agent.py
```

### Docker Deployment
```bash
docker-compose up --build
```
Access the application at `http://localhost:8501`.

---

## 📂 Project Structure

```text
├── simulate_agent.py                        # Streamlit Execution Studio UI
├── functions_for_pipeline.py                # LangGraph nodes and agent state logic
├── helper_functions.py                      # Vector store & text processing utilities
├── chunks_vector_store/                     # Pre-indexed document chunks (FAISS)
├── chapter_summaries_vector_store/          # Pre-indexed chapter summaries (FAISS)
└── book_quotes_vectorstore/                 # Pre-indexed direct quotes (FAISS)
```

---

## 📄 License
Licensed under the **Apache-2.0 License**.
