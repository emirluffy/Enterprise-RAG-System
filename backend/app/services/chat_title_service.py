"""
Context7 Verified: Intelligent Chat Title Generation Service
Using Google GenAI Python SDK for automatic conversation title generation
Based on: /googleapis/python-genai patterns (Trust Score 8.5)
"""

import asyncio
from typing import Optional
import google.genai as genai
from google.genai import types

from app.core.config import settings


class ChatTitleService:
    """Context7 verified: Intelligent conversation title generation using Gemini API"""
    
    def __init__(self):
        """Initialize the chat title service with Gemini API"""
        self.client = None
        self.model_name = "gemini-2.0-flash-001"
        self._initialize_client()
    
    def _initialize_client(self):
        """Context7 verified: Initialize Google GenAI client"""
        try:
            if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
                # Context7 verified: Direct client initialization pattern
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                print(f"✅ Chat Title Service initialized with Gemini API")
            else:
                print("⚠️ Chat Title Service: No Gemini API key available")
        except Exception as e:
            print(f"⚠️ Chat Title Service initialization failed: {e}")
            self.client = None
    
    async def generate_title(self, first_user_message: str, first_ai_response: Optional[str] = None) -> str:
        """
        Context7 verified: Generate intelligent conversation title
        
        Args:
            first_user_message: The first message from user
            first_ai_response: The first AI response (optional)
            
        Returns:
            Generated title or fallback title
        """
        if not self.client:
            return self._generate_fallback_title(first_user_message)
        
        try:
            # Context7 verified: Construct content for title generation
            prompt_parts = [
                "Kullanıcının ilk mesajına dayanarak bu sohbet için kısa, öz ve anlamlı bir başlık oluştur.",
                "Başlık türkçe olmalı, maksimum 4-5 kelime olmalı ve sohbetin konusunu yansıtmalı.",
                "Sadece başlığı döndür, başka hiçbir açıklama ekleme.",
                "",
                f"Kullanıcı mesajı: {first_user_message}"
            ]
            
            if first_ai_response:
                prompt_parts.append(f"AI yanıtı: {first_ai_response[:200]}...")
            
            prompt = "\n".join(prompt_parts)
            
            # Context7 verified: Generate content using Google GenAI patterns
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for consistent titles
                    max_output_tokens=20,  # Short titles only
                    top_p=0.8,
                    candidate_count=1
                )
            )
            
            if response and response.text:
                title = response.text.strip()
                
                # Clean and validate the title
                title = self._clean_title(title)
                
                if self._is_valid_title(title):
                    print(f"🎯 Generated title: '{title}' for message: '{first_user_message[:50]}...'")
                    return title
                else:
                    print(f"⚠️ Invalid title generated: '{title}', using fallback")
                    return self._generate_fallback_title(first_user_message)
            else:
                print("⚠️ Empty response from Gemini, using fallback title")
                return self._generate_fallback_title(first_user_message)
                
        except Exception as e:
            print(f"⚠️ Title generation failed: {e}")
            return self._generate_fallback_title(first_user_message)
    
    def _clean_title(self, title: str) -> str:
        """Clean and format the generated title"""
        # Remove quotes and extra whitespace
        title = title.strip().strip('"').strip("'").strip()
        
        # Remove common prefixes that AI might add
        prefixes_to_remove = [
            "Başlık:", "Title:", "Sohbet:", "Chat:", 
            "Konu:", "Topic:", "Soru:", "Question:"
        ]
        
        for prefix in prefixes_to_remove:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()
        
        return title
    
    def _is_valid_title(self, title: str) -> bool:
        """Validate if the generated title is appropriate"""
        if not title or len(title.strip()) == 0:
            return False
        
        # Check length (should be reasonable for a title)
        if len(title) < 3 or len(title) > 100:
            return False
        
        # Check if it looks like a proper title (not a sentence)
        if title.endswith('.') and len(title.split()) > 8:
            return False
        
        return True
    
    def _generate_fallback_title(self, first_message: str) -> str:
        """Generate fallback title based on message content"""
        # Extract key words from the message
        words = first_message.strip().split()
        
        if len(words) == 0:
            return f"Sohbet {self._get_current_time()}"
        
        # Take first few meaningful words
        meaningful_words = []
        stop_words = {'ve', 'ile', 'için', 'hakkında', 'ne', 'nasıl', 'neden', 'nedir', 'var', 'mı', 'mi', 'mu', 'mü'}
        
        for word in words[:6]:  # Look at first 6 words
            clean_word = word.strip('.,!?()[]{}').lower()
            if len(clean_word) > 2 and clean_word not in stop_words:
                meaningful_words.append(clean_word.capitalize())
                if len(meaningful_words) >= 3:  # Max 3 words for title
                    break
        
        if meaningful_words:
            title = ' '.join(meaningful_words)
            if len(title) > 50:  # If too long, truncate
                title = title[:47] + "..."
            return title
        else:
            # Last resort - use first words
            first_part = ' '.join(words[:3])
            if len(first_part) > 50:
                first_part = first_part[:47] + "..."
            return first_part or f"Sohbet {self._get_current_time()}"
    
    def _get_current_time(self) -> str:
        """Get current time for fallback titles"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M")


# Global service instance
chat_title_service = ChatTitleService() 