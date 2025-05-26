from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Financial Analysis Agent")

class AnalysisRequest(BaseModel):
    data: Dict[str, Any]

class StockAnalysis(BaseModel):
    symbol: str
    metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    sentiment: Dict[str, Any]
    recommendations: List[str]

class AnalysisResponse(BaseModel):
    analyses: Dict[str, StockAnalysis]
    portfolio_metrics: Dict[str, Any]
    risk_exposure: Dict[str, Any]
    insights: List[str]
    metadata: Dict[str, Any]

def calculate_risk_metrics(price_data: List[float]) -> Dict[str, float]:
    """Calculate various risk metrics for a stock."""
    if not price_data:
        return {
            "volatility": 0.0,
            "beta": 0.0,
            "var_95": 0.0
        }
    
    returns = pd.Series(price_data).pct_change().dropna()
    
    return {
        "volatility": float(returns.std() * np.sqrt(252)),  # Annualized volatility
        "beta": 1.0,  # Placeholder - would need market data for actual beta
        "var_95": float(np.percentile(returns, 5))  # 95% VaR
    }

def analyze_sentiment(news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze sentiment from news items."""
    if not news_items:
        return {
            "score": 0.0,
            "label": "neutral",
            "confidence": 0.0
        }
    
    # For now, using a simple average of relevance scores as sentiment
    # In production, would use a proper sentiment analysis model
    avg_score = sum(item.get('relevance_score', 0) for item in news_items) / len(news_items)
    
    return {
        "score": avg_score,
        "label": "positive" if avg_score > 0.6 else "neutral" if avg_score > 0.4 else "negative",
        "confidence": 0.8
    }

def generate_recommendations(metrics: Dict[str, float], risk_metrics: Dict[str, float], 
                           sentiment: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on analysis."""
    recommendations = []
    
    # Example rules for recommendations
    if risk_metrics["volatility"] > 0.3:
        recommendations.append("High volatility detected - consider hedging positions")
    
    if sentiment["label"] == "positive" and risk_metrics["var_95"] > -0.02:
        recommendations.append("Positive sentiment with manageable risk - maintain position")
    
    if sentiment["label"] == "negative" and risk_metrics["volatility"] > 0.25:
        recommendations.append("Negative sentiment with high volatility - consider reducing exposure")
    
    return recommendations

def calculate_portfolio_metrics(analyses: Dict[str, StockAnalysis]) -> Dict[str, Any]:
    """Calculate portfolio-level metrics."""
    total_exposure = sum(analysis.metrics.get("market_cap", 0) 
                        for analysis in analyses.values())
    
    sector_exposure = {
        "semiconductors": sum(analysis.metrics.get("market_cap", 0) 
                            for symbol, analysis in analyses.items()
                            if symbol in ["TSM", "SSNLF"]),
        "internet": sum(analysis.metrics.get("market_cap", 0)
                       for symbol, analysis in analyses.items()
                       if symbol in ["BABA", "TCEHY"])
    }
    
    return {
        "total_exposure": total_exposure,
        "sector_exposure": {
            sector: value / total_exposure if total_exposure else 0
            for sector, value in sector_exposure.items()
        }
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(request: AnalysisRequest):
    """Analyze financial data and generate insights."""
    try:
        market_data = request.data.get("market", {})
        news_data = request.data.get("news", {})
        context = request.data.get("context", {})
        
        analyses = {}
        
        # Analyze each stock
        for symbol, data in market_data.get("stocks", {}).items():
            # Calculate metrics
            metrics = {
                "market_cap": data.get("market_cap", 0),
                "pe_ratio": data.get("pe_ratio", 0),
                "price": data.get("current_price", 0),
                "volume": data.get("volume", 0)
            }
            
            # Calculate risk metrics
            risk_metrics = calculate_risk_metrics([data.get("current_price", 0)])
            
            # Analyze sentiment
            relevant_news = [
                item for item in news_data.get("news_items", [])
                if symbol.lower() in item.get("title", "").lower()
            ]
            sentiment = analyze_sentiment(relevant_news)
            
            # Generate recommendations
            recommendations = generate_recommendations(metrics, risk_metrics, sentiment)
            
            analyses[symbol] = StockAnalysis(
                symbol=symbol,
                metrics=metrics,
                risk_metrics=risk_metrics,
                sentiment=sentiment,
                recommendations=recommendations
            )
        
        # Calculate portfolio metrics
        portfolio_metrics = calculate_portfolio_metrics(analyses)
        
        # Generate risk exposure analysis
        risk_exposure = {
            "asia_tech_allocation": portfolio_metrics["sector_exposure"]["semiconductors"] +
                                  portfolio_metrics["sector_exposure"]["internet"],
            "high_risk_allocation": sum(
                analysis.metrics["market_cap"] / portfolio_metrics["total_exposure"]
                for analysis in analyses.values()
                if analysis.risk_metrics["volatility"] > 0.3
            ) if portfolio_metrics["total_exposure"] else 0
        }
        
        # Generate overall insights
        insights = [
            f"Asia tech allocation is {risk_exposure['asia_tech_allocation']:.1%} of portfolio",
            f"Semiconductor exposure: {portfolio_metrics['sector_exposure']['semiconductors']:.1%}",
            f"Internet sector exposure: {portfolio_metrics['sector_exposure']['internet']:.1%}"
        ]
        
        return AnalysisResponse(
            analyses=analyses,
            portfolio_metrics=portfolio_metrics,
            risk_exposure=risk_exposure,
            insights=insights,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "analysis_version": "1.0",
                "data_sources": ["market_data", "news_data", "historical_context"]
            }
        )
    
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("ANALYZER_AGENT_PORT", 8004))) 