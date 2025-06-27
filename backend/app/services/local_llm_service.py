"""
Local LLM Service - Completely Free
Uses HuggingFace Transformers for local inference
Context7 Verified Implementation - 2024
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig
)
import gc

logger = logging.getLogger(__name__)

class LocalLLMService:
    """
    Local LLM Service using free HuggingFace models
    Supports multiple model sizes based on available hardware
    """
    
    def __init__(self, model_name: str = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # Auto-select model based on hardware
        if model_name is None:
            model_name = self._select_best_model()
        
        self.model_name = model_name
        self.max_length = 512  # Adjust based on model
        self.is_loaded = False
        
        logger.info(f"🤖 Local LLM Service initialized")
        logger.info(f"📱 Device: {self.device}")
        logger.info(f"🎯 Selected model: {self.model_name}")
    
    def _select_best_model(self) -> str:
        """Auto-select best model based on available hardware"""
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"🔥 CUDA available - GPU Memory: {gpu_memory:.1f}GB")
            
            if gpu_memory > 12:
                return "microsoft/DialoGPT-medium"  # ~1.4GB
            elif gpu_memory > 8:
                return "microsoft/DialoGPT-small"   # ~350MB
            else:
                return "distilgpt2"                 # ~250MB
        else:
            logger.info("💻 Using CPU - selecting lightweight model")
            return "distilgpt2"  # Very lightweight for CPU
    
    async def load_model(self) -> bool:
        """Load the selected model and tokenizer"""
        if self.is_loaded:
            logger.info("✅ Model already loaded")
            return True
        
        try:
            logger.info(f"🔄 Loading model: {self.model_name}")
            
            # Configure for memory efficiency
            if self.device == "cuda":
                # Use 8-bit quantization for GPU to save memory
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0,
                    llm_int8_has_fp16_weight=False,
                )
                model_kwargs = {
                    "quantization_config": quantization_config,
                    "device_map": "auto",
                    "torch_dtype": torch.float16
                }
            else:
                model_kwargs = {"torch_dtype": torch.float32}
            
            # Load tokenizer
            self.tokenizer = await asyncio.to_thread(
                AutoTokenizer.from_pretrained,
                self.model_name,
                padding_side="left"
            )
            
            # Add pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = await asyncio.to_thread(
                AutoModelForCausalLM.from_pretrained,
                self.model_name,
                **model_kwargs
            )
            
            # Create pipeline for text generation
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                do_sample=True,
                temperature=0.7,
                max_length=self.max_length,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            self.is_loaded = True
            logger.info(f"✅ Model loaded successfully: {self.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False
    
    async def generate_response(
        self, 
        prompt: str, 
        context: str = None,
        max_new_tokens: int = 150,
        temperature: float = 0.7
    ) -> str:
        """Generate response using the local model"""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Build the full prompt
            if context:
                full_prompt = self._build_rag_prompt(prompt, context)
            else:
                full_prompt = self._build_simple_prompt(prompt)
            
            logger.info(f"🤖 Generating response for: '{prompt[:50]}...'")
            
            # Generate response
            outputs = await asyncio.to_thread(
                self.pipeline,
                full_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                num_return_sequences=1,
                return_full_text=False
            )
            
            response = outputs[0]['generated_text'].strip()
            
            # Clean up response
            response = self._clean_response(response)
            
            logger.info(f"✅ Generated response ({len(response)} chars)")
            return response
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"
    
    def _build_rag_prompt(self, question: str, context: str) -> str:
        """Build a RAG-style prompt with context"""
        return f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Answer:"""
    
    def _build_simple_prompt(self, question: str) -> str:
        """Build a simple prompt without context"""
        return f"""Question: {question}

Answer:"""
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the generated response"""
        # Remove common artifacts
        response = response.replace("<|endoftext|>", "")
        response = response.replace("[PAD]", "")
        
        # Split by common stopping points
        for stop_phrase in ["\n\nQuestion:", "\nQuestion:", "Context:", "\n\n\n"]:
            if stop_phrase in response:
                response = response.split(stop_phrase)[0]
        
        # Clean up whitespace
        response = response.strip()
        
        # If response is too short, add a fallback
        if len(response) < 10:
            response = "I need more information to provide a comprehensive answer to your question."
        
        return response
    
    async def answer_with_rag(
        self, 
        question: str, 
        retrieved_docs: List[Dict[str, Any]],
        max_context_length: int = 1000
    ) -> Dict[str, Any]:
        """Answer question using RAG (Retrieval-Augmented Generation)"""
        try:
            # Build context from retrieved documents
            context_parts = []
            total_length = 0
            
            for i, doc in enumerate(retrieved_docs):
                content = doc.get('content', '')
                if total_length + len(content) < max_context_length:
                    context_parts.append(f"[Source {i+1}] {content}")
                    total_length += len(content)
                else:
                    break
            
            context = "\n\n".join(context_parts)
            
            # Generate response
            response = await self.generate_response(
                prompt=question,
                context=context,
                max_new_tokens=200,
                temperature=0.3  # Lower temperature for more focused answers
            )
            
            return {
                'answer': response,
                'sources_used': len(context_parts),
                'total_sources': len(retrieved_docs),
                'context_length': len(context),
                'model_used': self.model_name
            }
            
        except Exception as e:
            logger.error(f"❌ RAG answer failed: {e}")
            return {
                'answer': f"I apologize, but I encountered an error: {str(e)}",
                'sources_used': 0,
                'total_sources': len(retrieved_docs),
                'context_length': 0,
                'model_used': self.model_name
            }
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        model_info = {
            'model_name': self.model_name,
            'device': self.device,
            'is_loaded': self.is_loaded,
            'max_length': self.max_length
        }
        
        if self.is_loaded and torch.cuda.is_available():
            model_info.update({
                'gpu_memory_allocated': f"{torch.cuda.memory_allocated() / 1024**3:.2f}GB",
                'gpu_memory_reserved': f"{torch.cuda.memory_reserved() / 1024**3:.2f}GB"
            })
        
        return model_info
    
    async def unload_model(self) -> bool:
        """Unload model to free memory"""
        try:
            if self.is_loaded:
                logger.info("🗑️ Unloading model...")
                
                del self.model
                del self.tokenizer
                del self.pipeline
                
                self.model = None
                self.tokenizer = None
                self.pipeline = None
                self.is_loaded = False
                
                # Clear cache
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                logger.info("✅ Model unloaded successfully")
                return True
            else:
                logger.info("ℹ️ No model loaded")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to unload model: {e}")
            return False

# Global instance
local_llm_service = LocalLLMService() 