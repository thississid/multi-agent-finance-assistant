import pytest
import asyncio
from orchestrator.agent_orchestrator import AgentOrchestrator
from typing import Dict, Any

@pytest.fixture
async def orchestrator():
    """Create and initialize an orchestrator instance."""
    orchestrator = AgentOrchestrator()
    initialized = await orchestrator.initialize()
    assert initialized, "Failed to initialize orchestrator"
    yield orchestrator
    await orchestrator.cleanup()

@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test that the orchestrator initializes correctly."""
    assert orchestrator.agents_initialized

@pytest.mark.asyncio
async def test_text_query_processing(orchestrator):
    """Test processing a text query."""
    query_data = {
        "query": "What's our risk exposure in Asia tech stocks today?",
        "input_type": "text",
        "response_type": "text"
    }
    
    response = await orchestrator.process_query(query_data)
    
    assert "content" in response
    assert "confidence" in response
    assert "sources" in response
    assert "timestamp" in response
    assert "error" not in response

@pytest.mark.asyncio
async def test_voice_query_processing(orchestrator):
    """Test processing a voice query."""
    # Create dummy audio data (silence)
    audio_data = [0.0] * 16000  # 1 second of silence at 16kHz
    
    query_data = {
        "query": "",
        "input_type": "voice",
        "response_type": "voice",
        "audio_data": audio_data
    }
    
    response = await orchestrator.process_query(query_data)
    
    assert "content" in response
    assert "audio_data" in response
    assert "sample_rate" in response
    assert "error" not in response

@pytest.mark.asyncio
async def test_market_data_gathering(orchestrator):
    """Test gathering market data."""
    market_data = await orchestrator._gather_market_data(
        "What's the performance of AAPL and TSMC today?"
    )
    
    assert "market_data" in market_data
    assert "earnings_data" in market_data
    assert isinstance(market_data["market_data"], dict)
    assert isinstance(market_data["earnings_data"], dict)

@pytest.mark.asyncio
async def test_context_gathering(orchestrator):
    """Test gathering contextual information."""
    context = await orchestrator._gather_context(
        "What's the latest news about semiconductor companies?"
    )
    
    assert "news" in context
    assert "relevant_docs" in context
    assert isinstance(context["news"], list)
    assert isinstance(context["relevant_docs"], list)

@pytest.mark.asyncio
async def test_data_analysis(orchestrator):
    """Test financial data analysis."""
    # Create sample data
    market_data = {
        "market_data": {
            "AAPL": {"current_price": 150.0, "change_percent": 2.5},
            "TSMC": {"current_price": 100.0, "change_percent": -1.5}
        },
        "earnings_data": {
            "AAPL": {"revenue": 100000000000, "earnings": 30000000000},
            "TSMC": {"revenue": 50000000000, "earnings": 15000000000}
        }
    }
    
    context_data = {
        "news": [
            {
                "title": "Tech Stocks Rally",
                "summary": "Technology stocks show strong performance..."
            }
        ],
        "relevant_docs": []
    }
    
    analysis = await orchestrator._analyze_data(market_data, context_data)
    
    assert "sentiment" in analysis
    assert "risk" in analysis
    assert "earnings" in analysis

@pytest.mark.asyncio
async def test_response_generation(orchestrator):
    """Test natural language response generation."""
    query = "What's our risk exposure in Asia tech stocks?"
    market_data = {
        "market_data": {"TSMC": {"current_price": 100.0}},
        "earnings_data": {}
    }
    context_data = {"news": [], "relevant_docs": []}
    analysis_result = {
        "sentiment": {"overall": "neutral"},
        "risk": {"risk_level": "medium"},
        "earnings": {}
    }
    
    response = await orchestrator._generate_response(
        query,
        market_data,
        context_data,
        analysis_result
    )
    
    assert "content" in response
    assert "confidence" in response
    assert "sources" in response
    assert "timestamp" in response

@pytest.mark.asyncio
async def test_error_handling(orchestrator):
    """Test error handling in the orchestrator."""
    # Test with invalid input
    query_data = {
        "query": "",  # Empty query should raise an error
        "input_type": "invalid",  # Invalid input type
        "response_type": "text"
    }
    
    response = await orchestrator.process_query(query_data)
    assert "error" in response 