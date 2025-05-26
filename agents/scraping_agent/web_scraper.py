from typing import Dict, Any, Optional, List
import aiohttp
from bs4 import BeautifulSoup
import json
from datetime import datetime
import asyncio
from urllib.parse import urljoin
import logging
from ..base_agent import BaseAgent

class WebScraper(BaseAgent):
    """Agent responsible for scraping financial data from various web sources."""
    
    def __init__(self, name: str = "web_scraper", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Define source configurations
        self.sources = {
            "earnings": {
                "url": "https://www.earningswhispers.com/calendar",
                "selectors": {
                    "companies": ".company",
                    "date": ".date",
                    "estimate": ".estimate"
                }
            },
            "market_news": {
                "url": "https://www.marketwatch.com/latest-news",
                "selectors": {
                    "articles": "article",
                    "title": "h3",
                    "summary": ".article__summary"
                }
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize the web scraper with an HTTP session."""
        try:
            self.session = aiohttp.ClientSession(headers=self.headers)
            return True
        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process scraping requests."""
        try:
            scrape_type = input_data.get("scrape_type")
            
            if scrape_type == "earnings":
                return await self._scrape_earnings(input_data)
            elif scrape_type == "market_news":
                return await self._scrape_market_news(input_data)
            elif scrape_type == "custom":
                return await self._custom_scrape(input_data)
            else:
                raise ValueError(f"Unsupported scrape type: {scrape_type}")
                
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            return {"error": str(e)}
    
    async def _scrape_earnings(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape earnings data for specified companies."""
        try:
            companies = input_data.get("companies", [])
            source = self.sources["earnings"]
            
            async with self.session.get(source["url"]) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch earnings data: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                results = []
                for company in companies:
                    company_elem = soup.find(
                        source["selectors"]["companies"],
                        text=lambda x: company.lower() in x.lower() if x else False
                    )
                    
                    if company_elem:
                        date_elem = company_elem.find_next(source["selectors"]["date"])
                        estimate_elem = company_elem.find_next(source["selectors"]["estimate"])
                        
                        results.append({
                            "company": company,
                            "date": date_elem.text.strip() if date_elem else None,
                            "estimate": estimate_elem.text.strip() if estimate_elem else None,
                            "timestamp": datetime.now().isoformat()
                        })
            
            return {
                "results": results,
                "source": source["url"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Earnings scraping error: {str(e)}")
            return {"error": str(e)}
    
    async def _scrape_market_news(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape latest market news articles."""
        try:
            limit = input_data.get("limit", 5)
            source = self.sources["market_news"]
            
            async with self.session.get(source["url"]) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch market news: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                articles = []
                for article in soup.find_all(source["selectors"]["articles"])[:limit]:
                    title_elem = article.find(source["selectors"]["title"])
                    summary_elem = article.find(source["selectors"]["summary"])
                    link = article.find("a", href=True)
                    
                    if title_elem:
                        articles.append({
                            "title": title_elem.text.strip(),
                            "summary": summary_elem.text.strip() if summary_elem else None,
                            "url": urljoin(source["url"], link["href"]) if link else None,
                            "timestamp": datetime.now().isoformat()
                        })
            
            return {
                "articles": articles,
                "source": source["url"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Market news scraping error: {str(e)}")
            return {"error": str(e)}
    
    async def _custom_scrape(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform custom scraping based on provided configuration."""
        try:
            url = input_data.get("url")
            selectors = input_data.get("selectors", {})
            
            if not url or not selectors:
                raise ValueError("URL and selectors are required for custom scraping")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch from {url}: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                results = {}
                for key, selector in selectors.items():
                    elements = soup.select(selector)
                    results[key] = [elem.text.strip() for elem in elements]
            
            return {
                "results": results,
                "source": url,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Custom scraping error: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for processing."""
        if "scrape_type" not in input_data:
            return False
            
        if input_data["scrape_type"] == "earnings":
            return "companies" in input_data and isinstance(input_data["companies"], list)
        elif input_data["scrape_type"] == "market_news":
            return True  # No additional validation needed
        elif input_data["scrape_type"] == "custom":
            return all(key in input_data for key in ["url", "selectors"])
            
        return False 