# Multi-Agent Finance Assistant

A sophisticated multi-agent finance assistant that delivers spoken market briefs via a Streamlit app. This system uses multiple specialized agents to gather, analyze, and present financial data through voice interaction.

## Features

- Real-time market data integration via API agents
- Web scraping for financial filings and news
- Retrieval-Augmented Generation (RAG) for context-aware responses
- Voice input/output capabilities
- Microservices architecture with FastAPI
- Beautiful Streamlit interface

## Architecture

### Agent Components

1. **API Agent**
   - Polls real-time & historical market data
   - Uses AlphaVantage/Yahoo Finance APIs

2. **Scraping Agent**
   - Crawls financial filings and news
   - Implements efficient data extraction

3. **Retriever Agent**
   - Indexes embeddings in vector store
   - Performs semantic search and retrieval

4. **Analysis Agent**
   - Processes financial data
   - Generates insights and analytics

5. **Language Agent**
   - Synthesizes narrative responses
   - Handles context management

6. **Voice Agent**
   - Manages STT (Whisper) and TTS pipelines
   - Handles voice I/O

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multi-agent-finance-assistant.git
cd multi-agent-finance-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configurations
```

5. Run the application:
```bash
streamlit run streamlit_app/app.py
```

## Project Structure

```
.
├── agents/                 # Agent implementations
│   ├── api/               # API agent
│   ├── scraper/           # Scraping agent
│   ├── retriever/         # Retrieval agent
│   ├── analyzer/          # Analysis agent
│   ├── language/          # Language agent
│   └── voice/             # Voice agent
├── data_ingestion/        # Data ingestion pipelines
├── orchestrator/          # Agent orchestration logic
├── streamlit_app/         # Streamlit frontend
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
└── docker/                # Docker configuration
```

## Documentation

- [AI Tool Usage Log](docs/ai_tool_usage.md)
- [API Documentation](docs/api.md)
- [Architecture Details](docs/architecture.md)
- [Development Guide](docs/development.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests.

## Acknowledgments

This project uses various open-source tools and frameworks:
- Streamlit
- FastAPI
- LangChain
- CrewAI
- OpenAI Whisper
- FAISS/Pinecone