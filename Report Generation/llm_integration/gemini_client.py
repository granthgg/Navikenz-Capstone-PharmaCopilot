"""
Google Gemini Client for LLM Integration in PharmaCopilot
Handles communication with Google Gemini API for comprehensive report generation
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Advanced client for interacting with Google Gemini 2.5 Pro API for pharmaceutical report generation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or "AIzaSyAqbz57oRkNc_gwsFgcvjFmA1b-vQu5-7E"
        if not self.api_key:
            logger.warning("No Gemini API key provided. LLM functionality will be disabled.")
            self.client = None
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                # Try Gemini 2.0 Flash Experimental first (latest available)
                try:
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    self.model_name = 'gemini-2.0-flash-exp'
                    logger.info("Gemini 2.0 Flash Experimental client initialized successfully")
                except Exception:
                    # Fallback to Gemini 1.5 Pro if 2.0 Flash Exp is not available
                    self.model = genai.GenerativeModel('gemini-1.5-pro')
                    self.model_name = 'gemini-1.5-pro'
                    logger.info("Gemini 1.5 Pro client initialized as fallback")
                
                self.client = True
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
                self.model = None
    
    def is_available(self) -> bool:
        """Check if the Gemini client is available"""
        return self.client is not None and self.model is not None
    
    def generate_comprehensive_report(self, query: str, context: List[Dict[str, Any]], 
                                    report_type: str = "quality_control", 
                                    collected_data: Dict[str, Any] = None,
                                    use_compact_mode: bool = False) -> Dict[str, Any]:
        """
        Generate a comprehensive pharmaceutical report using Gemini 2.5 Pro
        """
        if not self.is_available():
            return {
                'status': 'error',
                'error': 'Gemini client not available',
                'content': self._generate_fallback_content(report_type)
            }
        
        try:
            # Build comprehensive context (compact mode for rate limit management)
            context_text = self._build_rich_context(context, collected_data, compact=use_compact_mode)
            
            # Create advanced system prompt (shorter for compact mode)
            system_prompt = self._get_advanced_system_prompt(report_type, compact=use_compact_mode)
            
            # Create detailed user prompt (essential info only in compact mode)
            user_prompt = self._build_comprehensive_prompt(query, context_text, report_type, collected_data, compact=use_compact_mode)
            
            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate content with Gemini (with retry logic)
            max_retries = 3
            base_delay = 15  # Start with 15 seconds delay
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                            top_p=0.8,
                            top_k=40,
                            max_output_tokens=4000,
                        )
                    )
                    
                    content = response.text if response.text else ""
                    
                    # Clean and format content
                    cleaned_content = self._clean_and_format_content(content)
                    
                    return {
                        'status': 'success',
                        'content': cleaned_content,
                        'model_used': getattr(self, 'model_name', 'gemini-2.0-flash-exp'),
                        'tokens_used': self._estimate_token_usage(full_prompt, content),
                        'attempt': attempt + 1
                    }
                    
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "quota" in error_str.lower():
                        # Rate limit hit
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Rate limit hit, retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            continue
                        elif not use_compact_mode and attempt == max_retries - 1:
                            # Last attempt, try compact mode
                            logger.warning("Final attempt with compact mode to reduce token usage")
                            return self.generate_comprehensive_report(query, context, report_type, collected_data, use_compact_mode=True)
                        else:
                            logger.error(f"Rate limit exceeded after {max_retries} attempts, falling back to template")
                            break
                    else:
                        # Other error, don't retry
                        logger.error(f"Non-rate-limit error: {error_str}")
                        break
            
        except Exception as e:
            logger.error(f"Error generating report with Gemini: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'content': self._generate_fallback_content(report_type)
            }
    
    def _build_rich_context(self, context: List[Dict[str, Any]], collected_data: Dict[str, Any], compact: bool = False) -> str:
        """Build rich context from historical data and current metrics"""
        context_parts = []
        
        # Add historical context (limit in compact mode)
        if context:
            context_parts.append("=== HISTORICAL DATA ANALYSIS ===")
            context_limit = 2 if compact else 5
            for i, item in enumerate(context[:context_limit]):
                if isinstance(item, dict):
                    if 'content' in item:
                        content_limit = 150 if compact else 300
                        context_parts.append(f"Historical Record {i+1}: {str(item['content'])[:content_limit]}")
                    elif 'data' in item:
                        content_limit = 150 if compact else 300
                        context_parts.append(f"Data Point {i+1}: {str(item['data'])[:content_limit]}")
        
        # Add current data analysis
        if collected_data:
            context_parts.append("\n=== CURRENT REAL-TIME DATA ===")
            
            # Classification data
            if 'classification' in collected_data and 'error' not in collected_data['classification']:
                class_data = collected_data['classification']
                context_parts.append(f"Defect Probability: {class_data.get('defect_probability', 'N/A')}")
                context_parts.append(f"Risk Level: {class_data.get('risk_level', 'N/A')}")
            
            # Forecasting data
            if 'forecasting' in collected_data and 'error' not in collected_data['forecasting']:
                forecast_data = collected_data['forecasting']
                if 'forecast' in forecast_data and len(forecast_data['forecast']) > 0:
                    next_forecast = forecast_data['forecast'][0]
                    if 'sensors' in next_forecast:
                        sensors = next_forecast['sensors']
                        context_parts.append(f"Predicted Waste: {sensors.get('waste', 'N/A')}")
                        context_parts.append(f"Predicted Production: {sensors.get('produced', 'N/A')}")
            
            # Quality data
            if 'quality' in collected_data and 'error' not in collected_data['quality']:
                quality_data = collected_data['quality']
                context_parts.append(f"Quality Classification: {quality_data.get('quality_class', 'N/A')}")
            
            # RL Actions
            if 'rl_actions' in collected_data and 'error' not in collected_data['rl_actions']:
                rl_data = collected_data['rl_actions']
                context_parts.append(f"Recommended Actions: {rl_data.get('recommended_actions', 'N/A')}")
        
        return "\n".join(context_parts)
    
    def _get_advanced_system_prompt(self, report_type: str, compact: bool = False) -> str:
        """Get comprehensive system prompt for Gemini"""
        if compact:
            # Shorter system prompt for rate limit management
            base_prompt = """You are PharmaCopilot AI, a pharmaceutical manufacturing analyst specializing in quality control and regulatory compliance.

MISSION: Generate concise, professional pharmaceutical manufacturing reports.

REQUIREMENTS:
• Professional pharmaceutical terminology
• Data-driven insights with specific metrics
• Regulatory compliance focus
• Risk-based analysis with actionable recommendations
• Clear executive summary and technical analysis"""
        else:
            base_prompt = """You are PharmaCopilot AI, an expert pharmaceutical manufacturing analyst and quality control specialist with deep expertise in:

• FDA 21 CFR Part 11 regulatory compliance
• ICH Q7 Good Manufacturing Practice guidelines  
• Statistical Process Control (SPC) and Quality by Design (QbD)
• Pharmaceutical process optimization and risk management
• Real-time data analysis and predictive analytics
• Regulatory documentation and audit trail management

MISSION: Generate comprehensive, professional, regulatory-compliant reports for pharmaceutical manufacturing operations.

REPORT REQUIREMENTS:
✓ Professional medical/pharmaceutical tone and terminology
✓ Data-driven insights with specific metrics and KPIs
✓ Regulatory compliance focus (21 CFR Part 11, ICH guidelines)
✓ Risk-based analysis with actionable recommendations
✓ Statistical significance and process capability assessment
✓ Clear executive summary for management decision-making
✓ Detailed technical analysis for quality professionals
✓ Comprehensive trend analysis and predictive insights

FORMAT STANDARDS:
• Use professional medical/scientific writing style
• Include specific numerical data and statistical analysis
• Provide clear section headers and bullet points
• Add tables for key metrics where appropriate
• Include regulatory references and compliance statements
• Ensure actionable recommendations with priority levels
• Add risk assessment matrix and mitigation strategies"""

        report_specific = {
            'quality_control': """
FOCUS: Quality Control & Defect Analysis
• Real-time defect probability assessment and trend analysis
• Quality classification accuracy and confidence metrics
• Critical Control Point (CCP) monitoring and compliance
• Statistical Process Control chart analysis and capability studies
• Root cause analysis and corrective/preventive action recommendations
• Quality system integration and validation status
• Regulatory compliance verification and audit readiness""",
            
            'batch_record': """
FOCUS: Batch Record Analysis & Performance Review  
• Batch disposition and quality assessment
• Process parameter compliance and deviation analysis
• Yield analysis and material consumption efficiency
• Equipment performance and utilization metrics
• Environmental monitoring and control verification
• Documentation completeness and electronic record integrity""",
            
            'excellence': """
FOCUS: Manufacturing Excellence & Optimization
• Overall Equipment Effectiveness (OEE) analysis
• Process optimization opportunities and continuous improvement
• Lean manufacturing implementation and waste reduction
• Technology integration and digital transformation readiness
• Operational excellence benchmarking and best practice implementation
• Strategic recommendations for competitive advantage""",
            
            'compliance': """
FOCUS: Regulatory Compliance & Audit Readiness
• 21 CFR Part 11 electronic records compliance verification
• Data integrity assessment (ALCOA+ principles)
• Audit trail completeness and change control validation
• Regulatory inspection readiness and documentation review
• Quality system effectiveness and CAPA management
• Risk management compliance and validation status"""
        }
        
        specific_guidance = report_specific.get(report_type, "Generate a comprehensive pharmaceutical manufacturing analysis report.")
        
        return f"{base_prompt}\n\n{specific_guidance}"
    
    def _build_comprehensive_prompt(self, query: str, context_text: str, report_type: str, collected_data: Dict[str, Any], compact: bool = False) -> str:
        """Build comprehensive prompt with all available data"""
        
        # Extract key metrics for prompt with detailed analysis
        metrics_analysis = self._extract_detailed_metrics(collected_data)
        
        if compact:
            # Shorter prompt for rate limit management
            return f"""
GENERATE {report_type.upper().replace('_', ' ')} REPORT

REQUEST: {query}

KEY METRICS:
• Defect Probability: {metrics_analysis.get('defect_probability', 'N/A')}
• Quality Class: {metrics_analysis.get('quality_class', 'Unknown')}
• Risk Level: {metrics_analysis.get('risk_level', 'N/A')}
• Predicted Waste: {metrics_analysis.get('predicted_waste', 'N/A')} units

CONTEXT: {context_text[:500] if context_text else 'No historical data'}

REQUIRED SECTIONS:
1. Executive Summary
2. Key Metrics Table
3. Risk Assessment
4. Immediate Actions

Use ONLY actual data provided. Professional pharmaceutical tone required."""
        
        # Full detailed prompt for normal operation
        
        return f"""
GENERATE COMPREHENSIVE {report_type.upper().replace('_', ' ')} REPORT

EXECUTIVE REQUEST: {query}

REAL-TIME MANUFACTURING DATA ANALYSIS:
{metrics_analysis}

HISTORICAL CONTEXT & PATTERNS:
{context_text}

CRITICAL REQUIREMENT: Use ONLY the actual data provided above. Do not invent numbers or metrics.

REPORT STRUCTURE REQUIRED:

# COMPREHENSIVE {report_type.upper().replace('_', ' ')} REPORT

## EXECUTIVE SUMMARY
• Analyze the ACTUAL defect probability: {metrics_analysis.get('defect_probability', 'N/A')}
• Current quality classification: {metrics_analysis.get('quality_class', 'Unknown')}  
• Risk assessment based on REAL data: {metrics_analysis.get('risk_level', 'N/A')}
• Process efficiency from ACTUAL waste prediction: {metrics_analysis.get('predicted_waste', 'N/A')} units

## KEY PERFORMANCE INDICATORS
Create a detailed table using the REAL metrics provided:

| Metric | Current Value | Target | Status | Trend | Action Required |
|--------|---------------|---------|--------|-------|-----------------|
| Defect Probability | {metrics_analysis.get('defect_probability', 'N/A')} | < 5% | [Analyze based on actual value] | [Determine from data] | [Based on real metrics] |
| Quality Class | {metrics_analysis.get('quality_class', 'Unknown')} | High | [Assess actual status] | [Real trend] | [Specific actions] |
| Predicted Waste | {metrics_analysis.get('predicted_waste', 'N/A')} units | < 10% of production | [Real status] | [Actual trend] | [Data-driven actions] |
| Production Forecast | {metrics_analysis.get('predicted_production', 'N/A')} units | Meet targets | [Current status] | [Trend analysis] | [Required actions] |

## DETAILED TECHNICAL ANALYSIS
### Process Performance Assessment (Based on Real Data)
• ACTUAL defect probability analysis: {metrics_analysis.get('defect_probability', 'No data available')}
• REAL waste prediction impact: {metrics_analysis.get('predicted_waste', 'No forecast data')} units
• Current sensor readings: {metrics_analysis.get('sensor_summary', 'No sensor data available')}
• Process efficiency calculation from real metrics

### Risk Assessment & Mitigation  
• Current risk level: {metrics_analysis.get('risk_level', 'Assessment pending')}
• Risk factors based on actual defect probability
• Mitigation strategies for current risk profile

## ACTIONABLE RECOMMENDATIONS (Data-Driven)
### Immediate Actions (0-4 hours)
[Generate based on actual defect probability and risk level]

### Short-term Actions (24-48 hours)  
[Base on real waste predictions and quality classification]

### Strategic Actions (1-4 weeks)
[Derive from actual performance trends and forecasts]

## PREDICTIVE INSIGHTS (Using Real Forecast Data)
• Next period waste prediction: {metrics_analysis.get('predicted_waste', 'No forecast')} units
• Production forecast: {metrics_analysis.get('predicted_production', 'No forecast')} units  
• Forecast horizon: {metrics_analysis.get('forecast_horizon', 'N/A')} timesteps
• Trend analysis based on historical context

REQUIREMENTS:
• Reference the EXACT metrics provided - never invent numbers
• If data shows 'N/A' or 'Unknown', acknowledge missing data
• Provide specific analysis of the actual defect probability: {metrics_analysis.get('defect_probability', 'N/A')}
• Use the real predicted waste amount: {metrics_analysis.get('predicted_waste', 'N/A')} units
• Base all recommendations on the actual data quality and completeness
• Include pharmaceutical regulatory compliance context
• Maintain professional scientific accuracy
        """
    
    def _extract_detailed_metrics(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed metrics with comprehensive analysis"""
        metrics = {
            'defect_probability': 'N/A',
            'quality_class': 'Unknown',
            'risk_level': 'Unknown',
            'predicted_waste': 'N/A',
            'predicted_production': 'N/A',
            'forecast_horizon': 'N/A',
            'sensor_summary': 'No sensor data available',
            'data_sources': [],
            'data_quality_score': 0
        }
        
        if not collected_data:
            return metrics
        
        metrics['data_sources'] = list(collected_data.keys())
        successful_sources = 0
        
        try:
            # Extract classification data
            if 'classification' in collected_data:
                class_data = collected_data['classification']
                if isinstance(class_data, dict) and 'error' not in class_data:
                    metrics['defect_probability'] = class_data.get('defect_probability', 'N/A')
                    metrics['risk_level'] = class_data.get('risk_level', 'Unknown')
                    successful_sources += 1
                    
                    # Determine quality class based on defect probability
                    if isinstance(metrics['defect_probability'], (int, float)):
                        if metrics['defect_probability'] < 0.05:
                            metrics['quality_class'] = 'Excellent'
                        elif metrics['defect_probability'] < 0.15:
                            metrics['quality_class'] = 'Good'
                        elif metrics['defect_probability'] < 0.3:
                            metrics['quality_class'] = 'Acceptable'
                        else:
                            metrics['quality_class'] = 'Poor - Requires Attention'
            
            # Extract forecasting data  
            if 'forecasting' in collected_data:
                forecast_data = collected_data['forecasting']
                if isinstance(forecast_data, dict) and 'error' not in forecast_data:
                    metrics['forecast_horizon'] = forecast_data.get('forecast_horizon', 'N/A')
                    forecast_list = forecast_data.get('forecast', [])
                    
                    if forecast_list and len(forecast_list) > 0:
                        first_forecast = forecast_list[0]
                        if 'sensors' in first_forecast:
                            sensors = first_forecast['sensors']
                            metrics['predicted_waste'] = sensors.get('waste', 'N/A')
                            metrics['predicted_production'] = sensors.get('produced', 'N/A')
                            
                            # Create sensor summary
                            sensor_data = []
                            for key, value in sensors.items():
                                if isinstance(value, (int, float)):
                                    sensor_data.append(f"{key}: {value:.2f}")
                            metrics['sensor_summary'] = ", ".join(sensor_data) if sensor_data else "No valid sensor readings"
                    
                    successful_sources += 1
            
            # Extract quality data
            if 'quality' in collected_data:
                quality_data = collected_data['quality']
                if isinstance(quality_data, dict) and 'error' not in quality_data:
                    quality_class = quality_data.get('quality_class')
                    if quality_class and quality_class != 'Unknown':
                        metrics['quality_class'] = quality_class
                    successful_sources += 1
            
            # Extract RL actions
            if 'rl_actions' in collected_data:
                rl_data = collected_data['rl_actions'] 
                if isinstance(rl_data, dict) and 'error' not in rl_data:
                    successful_sources += 1
            
            # Calculate data quality score
            total_sources = len(collected_data)
            metrics['data_quality_score'] = (successful_sources / total_sources) * 100 if total_sources > 0 else 0
            
        except Exception as e:
            logger.error(f"Error extracting detailed metrics: {e}")
            metrics['extraction_error'] = str(e)
        
        return metrics
    
    def _clean_and_format_content(self, content: str) -> str:
        """Clean and format the generated content"""
        if not content:
            return content
        
        # Remove any potential markdown artifacts from Gemini
        content = content.strip()
        
        # Ensure proper spacing around headers
        import re
        content = re.sub(r'\n#+\s*([^\n]+)', r'\n\n# \1\n', content)
        content = re.sub(r'\n#{2,}\s*([^\n]+)', r'\n\n## \1\n', content)
        content = re.sub(r'\n#{3,}\s*([^\n]+)', r'\n\n### \1\n', content)
        
        # Clean up multiple newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure bullet points are properly formatted
        content = re.sub(r'\n•\s*', '\n- ', content)
        content = re.sub(r'\n\*\s*', '\n- ', content)
        
        return content.strip()
    
    def _estimate_token_usage(self, prompt: str, response: str) -> int:
        """Estimate token usage for tracking"""
        # Rough estimation: ~4 characters per token
        return (len(prompt) + len(response)) // 4
    
    def _generate_fallback_content(self, report_type: str) -> str:
        """Generate fallback content when Gemini is not available"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# {report_type.replace('_', ' ').title()} Report

**Generated:** {timestamp}
**Status:** Fallback Mode - Gemini API Unavailable

## Executive Summary
This report was generated in fallback mode due to Gemini API service unavailability.

## Current Status
- System Status: Monitoring
- Data Collection: Active
- Analysis: Manual review recommended

## Recommendations
- Verify Gemini API service connectivity
- Check API key configuration
- Perform manual analysis
- Contact system administrator

## Compliance Status
- Documentation: Complete
- Audit Trail: Maintained
- Manual verification required

*This is an automated fallback response. Manual review recommended.*"""

    # Legacy compatibility method for existing code
    def generate_rag_report(self, query: str, context: List[Dict[str, Any]], 
                           report_type: str = "quality_control", 
                           model: str = "gemini-2.0-flash-exp") -> Dict[str, Any]:
        """Legacy method for compatibility with existing code"""
        return self.generate_comprehensive_report(query, context, report_type)
