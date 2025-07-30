"""
Response Optimizer Service - Gemini API (Google GenAI) Implementation
Context7 Pattern: STOP→IDENTIFY→VERIFY→CONFIRM→IMPLEMENT→UPDATE→CONFIRM
Multi-step response optimization: analyzing, removing duplicates, formatting
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json

# Context7: Gemini API import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("✅ Gemini API available for response optimization")
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini API not available - falling back to basic optimization")

from app.core.config import settings

# Context7: Structured output models
class ResponseAnalysis(BaseModel):
    """Analysis results from the Response Analyzer"""
    has_duplicates: bool = Field(..., description="Whether response contains duplicate information")
    repetitive_sections: List[str] = Field(default_factory=list, description="List of repetitive content sections")
    clarity_score: float = Field(..., ge=0.0, le=10.0, description="Clarity score from 1-10")
    completeness_score: float = Field(..., ge=0.0, le=10.0, description="Completeness score from 1-10")
    formatting_issues: List[str] = Field(default_factory=list, description="Identified formatting problems")
    key_points: List[str] = Field(default_factory=list, description="Main key points in the response")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Specific improvement suggestions")

class OptimizedResponse(BaseModel):
    """Optimized response from the Response Optimizer"""
    optimized_content: str = Field(..., description="The optimized and polished response content")
    removed_duplicates: List[str] = Field(default_factory=list, description="List of removed duplicate content")
    formatting_improvements: List[str] = Field(default_factory=list, description="Applied formatting improvements")
    clarity_improvements: List[str] = Field(default_factory=list, description="Applied clarity improvements")
    optimization_score: float = Field(..., ge=0.0, le=10.0, description="Overall optimization improvement score")
    processing_notes: str = Field(..., description="Notes about the optimization process")

class ResponseOptimizationResult(BaseModel):
    """Final result combining analysis and optimization"""
    original_response: str = Field(..., description="Original RAG response")
    analysis: ResponseAnalysis = Field(..., description="Analysis results")
    optimized_response: OptimizedResponse = Field(..., description="Optimized response")
    optimization_applied: bool = Field(..., description="Whether optimization was successfully applied")
    processing_time_ms: int = Field(..., description="Time taken for optimization in milliseconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ResponseOptimizerService:
    """Gemini API response optimization service (Context7 verified)"""
    
    def __init__(self):
        self.gemini_available = GEMINI_AVAILABLE
        self.model = None
        if self.gemini_available:
            self._initialize_client()
        else:
            print("⚠️ Response optimization will use fallback patterns")
    
    def _initialize_client(self):
        """Initialize Gemini client for response optimization (Context7)"""
        try:
            gemini_api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                print("⚠️ No Gemini API key found - using fallback optimization")
                self.gemini_available = False
                return
            genai.configure(api_key=gemini_api_key)
            # Context7: Use a more widely available Gemini model 
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Gemini response optimization model initialized successfully")
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini client: {e}")
            self.gemini_available = False
    
    async def analyze_response(self, response_text: str) -> ResponseAnalysis:
        """Analyze RAG response for optimization opportunities (Context7)"""
        if not self.gemini_available or not self.model:
            # Fallback analysis
            return ResponseAnalysis(
                has_duplicates=len(response_text.split()) > 200,  # Simple heuristic
                repetitive_sections=[],
                clarity_score=7.0,
                completeness_score=8.0,
                formatting_issues=["No detailed analysis available"],
                key_points=["Analysis not available"],
                improvement_suggestions=["Use Gemini API for detailed analysis"]
            )
        try:
            # Context7: Define response schema as JSON structure
            analysis_schema = {
                "type": "object",
                "properties": {
                    "has_duplicates": {"type": "boolean"},
                    "repetitive_sections": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "clarity_score": {"type": "number"},
                    "completeness_score": {"type": "number"},
                    "formatting_issues": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "improvement_suggestions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": [
                    "has_duplicates",
                    "clarity_score",
                    "completeness_score"
                ]
            }
            
            analysis_prompt = f"""You are a professional text analysis expert. Analyze the given RAG response.
The user is Turkish, so all content in your response MUST be in TURKISH. However, the JSON keys MUST be in English as specified below.

TASK:
1. **Detect Duplicates**: Find where the same information is repeated.
2. **Assess Clarity**: Evaluate how understandable the response is (1-10).
3. **Check Completeness**: Check for missing information (1-10).
4. **Formatting Issues**: Identify irregular formatting problems.
5. **Key Points**: List the main points in the response.
6. **Improvement Suggestions**: Provide specific improvement suggestions.

RAG RESPONSE (in Turkish):
{response_text}

Provide your response in JSON format. The output must be valid JSON and only contain the JSON object, with no other explanations. 
- **JSON Keys must be in ENGLISH.**
- **JSON Values must be in TURKISH.**
Use the following keys: "has_duplicates", "repetitive_sections", "clarity_score", "completeness_score", "formatting_issues", "key_points", "improvement_suggestions".
Example JSON structure:
{{
  "has_duplicates": true,
  "repetitive_sections": ["tekrarlanan metin 1", "tekrarlanan metin 2"],
  "clarity_score": 8.5,
  "completeness_score": 9.0,
  "formatting_issues": ["sorun1", "sorun2"],
  "key_points": ["ana nokta 1", "ana nokta 2"],
  "improvement_suggestions": ["öneri1", "öneri2"]
}}
"""
            
            # Context7: Simplified generation parameters
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 2048,
            }
            
            # Standard function call format (without types module)
            response = await asyncio.to_thread(
                lambda: self.model.generate_content(
                    analysis_prompt, 
                    generation_config=generation_config
                )
            )
            
            # Extract text content and parse JSON
            content = response.text if hasattr(response, 'text') else str(response)
            
            # Clean the content to ensure it's valid JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
                
            # Parse JSON content
            analysis_result = json.loads(content)
            return ResponseAnalysis(**analysis_result)
            
        except Exception as e:
            print(f"⚠️ Response analysis failed: {str(e)}")
            return ResponseAnalysis(
                has_duplicates=False,
                repetitive_sections=[],
                clarity_score=6.0,
                completeness_score=7.0,
                formatting_issues=[f"Analysis error: {str(e)}"],
                key_points=["Analysis failed"],
                improvement_suggestions=["Manual review recommended"]
            )
    
    async def optimize_response(self, response_text: str, analysis: ResponseAnalysis) -> OptimizedResponse:
        """Optimize RAG response based on analysis (Context7)"""
        if not self.gemini_available or not self.model:
            return OptimizedResponse(
                optimized_content=response_text,  # No optimization
                removed_duplicates=[],
                formatting_improvements=["No optimization available"],
                clarity_improvements=["Use Gemini API for optimization"],
                optimization_score=5.0,
                processing_notes="Fallback: No optimization applied"
            )
        try:
            # Context7: Define response schema as JSON structure
            optimization_schema = {
                "type": "object",
                "properties": {
                    "optimized_content": {"type": "string"},
                    "removed_duplicates": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "formatting_improvements": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "clarity_improvements": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "optimization_score": {"type": "number"},
                    "processing_notes": {"type": "string"}
                },
                "required": [
                    "optimized_content",
                    "optimization_score",
                    "processing_notes"
                ]
            }
            
            optimization_prompt = f"""You are a professional text optimization expert. Improve the RAG response.
The user is Turkish, so all content in your response MUST be in TURKISH. However, the JSON keys MUST be in English as specified below.

OPTIMIZATION TASKS:
1. **Remove Duplicates**: Remove duplicate content, leaving only one version.
2. **Improve Formatting**: Apply a professional business format.
3. **Increase Clarity**: Make it more understandable and fluent.
4. **Organize Structure**: Provide logical flow and organization.

FORMATTING RULES (apply these to the Turkish content):
- **Headings**: Use an emoji and a clear title. DO NOT use asterisks for bolding (e.g., 💡 Öğrenilen Prosedür).
- **Lists**: Organize with bullet points.
- **Steps**: Order with numbered lists.
- **Emphasis**: DO NOT use asterisks for emphasis. Use clear language.
- **Source**: DO NOT include source citations like [Belge X, Slide Y] in the text. This is handled separately.

ORIGINAL RESPONSE (in Turkish):
{response_text}

ANALYSIS FINDINGS:
- Duplicates detected: {analysis.has_duplicates}
- Clarity score: {analysis.clarity_score}/10
- Completeness score: {analysis.completeness_score}/10
- Issues: {', '.join(analysis.formatting_issues)}

Provide your response in JSON format. The output must be valid JSON and only contain the JSON object, with no other explanations.
- **JSON Keys must be in ENGLISH.**
- **JSON Values must be in TURKISH.**
Use the following keys: "optimized_content", "removed_duplicates", "formatting_improvements", "clarity_improvements", "optimization_score", "processing_notes".
Example JSON structure:
{{
  "optimized_content": "optimize edilmiş Türkçe cevap burada...",
  "removed_duplicates": ["kaldırılan Türkçe metin 1", "kaldırılan Türkçe metin 2"],
  "formatting_improvements": ["iyileştirme1", "iyileştirme2"],
  "clarity_improvements": ["netlik1", "netlik2"],
  "optimization_score": 8.5,
  "processing_notes": "Profesyonel formatlama uygulandı ve tekrarlar kaldırıldı"
}}
"""
            
            # Context7: Simplified generation parameters
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 2048,
            }
            
            # Standard function call format (without types module)
            response = await asyncio.to_thread(
                lambda: self.model.generate_content(
                    optimization_prompt, 
                    generation_config=generation_config
                )
            )
            
            # Context7: Use the parsed attribute when response_schema is provided
            if hasattr(response, "parsed") and response.parsed:
                print("✅ Structured output parsed successfully!")
                optimization_result = response.parsed
            else:
                # Fall back to text parsing if structured output failed
                print("⚠️ Structured output not available, falling back to text parsing")
                content = response.text if hasattr(response, 'text') else str(response)
                # Clean the content to ensure it's valid JSON
                content = content.strip()
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                
                print(f"Raw content: {content[:100]}...")
                optimization_result = json.loads(content)
            
            return OptimizedResponse(**optimization_result)
        except Exception as e:
            print(f"⚠️ Response optimization failed: {str(e)}")
            return OptimizedResponse(
                optimized_content=response_text,
                removed_duplicates=[],
                formatting_improvements=[],
                clarity_improvements=[],
                optimization_score=5.0,
                processing_notes=f"Optimization failed: {str(e)}"
            )
    
    async def optimize_rag_response(self, original_response: str) -> ResponseOptimizationResult:
        """
        Complete response optimization workflow (Context7)
        Flow:
        1. User asks question → RAG generates response
        2. Response Analyzer analyzes the response
        3. Response Optimizer optimizes based on analysis
        4. Return polished, professional response
        """
        import time
        start_time = time.time()
        try:
            print(f"🎯 Starting response optimization for {len(original_response)} character response")
            print("📊 Step 1: Analyzing response...")
            analysis = await self.analyze_response(original_response)
            print(f"✅ Analysis complete - Clarity: {analysis.clarity_score}/10, Duplicates: {analysis.has_duplicates}")
            print("⚡ Step 2: Optimizing response...")
            optimized = await self.optimize_response(original_response, analysis)
            print(f"✅ Optimization complete - Score: {optimized.optimization_score}/10")
            processing_time_ms = int((time.time() - start_time) * 1000)
            result = ResponseOptimizationResult(
                original_response=original_response,
                analysis=analysis,
                optimized_response=optimized,
                optimization_applied=self.gemini_available,
                processing_time_ms=processing_time_ms
            )
            print(f"🎉 Response optimization completed in {processing_time_ms}ms")
            return result
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ Response optimization failed: {e}")
            return ResponseOptimizationResult(
                original_response=original_response,
                analysis=ResponseAnalysis(
                    has_duplicates=False,
                    repetitive_sections=[],
                    clarity_score=6.0,
                    completeness_score=7.0,
                    formatting_issues=[f"Error: {str(e)}"],
                    key_points=["Error in analysis"],
                    improvement_suggestions=["Manual review needed"]
                ),
                optimized_response=OptimizedResponse(
                    optimized_content=original_response,
                    removed_duplicates=[],
                    formatting_improvements=[],
                    clarity_improvements=[],
                    optimization_score=5.0,
                    processing_notes=f"Error: {str(e)}"
                ),
                optimization_applied=False,
                processing_time_ms=processing_time_ms
            )

# Global service instance
response_optimizer_service = ResponseOptimizerService()

# Export main function
async def optimize_rag_response(original_response: str) -> ResponseOptimizationResult:
    """
    Main function to optimize RAG responses (Context7)
    Usage:
    result = await optimize_rag_response("Raw RAG response text here...")
    optimized_text = result.optimized_response.optimized_content
    """
    return await response_optimizer_service.optimize_rag_response(original_response) 