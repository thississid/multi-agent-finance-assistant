from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Financial Data Scraping Agent")

class ScrapingRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class NewsItem(BaseModel):
    title: str
    content: str
    source: str
    url: str
    timestamp: str
    relevance_score: float

class ScrapingResponse(BaseModel):
    news_items: List[NewsItem]
    filings_data: Dict[str, Any]
    metadata: Dict[str, Any]

def scrape_financial_news(company: str) -> List[Dict[str, Any]]:
    """Scrape financial news from multiple sources."""
    news_items = []
    
    # Example: Scrape from MarketWatch
    try:
        # Using MarketWatch search API
        url = f"https://www.marketwatch.com/search?q={company}&ts=0&tab=Articles"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract articles
        articles = soup.find_all('div', class_='article')
        
        for article in articles[:5]:  # Get top 5 articles
            title = article.find('h3').text.strip() if article.find('h3') else ""
            summary = article.find('p').text.strip() if article.find('p') else ""
            article_url = article.find('a')['href'] if article.find('a') else ""
            
            news_items.append({
                'title': title,
                'content': summary,
                'source': 'MarketWatch',
                'url': article_url,
                'timestamp': datetime.now().isoformat(),
                'relevance_score': 0.8  # Placeholder score
            })
    
    except Exception as e:
        logger.error(f"Error scraping MarketWatch: {str(e)}")
    
    return news_items

def get_sec_filings(ticker: str) -> Dict[str, Any]:
    """Get SEC filings data using SEC API."""
    try:
        # SEC EDGAR API endpoint
        base_url = "https://data.sec.gov/api/xbrl/companyfacts"
        url = f"{base_url}/{ticker}.json"
        
        headers = {
            'User-Agent': 'FinanceAssistant research@example.com'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant financial metrics
            metrics = {
                'revenue': None,
                'net_income': None,
                'assets': None,
                'liabilities': None
            }
            
            if 'facts' in data:
                facts = data['facts']
                if 'us-gaap' in facts:
                    gaap = facts['us-gaap']
                    
                    # Try to get revenue
                    if 'Revenue' in gaap:
                        metrics['revenue'] = gaap['Revenue']['units']['USD'][-1]['val']
                    
                    # Try to get net income
                    if 'NetIncomeLoss' in gaap:
                        metrics['net_income'] = gaap['NetIncomeLoss']['units']['USD'][-1]['val']
            
            return metrics
        
        return {}
    
    except Exception as e:
        logger.error(f"Error fetching SEC filings: {str(e)}")
        return {}

@app.post("/query", response_model=ScrapingResponse)
async def handle_query(request: ScrapingRequest):
    """Handle scraping requests for financial news and filings."""
    try:
        # Extract company names/tickers from query
        # For now, using a simple approach - could be enhanced with NLP
        companies = ["TSMC", "Samsung", "BABA", "Tencent"]
        
        all_news = []
        all_filings = {}
        
        for company in companies:
            # Get news
            news_items = scrape_financial_news(company)
            all_news.extend(news_items)
            
            # Get filings (if we have the ticker)
            ticker_map = {
                "TSMC": "TSM",
                "Samsung": "SSNLF",
                "BABA": "BABA",
                "Tencent": "TCEHY"
            }
            
            if company in ticker_map:
                filings = get_sec_filings(ticker_map[company])
                all_filings[ticker_map[company]] = filings
        
        # Sort news by relevance score
        all_news.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "sources_checked": ["MarketWatch", "SEC EDGAR"],
            "companies_analyzed": companies
        }
        
        return ScrapingResponse(
            news_items=[NewsItem(**item) for item in all_news],
            filings_data=all_filings,
            metadata=metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("SCRAPER_AGENT_PORT", 8002))) 