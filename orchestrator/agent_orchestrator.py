from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import logging
from pathlib import Path

from agents.api_agent.market_data_agent import MarketDataAgent
from agents.scraping_agent.web_scraper import WebScraper
from agents.retriever_agent.vector_store import VectorStoreAgent
from agents.analysis_agent.financial_analyzer import FinancialAnalyzer
from agents.language_agent.language_processor import LanguageProcessor
from agents.voice_agent.voice_processor import VoiceProcessor

class AgentOrchestrator:
    """Orchestrates the interaction between different agents in the system."""
    
    def __init__(self):
        self.logger = logging.getLogger("orchestrator")
        
        # Initialize agents
        self.market_data_agent = MarketDataAgent()
        self.web_scraper = WebScraper()
        self.vector_store = VectorStoreAgent()
        self.financial_analyzer = FinancialAnalyzer()
        self.language_processor = LanguageProcessor()
        self.voice_processor = VoiceProcessor()
        
        self.agents_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all agents."""
        try:
            # Initialize agents in parallel
            init_results = await asyncio.gather(
                self.market_data_agent.initialize(),
                self.web_scraper.initialize(),
                self.vector_store.initialize(),
                self.financial_analyzer.initialize(),
                self.language_processor.initialize(),
                self.voice_processor.initialize()
            )
            
            self.agents_initialized = all(init_results)
            return self.agents_initialized
            
        except Exception as e:
            self.logger.error(f"Orchestrator initialization error: {str(e)}")
            return False
    
    async def process_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user query through the agent pipeline."""
        try:
            if not self.agents_initialized:
                raise RuntimeError("Agents not initialized")
            
            # Extract query information
            query = query_data.get("query", "")
            input_type = query_data.get("input_type", "text")
            response_type = query_data.get("response_type", "text")
            
            # Process voice input if necessary
            if input_type == "voice":
                stt_result = await self.voice_processor.process({
                    "operation": "stt",
                    "audio_data": query_data.get("audio_data")
                })
                
                if "error" in stt_result:
                    raise ValueError(f"Speech-to-text error: {stt_result['error']}")
                    
                query = stt_result["text"]
            
            # Gather market data
            market_data = await self._gather_market_data(query)
            
            # Gather news and context
            context_data = await self._gather_context(query)
            
            # Analyze data
            analysis_result = await self._analyze_data(market_data, context_data)
            
            # Generate response
            response = await self._generate_response(query, market_data, context_data, analysis_result)
            
            # Convert to voice if needed
            if response_type == "voice":
                voice_result = await self.voice_processor.process({
                    "operation": "tts",
                    "text": response["content"]
                })
                
                if "error" in voice_result:
                    raise ValueError(f"Text-to-speech error: {voice_result['error']}")
                    
                response["audio_data"] = voice_result["audio_data"]
                response["sample_rate"] = voice_result["sample_rate"]
            
            return response
            
        except Exception as e:
            self.logger.error(f"Query processing error: {str(e)}")
            return {"error": str(e)}
    
    async def _gather_market_data(self, query: str) -> Dict[str, Any]:
        """Gather relevant market data based on the query."""
        try:
            # Extract relevant symbols from query
            # This is a simplified example - implement proper entity extraction
            symbols = ["AAPL", "TSMC", "SAMSUNG"]  # Placeholder
            
            # Get market data
            market_data = await self.market_data_agent.process({
                "query_type": "stock_data",
                "symbols": symbols
            })
            
            # Get earnings data
            earnings_data = await self.market_data_agent.process({
                "query_type": "earnings",
                "symbols": symbols
            })
            
            return {
                "market_data": market_data.get("data", {}),
                "earnings_data": earnings_data.get("earnings", {})
            }
            
        except Exception as e:
            self.logger.error(f"Market data gathering error: {str(e)}")
            return {}
    
    async def _gather_context(self, query: str) -> Dict[str, Any]:
        """Gather contextual information from various sources."""
        try:
            # Scrape market news
            news_data = await self.web_scraper.process({
                "scrape_type": "market_news",
                "limit": 5
            })
            
            # Search vector store for relevant documents
            vector_results = await self.vector_store.process({
                "operation": "search",
                "query": query,
                "k": 3
            })
            
            return {
                "news": news_data.get("articles", []),
                "relevant_docs": vector_results.get("results", [])
            }
            
        except Exception as e:
            self.logger.error(f"Context gathering error: {str(e)}")
            return {}
    
    async def _analyze_data(self, market_data: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gathered data."""
        try:
            # Analyze market sentiment
            sentiment = await self.financial_analyzer.process({
                "analysis_type": "market_sentiment",
                "market_data": market_data.get("market_data", {}),
                "news_data": context_data.get("news", [])
            })
            
            # Analyze portfolio risk
            risk = await self.financial_analyzer.process({
                "analysis_type": "portfolio_risk",
                "portfolio": market_data.get("market_data", {}),
                "market_data": market_data
            })
            
            # Analyze earnings
            earnings = await self.financial_analyzer.process({
                "analysis_type": "earnings_analysis",
                "earnings_data": market_data.get("earnings_data", []),
                "market_expectations": {}  # Placeholder - implement expectations gathering
            })
            
            return {
                "sentiment": sentiment,
                "risk": risk,
                "earnings": earnings
            }
            
        except Exception as e:
            self.logger.error(f"Data analysis error: {str(e)}")
            return {}
    
    async def _generate_response(
        self,
        query: str,
        market_data: Dict[str, Any],
        context_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a natural language response."""
        try:
            # Generate market brief
            response = await self.language_processor.process({
                "task_type": "market_brief",
                "market_data": market_data,
                "context": {
                    "query": query,
                    "news": context_data.get("news", []),
                    "analysis": analysis_result
                }
            })
            
            return {
                "content": response.get("brief", "Unable to generate response"),
                "confidence": response.get("confidence", 0),
                "sources": response.get("sources", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Response generation error: {str(e)}")
            return {
                "content": "I apologize, but I encountered an error while generating the response.",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Clean up all agents."""
        try:
            await asyncio.gather(
                self.market_data_agent.cleanup(),
                self.web_scraper.cleanup(),
                self.vector_store.cleanup(),
                self.financial_analyzer.cleanup(),
                self.language_processor.cleanup(),
                self.voice_processor.cleanup()
            )
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}") 