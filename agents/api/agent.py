from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Market Data API Agent")

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class StockData(BaseModel):
    symbol: str
    current_price: float
    change_percent: float
    volume: int
    market_cap: float
    pe_ratio: Optional[float] = None

class MarketData(BaseModel):
    stocks: Dict[str, StockData]
    timestamp: str
    market_summary: Dict[str, Any]

def get_alpha_vantage_data(symbol: str) -> Dict[str, Any]:
    """Fetch data from Alpha Vantage API."""
    ts = TimeSeries(key=os.getenv("ALPHA_VANTAGE_API_KEY"))
    try:
        data, meta = ts.get_quote_endpoint(symbol)
        return {
            "price": float(data.get("05. price", 0)),
            "change_percent": float(data.get("10. change percent", "0").strip("%")),
            "volume": int(data.get("06. volume", 0))
        }
    except Exception as e:
        print(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
        return None

def get_yahoo_finance_data(symbol: str) -> Dict[str, Any]:
    """Fetch data from Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown")
        }
    except Exception as e:
        print(f"Error fetching Yahoo Finance data for {symbol}: {str(e)}")
        return None

def get_asia_tech_stocks() -> List[str]:
    """Return a list of major Asian tech stocks to monitor."""
    return [
        "TSM",      # TSMC
        "SSNLF",    # Samsung
        "BABA",     # Alibaba
        "TCEHY",    # Tencent
        "9984.T",   # Softbank
        "035420.KS" # NAVER
    ]

@app.post("/query", response_model=MarketData)
async def handle_query(request: QueryRequest):
    """Handle market data queries."""
    try:
        stocks_data = {}
        asia_tech_stocks = get_asia_tech_stocks()
        
        for symbol in asia_tech_stocks:
            av_data = get_alpha_vantage_data(symbol)
            yf_data = get_yahoo_finance_data(symbol)
            
            if av_data and yf_data:
                stocks_data[symbol] = StockData(
                    symbol=symbol,
                    current_price=av_data["price"],
                    change_percent=av_data["change_percent"],
                    volume=av_data["volume"],
                    market_cap=yf_data["market_cap"],
                    pe_ratio=yf_data["pe_ratio"]
                )
        
        # Calculate market summary
        total_market_cap = sum(stock.market_cap for stock in stocks_data.values())
        avg_change = sum(stock.change_percent for stock in stocks_data.values()) / len(stocks_data)
        
        market_summary = {
            "total_market_cap": total_market_cap,
            "average_change_percent": avg_change,
            "number_of_stocks": len(stocks_data),
            "sector_performance": {
                "semiconductors": {
                    "symbols": ["TSM", "SSNLF"],
                    "avg_change": sum(stocks_data[s].change_percent for s in ["TSM", "SSNLF"] if s in stocks_data) / 2
                },
                "internet": {
                    "symbols": ["BABA", "TCEHY"],
                    "avg_change": sum(stocks_data[s].change_percent for s in ["BABA", "TCEHY"] if s in stocks_data) / 2
                }
            }
        }
        
        return MarketData(
            stocks=stocks_data,
            timestamp=pd.Timestamp.now(tz="Asia/Tokyo").isoformat(),
            market_summary=market_summary
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_AGENT_PORT", 8001))) 