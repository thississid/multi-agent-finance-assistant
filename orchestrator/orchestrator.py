from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Finance Assistant Orchestrator")

class QueryRequest(BaseModel):
    query: str
    mode: str = "text"  # "text" or "voice"
    context: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
    confidence: float
    source: List[str]

class AgentResponse(BaseModel):
    status: str
    data: Any
    error: Optional[str] = None

async def call_agent_service(service_url: str, payload: Dict[str, Any]) -> AgentResponse:
    """Make an async call to an agent service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(service_url, json=payload)
            response.raise_for_status()
            return AgentResponse(**response.json())
        except httpx.HTTPError as e:
            return AgentResponse(status="error", data=None, error=str(e))

async def process_market_query(query: str) -> QueryResponse:
    """Process a market-related query through various agents."""
    
    # 1. Call API Agent for market data
    api_response = await call_agent_service(
        f"http://localhost:{os.getenv('API_AGENT_PORT')}/query",
        {"query": query}
    )
    
    # 2. Call Scraping Agent for news and filings
    scraper_response = await call_agent_service(
        f"http://localhost:{os.getenv('SCRAPER_AGENT_PORT')}/query",
        {"query": query}
    )
    
    # 3. Call Retriever Agent for relevant historical context
    retriever_response = await call_agent_service(
        f"http://localhost:{os.getenv('RETRIEVER_AGENT_PORT')}/query",
        {"query": query, "context": {
            "market_data": api_response.data,
            "news_data": scraper_response.data
        }}
    )
    
    # 4. Call Analysis Agent for financial analysis
    analysis_response = await call_agent_service(
        f"http://localhost:{os.getenv('ANALYZER_AGENT_PORT')}/analyze",
        {"data": {
            "market": api_response.data,
            "news": scraper_response.data,
            "context": retriever_response.data
        }}
    )
    
    # 5. Call Language Agent to generate narrative
    language_response = await call_agent_service(
        f"http://localhost:{os.getenv('LANGUAGE_AGENT_PORT')}/generate",
        {"analysis": analysis_response.data}
    )
    
    return QueryResponse(
        message=language_response.data["narrative"],
        data={
            "market_data": api_response.data,
            "news_data": scraper_response.data,
            "analysis": analysis_response.data
        },
        confidence=language_response.data.get("confidence", 0.0),
        source=language_response.data.get("sources", [])
    )

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Handle incoming queries and orchestrate agent responses."""
    try:
        if request.mode == "voice":
            # Handle voice input through Voice Agent
            voice_response = await call_agent_service(
                f"http://localhost:{os.getenv('VOICE_AGENT_PORT')}/transcribe",
                {"audio_data": request.context.get("audio_data")}
            )
            
            if voice_response.status == "error":
                raise HTTPException(status_code=400, detail="Voice transcription failed")
            
            query = voice_response.data["text"]
        else:
            query = request.query
        
        # Process the query through market agents
        response = await process_market_query(query)
        
        if request.mode == "voice":
            # Convert response to speech
            await call_agent_service(
                f"http://localhost:{os.getenv('VOICE_AGENT_PORT')}/synthesize",
                {"text": response.message}
            )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("ORCHESTRATOR_PORT", 8000))) 