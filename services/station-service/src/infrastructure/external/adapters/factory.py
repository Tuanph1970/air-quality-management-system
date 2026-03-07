"""Adapter factory - creates appropriate adapter based on type."""
from __future__ import annotations

import logging
from typing import Dict, Type

from .base_adapter import BaseStationAdapter
from .generic_adapter import GenericStationAdapter

logger = logging.getLogger(__name__)


class AdapterFactory:
    """Factory for creating station API adapters.
    
    This factory maintains a registry of adapter types and creates
    the appropriate adapter based on configuration.
    
    Example:
        factory = AdapterFactory()
        adapter = factory.create("generic")
        result = await adapter.fetch_data(config)
    """
    
    def __init__(self):
        """Initialize adapter factory with built-in adapters."""
        self._adapters: Dict[str, Type[BaseStationAdapter]] = {
            "generic": GenericStationAdapter,
        }
    
    def register_adapter(
        self,
        adapter_type: str,
        adapter_class: Type[BaseStationAdapter],
    ) -> None:
        """Register a custom adapter type.
        
        Args:
            adapter_type: Unique identifier for the adapter
            adapter_class: Adapter class to register
            
        Example:
            factory.register_adapter("epa", EPAAdapter)
        """
        self._adapters[adapter_type.lower()] = adapter_class
        logger.info(f"Registered adapter: {adapter_type}")
    
    def create(self, adapter_type: str) -> BaseStationAdapter:
        """Create an adapter instance.
        
        Args:
            adapter_type: Type of adapter to create
            
        Returns:
            Adapter instance
            
        Raises:
            ValueError: If adapter type is not registered
        """
        adapter_type = adapter_type.lower()
        
        if adapter_type not in self._adapters:
            available = ", ".join(self._adapters.keys())
            raise ValueError(
                f"Unknown adapter type: {adapter_type}. Available: {available}"
            )
        
        adapter_class = self._adapters[adapter_type]
        return adapter_class()
    
    def get_available_adapters(self) -> list[str]:
        """Get list of available adapter types.
        
        Returns:
            List of adapter type names
        """
        return list(self._adapters.keys())
    
    @classmethod
    def get_instance(cls) -> "AdapterFactory":
        """Get singleton instance of the factory.
        
        Returns:
            Shared AdapterFactory instance
        """
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance


# Convenience function
def get_adapter(adapter_type: str) -> BaseStationAdapter:
    """Get an adapter instance by type.
    
    Args:
        adapter_type: Type of adapter
        
    Returns:
        Adapter instance
    """
    return AdapterFactory.get_instance().create(adapter_type)
