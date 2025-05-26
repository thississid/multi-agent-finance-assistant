from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name (str): Name of the agent
            config (Optional[Dict[str, Any]]): Configuration dictionary for the agent
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return results.
        
        Args:
            input_data (Dict[str, Any]): Input data to process
            
        Returns:
            Dict[str, Any]: Processing results
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the agent with necessary setup.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data before processing.
        
        Args:
            input_data (Dict[str, Any]): Input data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dict[str, Any]: Agent status information
        """
        return {
            "name": self.name,
            "status": "active",
            "config": self.config
        }
    
    async def cleanup(self) -> None:
        """Clean up any resources used by the agent."""
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__() 