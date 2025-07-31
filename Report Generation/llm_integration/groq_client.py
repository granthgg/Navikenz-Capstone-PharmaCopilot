"""
Groq Client for LLM Integration in PharmaCopilot
Handles communication with Groq API for report generation
"""

import os
import logging
from typing import Dict, Any, List, Optional
from groq import Groq

logger = logging.getLogger(__name__)

class GroqClient:
    """
    Client for interacting with Groq API for pharmaceutical report generation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            logger.warning("No Groq API key provided. LLM functionality will be disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if the Groq client is available"""
        return self.client is not None
    
    def generate_rag_report(self, query: str, context: List[Dict[str, Any]], 
                           report_type: str = "quality_control", 
                           model: str = "llama3-70b-8192") -> Dict[str, Any]:
        """
        Generate a report using RAG (Retrieval-Augmented Generation)
        """
        if not self.client:
            return {
                'status': 'error',
                'error': 'Groq client not available',
                'content': self._generate_fallback_content(report_type)
            }
        
        try:
            # Build context string
            context_text = self._build_context_text(context)
            
            # Create system prompt
            system_prompt = self._get_system_prompt(report_type)
            
            # Create user prompt
            user_prompt = self._build_user_prompt(query, context_text, report_type)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Clean content (remove emojis and formatting issues)
            cleaned_content = self._clean_content(content)
            
            return {
                'status': 'success',
                'content': cleaned_content,
                'model_used': model,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating report with Groq: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'content': self._generate_fallback_content(report_type)
            }
    
    def _build_context_text(self, context: List[Dict[str, Any]]) -> str:
        """Build context text from context items"""
        if not context:
            return "No historical context available."
        
        context_parts = []
        for item in context:
            if isinstance(item, dict):
                if 'content' in item:
                    context_parts.append(str(item['content']))
                elif 'data' in item:
                    context_parts.append(str(item['data']))
                else:
                    context_parts.append(str(item))
        
        return "\\n\\n".join(context_parts[:3])  # Limit context for efficiency
    
    def _get_system_prompt(self, report_type: str) -> str:
        """Get system prompt based on report type"""
        base_prompt = """You are an expert pharmaceutical manufacturing analyst specializing in quality control and process optimization. 

Generate professional, regulatory-compliant reports for pharmaceutical manufacturing operations. Your reports should be:
- Factual and data-driven
- Regulatory compliant (21 CFR Part 11)
- Professional in tone
- Free of emojis or decorative elements
- Focused on actionable insights
- Technically accurate

Use proper headings, bullet points, and tables where appropriate. Include specific metrics, risk assessments, and recommendations."""

        report_specific = {
            'quality_control': "Focus on defect probability, quality classifications, risk assessment, and quality control recommendations.",
            'batch_record': "Analyze batch performance, process parameters, yield analysis, and batch disposition recommendations.",
            'deviation': "Investigate process deviations, root cause analysis, corrective actions, and preventive measures.",
            'oee': "Assess Overall Equipment Effectiveness, availability, performance, and quality metrics.",
            'compliance': "Review regulatory compliance, audit readiness, data integrity, and validation status.",
            'excellence': "Evaluate manufacturing excellence, process optimization, and continuous improvement opportunities."
        }
        
        specific_guidance = report_specific.get(report_type, "Generate a comprehensive manufacturing report.")
        
        return f"{base_prompt}\\n\\n{specific_guidance}"
    
    def _build_user_prompt(self, query: str, context_text: str, report_type: str) -> str:
        """Build user prompt with query and context"""
        return f"""Generate a comprehensive {report_type.replace('_', ' ')} report based on the following:

QUERY: {query}

HISTORICAL CONTEXT:
{context_text}

Please generate a professional pharmaceutical manufacturing report with the following sections:
1. Executive Summary
2. Current Status Assessment
3. Key Metrics Analysis
4. Risk Assessment
5. Recommendations
6. Compliance Status

Focus on actionable insights and regulatory compliance. Do not use emojis or decorative elements."""
    
    def _clean_content(self, content: str) -> str:
        """Clean content by removing emojis and unwanted formatting"""
        if not content:
            return content
        
        # Remove common emojis - basic approach
        emoji_patterns = [
            '🏭', '📊', '🎯', '📈', '🔍', '✅', '⚠️', '🔴', '🟡', '🟢', '🔵',
            '📋', '🛡️', '🚨', '⚡', '🔧', '👥', '📞', '🎯', '📚', '🌟',
            '🏢', '⚙️', '🔌', '🛠️', '📄', '💡', '🎨', '🚀', '💪', '🎉',
            '📱', '💻', '🖥️', '📺', '⌚', '📷', '📹', '🎵', '🎶', '🎤'
        ]
        
        for emoji in emoji_patterns:
            content = content.replace(emoji, '')
        
        # Clean up multiple spaces and newlines
        import re
        content = re.sub(r'\\s+', ' ', content)
        content = re.sub(r'\\n\\s*\\n', '\\n\\n', content)
        
        return content.strip()
    
    def _generate_fallback_content(self, report_type: str) -> str:
        """Generate fallback content when LLM is not available"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# {report_type.replace('_', ' ').title()} Report

**Generated:** {timestamp}
**Status:** Fallback Mode - LLM Unavailable

## Executive Summary
This report was generated in fallback mode due to LLM service unavailability.

## Current Status
- System Status: Monitoring
- Data Collection: Active
- Analysis: Manual review recommended

## Recommendations
- Verify LLM service connectivity
- Perform manual analysis
- Contact system administrator
- Review data manually

## Compliance Status
- Documentation: Complete
- Audit Trail: Maintained
- Manual verification required

*This is an automated fallback response. Manual review recommended.*"""
