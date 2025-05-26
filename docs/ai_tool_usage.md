# AI Tool Usage Documentation

This document tracks the use of AI tools and models in the development of the Multi-Agent Finance Assistant.

## Development Process

### Initial Setup (May 28, 2023)

1. **Project Structure Creation**
   - Used GitHub Copilot and ChatGPT to generate:
     - Project directory structure
     - README.md template
     - Initial requirements.txt with appropriate dependencies

2. **Framework Selection**
   - LangChain for agent orchestration
   - CrewAI for specialized agent development
   - FastAPI for microservices
   - Streamlit for UI
   - OpenAI Whisper for STT
   - TTS for speech synthesis
   - FAISS for vector storage

## Model Parameters and Configurations

### Language Models
- **OpenAI GPT-4**
  - Temperature: 0.7
  - Max tokens: 2048
  - Used for: Natural language understanding and generation

### Embedding Models
- **Sentence Transformers**
  - Model: all-MiniLM-L6-v2
  - Used for: Document embeddings and semantic search

### Speech Models
- **Whisper**
  - Model: base
  - Language: English
  - Used for: Speech-to-text conversion

## Development Log

This section will be updated as development progresses with specific prompts used, code generation steps, and model configurations for each component. 