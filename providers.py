#!/usr/bin/env python3
"""
AI Provider Abstraction Layer
Supports multiple AI models: Claude (Anthropic) and Gemini (Google)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import anthropic
import json


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def __init__(self, api_key: str, model: str = None):
        """Initialize the provider with API key and optional model."""
        pass
    
    @abstractmethod
    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Generate a response from the AI model.
        
        Returns:
            Dict with keys:
            - 'text': str - The response text
            - 'input_tokens': int - Input tokens used
            - 'output_tokens': int - Output tokens used
            - 'cost': float - Estimated cost
        """
        pass
    
    @abstractmethod
    def get_pricing(self) -> Dict[str, float]:
        """Return pricing per million tokens: {'input': float, 'output': float}"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name (e.g., 'claude', 'gemini')"""
        pass


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider."""
    
    # Claude Sonnet 4 pricing per million tokens
    INPUT_PRICE_PER_MILLION = 3.0
    OUTPUT_PRICE_PER_MILLION = 15.0
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Generate response using Claude API."""
        # Convert messages to Claude format
        claude_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", [])
            claude_messages.append({"role": role, "content": content})
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=claude_messages
        )
        
        # Extract usage
        usage = response.usage
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        
        # Calculate cost
        cost = (input_tokens / 1_000_000 * self.INPUT_PRICE_PER_MILLION) + \
               (output_tokens / 1_000_000 * self.OUTPUT_PRICE_PER_MILLION)
        
        # Get response text
        response_text = response.content[0].text
        
        return {
            "text": response_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        }
    
    def get_pricing(self) -> Dict[str, float]:
        return {
            "input": self.INPUT_PRICE_PER_MILLION,
            "output": self.OUTPUT_PRICE_PER_MILLION
        }
    
    def get_provider_name(self) -> str:
        return "claude"


class GoogleProvider(AIProvider):
    """Google Gemini API provider."""
    
    # Gemini 1.5 Pro pricing per million tokens (approximate)
    INPUT_PRICE_PER_MILLION = 1.25  # $1.25 per million input tokens
    OUTPUT_PRICE_PER_MILLION = 5.0   # $5.00 per million output tokens
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai not installed. Install with: pip install google-generativeai"
            )
        
        self.api_key = api_key
        self.model_name = model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.genai = genai
    
    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Generate response using Google Gemini API."""
        # Gemini uses a different message format
        # Combine system prompt with first user message
        content_parts = []
        
        # Add system instruction (Gemini uses system_instruction parameter)
        # For now, we'll prepend it to the first message
        
        # Process messages and images
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", [])
            
            for item in content:
                if item.get("type") == "text":
                    text_content = item.get("text", "")
                    if role == "user" and system_prompt and not content_parts:
                        # Prepend system prompt to first user message
                        text_content = f"{system_prompt}\n\n{text_content}"
                    content_parts.append(text_content)
                elif item.get("type") == "image":
                    # Handle base64 image
                    image_data = item.get("source", {}).get("data", "")
                    if image_data:
                        import base64
                        from PIL import Image
                        from io import BytesIO
                        
                        image_bytes = base64.b64decode(image_data)
                        image = Image.open(BytesIO(image_bytes))
                        content_parts.append(image)
        
        # Generate response
        try:
            response = self.model.generate_content(
                content_parts,
                generation_config=self.genai.GenerationConfig(
                    max_output_tokens=max_tokens
                )
            )
            
            response_text = response.text
            
            # Get usage (Gemini provides usage info)
            usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
            if usage_metadata:
                input_tokens = usage_metadata.prompt_token_count
                output_tokens = usage_metadata.candidates_token_count
            else:
                # Fallback: estimate tokens (rough approximation: 1 token ≈ 4 chars)
                input_tokens = sum(len(str(part)) for part in content_parts) // 4
                output_tokens = len(response_text) // 4
            
            # Calculate cost
            cost = (input_tokens / 1_000_000 * self.INPUT_PRICE_PER_MILLION) + \
                   (output_tokens / 1_000_000 * self.OUTPUT_PRICE_PER_MILLION)
            
            return {
                "text": response_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost
            }
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def get_pricing(self) -> Dict[str, float]:
        return {
            "input": self.INPUT_PRICE_PER_MILLION,
            "output": self.OUTPUT_PRICE_PER_MILLION
        }
    
    def get_provider_name(self) -> str:
        return "gemini"


def create_provider(provider_type: str, api_key: str, model: str = None) -> AIProvider:
    """
    Factory function to create a provider instance.
    
    Args:
        provider_type: 'claude' or 'gemini'
        api_key: API key for the provider
        model: Optional model name (uses default if not provided)
    
    Returns:
        AIProvider instance
    """
    provider_type = provider_type.lower()
    
    if provider_type == "claude":
        model = model or "claude-sonnet-4-20250514"
        return ClaudeProvider(api_key, model)
    elif provider_type == "gemini" or provider_type == "google":
        model = model or "gemini-1.5-pro"
        return GoogleProvider(api_key, model)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}. Use 'claude' or 'gemini'")
