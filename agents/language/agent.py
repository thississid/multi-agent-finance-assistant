from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Language Generation Agent")

# Initialize LangChain components
llm = ChatOpenAI(
    model_name="gpt-4-turbo-preview",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

narrative_template = """
You are a professional financial analyst providing a market brief. Based on the following analysis, generate a clear and concise narrative about the current market situation, focusing on risk exposure and earnings surprises in Asia tech stocks.

Analysis Data:
{analysis_data}

Portfolio Metrics:
{portfolio_metrics}

Risk Exposure:
{risk_exposure}

Key Insights:
{insights}

Please provide a response that:
1. Summarizes the current Asia tech allocation and any significant changes
2. Highlights major earnings surprises (both positive and negative)
3. Describes the overall market sentiment and risk factors
4. Provides any relevant recommendations

Response should be professional, concise, and easy to understand when spoken.
"""

narrative_prompt = PromptTemplate(
    input_variables=["analysis_data", "portfolio_metrics", "risk_exposure", "insights"],
    template=narrative_template
)

narrative_chain = LLMChain(llm=llm, prompt=narrative_prompt)

class GenerationRequest(BaseModel):
    analysis: Dict[str, Any]

class GenerationResponse(BaseModel):
    narrative: str
    confidence: float
    sources: List[str]
    metadata: Dict[str, Any]

def format_percentage(value: float) -> str:
    """Format a decimal value as a percentage string."""
    return f"{value * 100:.1f}%"

def format_currency(value: float, billions: bool = True) -> str:
    """Format a currency value in billions or millions."""
    if billions:
        return f"${value / 1e9:.1f}B"
    return f"${value / 1e6:.1f}M"

def extract_earnings_surprises(analyses: Dict[str, Any]) -> List[str]:
    """Extract significant earnings surprises from the analyses."""
    surprises = []
    for symbol, analysis in analyses.items():
        sentiment = analysis.get("sentiment", {})
        if sentiment.get("label") in ["positive", "negative"]:
            surprises.append(f"{symbol}: {sentiment['label']} ({format_percentage(sentiment['score'])})")
    return surprises

@app.post("/generate", response_model=GenerationResponse)
async def generate_narrative(request: GenerationRequest):
    """Generate a narrative response based on financial analysis."""
    try:
        analysis = request.analysis
        
        # Format the analysis data for the prompt
        analysis_data = {
            "stocks_analyzed": len(analysis.get("analyses", {})),
            "earnings_surprises": extract_earnings_surprises(analysis.get("analyses", {})),
            "market_conditions": analysis.get("portfolio_metrics", {}).get("market_conditions", "neutral")
        }
        
        # Get portfolio metrics
        portfolio_metrics = analysis.get("portfolio_metrics", {})
        
        # Get risk exposure
        risk_exposure = analysis.get("risk_exposure", {})
        
        # Get insights
        insights = analysis.get("insights", [])
        
        # Generate the narrative
        response = narrative_chain.run({
            "analysis_data": analysis_data,
            "portfolio_metrics": portfolio_metrics,
            "risk_exposure": risk_exposure,
            "insights": "\n".join(insights)
        })
        
        # Extract sources from the analysis
        sources = [
            f"{symbol}: {data.get('sentiment', {}).get('source', 'market data')}"
            for symbol, data in analysis.get("analyses", {}).items()
        ]
        
        return GenerationResponse(
            narrative=response,
            confidence=0.85,  # Placeholder confidence score
            sources=sources,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-4-turbo-preview",
                "template_version": "1.0"
            }
        )
    
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("LANGUAGE_AGENT_PORT", 8005))) 