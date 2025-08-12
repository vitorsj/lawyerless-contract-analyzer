"""
LLM Provider Factory and Management System.

This module handles different LLM providers (OpenAI, LLM Studio) with
unified interface and provider switching capabilities.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.test import TestModel

from ..settings import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    LM_STUDIO = "lm_studio"


class LLMProviderError(Exception):
    """Custom exception for LLM provider errors."""
    pass


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def get_model(self) -> Any:
        """Get the model instance for PydanticAI."""
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate provider configuration."""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self):
        self.api_key = settings.get_current_api_key()
        self.model_name = settings.get_current_model()
        self.base_url = settings.get_current_base_url()
        self.timeout = settings.get_current_timeout()
    
    def get_model(self) -> OpenAIModel:
        """Get OpenAI model instance."""
        try:
            # Set environment variables for OpenAI client
            os.environ["OPENAI_API_KEY"] = self.api_key
            if self.base_url:
                os.environ["OPENAI_BASE_URL"] = self.base_url
            
            return OpenAIModel(
                self.model_name,
                provider='openai'
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI model: {e}")
            raise LLMProviderError(f"OpenAI initialization failed: {e}") from e
    
    def validate_configuration(self) -> bool:
        """Validate OpenAI configuration."""
        if not self.api_key or not self.api_key.startswith('sk-'):
            logger.error("Invalid OpenAI API key format")
            return False
        
        if not self.model_name:
            logger.error("OpenAI model name not specified")
            return False
        
        return True
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get OpenAI provider information."""
        return {
            "provider": "openai",
            "model": self.model_name,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "api_key_configured": bool(self.api_key and self.api_key != "test_key")
        }


class LMStudioProvider(BaseLLMProvider):
    """LLM Studio provider implementation (OpenAI-compatible API)."""
    
    def __init__(self):
        self.api_key = settings.get_current_api_key()
        self.model_name = settings.get_current_model()
        self.base_url = settings.get_current_base_url()
        self.timeout = settings.get_current_timeout()
    
    def get_model(self) -> OpenAIModel:
        """Get LLM Studio model instance using OpenAI-compatible interface."""
        try:
            # Set environment variables for OpenAI client
            os.environ["OPENAI_API_KEY"] = self.api_key
            os.environ["OPENAI_BASE_URL"] = self.base_url
            
            return OpenAIModel(
                self.model_name,
                provider='openai'  # Uses OpenAI client but points to LLM Studio
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM Studio model: {e}")
            raise LLMProviderError(f"LLM Studio initialization failed: {e}") from e
    
    def validate_configuration(self) -> bool:
        """Validate LLM Studio configuration."""
        if not self.api_key:
            logger.error("LLM Studio API key not provided")
            return False
        
        if not self.model_name:
            logger.error("LLM Studio model name not specified")
            return False
        
        if not self.base_url:
            logger.error("LLM Studio base URL not specified")
            return False
        
        # Basic URL validation
        if not (self.base_url.startswith('http://') or self.base_url.startswith('https://')):
            logger.error("LLM Studio base URL must start with http:// or https://")
            return False
        
        return True
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get LLM Studio provider information."""
        return {
            "provider": "llm_studio",
            "model": self.model_name,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "api_key_configured": bool(self.api_key and self.api_key != "test_key")
        }


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, BaseLLMProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """
        Get LLM provider instance.
        
        Args:
            provider_name: Provider name, uses settings.llm_provider if None
        
        Returns:
            Provider instance
            
        Raises:
            LLMProviderError: If provider is not supported
        """
        provider_name = provider_name or settings.llm_provider
        
        # Cache providers to avoid recreating
        if provider_name in cls._providers:
            return cls._providers[provider_name]
        
        if provider_name == LLMProvider.OPENAI:
            provider = OpenAIProvider()
        elif provider_name == LLMProvider.LM_STUDIO:
            provider = LMStudioProvider()
        else:
            raise LLMProviderError(f"Unsupported LLM provider: {provider_name}")
        
        # Validate configuration
        if not provider.validate_configuration():
            raise LLMProviderError(f"Invalid configuration for provider: {provider_name}")
        
        cls._providers[provider_name] = provider
        logger.info(f"Initialized LLM provider: {provider_name}")
        
        return provider
    
    @classmethod
    def get_model(cls, provider_name: Optional[str] = None) -> Any:
        """
        Get model instance for specified provider.
        
        Args:
            provider_name: Provider name, uses settings.llm_provider if None
            
        Returns:
            Model instance for PydanticAI
        """
        provider = cls.get_provider(provider_name)
        return provider.get_model()
    
    @classmethod
    def get_available_providers(cls) -> List[Dict[str, Any]]:
        """Get list of available providers with their info."""
        providers_info = []
        
        for provider_name in LLMProvider:
            try:
                # Temporarily switch to test the provider
                original_provider = settings.llm_provider
                settings.llm_provider = provider_name.value
                
                provider = cls.get_provider(provider_name.value)
                info = provider.get_provider_info()
                info['available'] = provider.validate_configuration()
                providers_info.append(info)
                
                # Restore original provider
                settings.llm_provider = original_provider
                
            except Exception as e:
                providers_info.append({
                    "provider": provider_name.value,
                    "available": False,
                    "error": str(e)
                })
        
        return providers_info
    
    @classmethod
    def clear_cache(cls):
        """Clear provider cache."""
        cls._providers.clear()
        logger.info("LLM provider cache cleared")


# Convenience function for external use
def get_llm_model(provider_name: Optional[str] = None) -> Any:
    """
    Get configured LLM model from settings or specified provider.
    
    Args:
        provider_name: Provider name, uses settings.llm_provider if None
        
    Returns:
        Model instance for PydanticAI
    """
    return LLMProviderFactory.get_model(provider_name)


def get_provider_info(provider_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get provider information.
    
    Args:
        provider_name: Provider name, uses settings.llm_provider if None
        
    Returns:
        Provider information dictionary
    """
    provider = LLMProviderFactory.get_provider(provider_name)
    return provider.get_provider_info()


def list_available_providers() -> List[Dict[str, Any]]:
    """
    List all available providers with their configuration status.
    
    Returns:
        List of provider information dictionaries
    """
    return LLMProviderFactory.get_available_providers()