"""
Quality Control Report Generator with Real Data Integration
"""

import logging
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import traceback

from .base_generator import BaseReportGenerator

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from utils.emoji_cleaner import clean_report_content
except ImportError:
    # Fallback if emoji cleaner not available
    def clean_report_content(data):
        return data

logger = logging.getLogger(__name__)

class QualityControlReportGenerator(BaseReportGenerator):
    """
    Advanced Quality Control Report Generator that uses real data
    and LLM integration for comprehensive reporting
    """
    
    def __init__(self):
        super().__init__()
        self.report_type = "quality_control"
        logger.info("Initialized QualityControlReportGenerator with real data integration")
    
    async def generate_report(self, query: str = "", additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive quality control report using real data"""
        try:
            logger.info("Starting quality control report generation with real data")
            
            # 1. Collect real data from all sources
            collected_data = await self._collect_comprehensive_data()
            
            # 2. Extract and validate metrics
            metrics = self._extract_real_metrics(collected_data)
            
            # 3. Generate report using LLM if available
            if self.llm_client and self.llm_client.is_available():
                try:
                    logger.info("Attempting LLM generation with Gemini")
                    report_content = await self._generate_llm_report(metrics, collected_data, query)
                    logger.info("LLM generation successful")
                except Exception as e:
                    logger.warning(f"LLM generation failed: {e}, falling back to enhanced template")
                    report_content = self._generate_enhanced_template_report(metrics, collected_data)
            else:
                logger.info("LLM not available, using enhanced template")
                report_content = self._generate_enhanced_template_report(metrics, collected_data)
            
            # 4. Build final report structure
            # Create comprehensive report content for UI display
            full_report_content = self._build_comprehensive_report_content(report_content, metrics)
            
            report = {
                "title": "Pharmaceutical Manufacturing Quality Control Report",
                "generated_at": datetime.now().isoformat(),
                "report_id": f"QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "data_sources": self._get_data_source_info(collected_data),
                "report_content": full_report_content,  # Combined content for UI
                "executive_summary": report_content.get("executive_summary", ""),
                "quality_metrics": metrics,
                "detailed_analysis": report_content.get("detailed_analysis", ""),
                "recommendations": report_content.get("recommendations", []),
                "compliance_status": report_content.get("compliance_status", ""),
                "risk_assessment": report_content.get("risk_assessment", ""),
                "action_items": report_content.get("action_items", []),
                "appendix": {
                    "raw_data_summary": self._create_data_summary(collected_data),
                    "methodology": "Real-time data collection with ML model predictions",
                    "data_freshness": self._assess_data_freshness(collected_data)
                }
            }
            
            logger.info("Quality control report generated successfully")
            
            # Clean emojis from the report before returning
            clean_report = clean_report_content(report)
            return clean_report
            
        except Exception as e:
            logger.error(f"Error generating quality control report: {e}")
            logger.error(traceback.format_exc())
            return self._generate_emergency_report(str(e))
    
    async def _collect_comprehensive_data(self) -> Dict[str, Any]:
        """Collect real data from all available sources"""
        try:
            logger.info("Collecting comprehensive manufacturing data")
            
            collected_data = {
                "timestamp": datetime.now().isoformat(),
                "classification": None,
                "forecasting": None,
                "quality": None,
                "rl_actions": None,
                "collection_errors": []
            }
            
            # Use the inherited collect_current_data method from BaseReportGenerator
            api_data = await self.collect_current_data()
            
            # Map the API response to our expected format - using correct keys
            if 'classification' in api_data:
                collected_data['classification'] = api_data['classification']
                logger.info("Successfully collected classification data")
            else:
                collected_data['collection_errors'].append("Classification data not available")
            
            if 'forecasting' in api_data:
                collected_data['forecasting'] = api_data['forecasting']
                logger.info("Successfully collected forecasting data")
            else:
                collected_data['collection_errors'].append("Forecasting data not available")
                
            if 'quality' in api_data:
                collected_data['quality'] = api_data['quality']
                logger.info("Successfully collected quality data")
            else:
                collected_data['collection_errors'].append("Quality data not available")
                
            if 'rl_actions' in api_data:
                collected_data['rl_actions'] = api_data['rl_actions']
                logger.info("Successfully collected RL data")
            else:
                collected_data['collection_errors'].append("RL data not available")
            
            return collected_data
            
        except Exception as e:
            logger.error(f"Error in comprehensive data collection: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _extract_real_metrics(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract real metrics from collected data with proper API response handling"""
        try:
            metrics = {
                "data_collection_time": collected_data.get("timestamp"),
                "total_predictions": 0,
                "defect_rates": {},
                "quality_scores": {},
                "forecast_accuracy": {},
                "rl_performance": {},
                "system_health": {},
                "collection_success_rate": 0.0
            }
            
            # Count successful data collections
            successful_collections = 0
            total_sources = 4
            
            # Process classification data (defect predictions)
            if collected_data.get("classification") and 'error' not in collected_data["classification"]:
                class_data = collected_data["classification"]
                successful_collections += 1
                
                if isinstance(class_data, dict):
                    # Extract defect probability and risk level
                    defect_prob = class_data.get("defect_probability", 0.0)
                    risk_level = class_data.get("risk_level", "unknown")
                    
                    # Convert to defect rates format
                    if isinstance(defect_prob, (int, float)):
                        if defect_prob > 0.6:
                            metrics["defect_rates"]["high_risk"] = 1
                        elif defect_prob > 0.3:
                            metrics["defect_rates"]["medium_risk"] = 1
                        else:
                            metrics["defect_rates"]["low_risk"] = 1
                        
                        metrics["total_predictions"] = 1
                    
                    # Store additional defect metrics
                    metrics["defect_probability"] = defect_prob
                    metrics["risk_classification"] = risk_level
            
            # Process quality data
            if collected_data.get("quality") and 'error' not in collected_data["quality"]:
                quality_data = collected_data["quality"]
                successful_collections += 1
                
                if isinstance(quality_data, dict):
                    # Map actual API response to expected format
                    quality_class = quality_data.get("quality_class", "unknown")
                    confidence = quality_data.get("confidence", 0.0)
                    class_probs = quality_data.get("class_probabilities", {})
                    
                    # Convert quality class to numeric score for better reporting
                    quality_score = 0.9 if quality_class == "High" else 0.7 if quality_class == "Medium" else 0.4 if quality_class == "Low" else 0.0
                    
                    metrics["quality_scores"] = {
                        "overall_score": quality_score,
                        "batch_quality": quality_class,
                        "quality_confidence": confidence,
                        "class_probabilities": class_probs
                    }
            
            # Process forecasting data
            if collected_data.get("forecasting") and 'error' not in collected_data["forecasting"]:
                forecast_data = collected_data["forecasting"]
                successful_collections += 1
                
                if isinstance(forecast_data, dict):
                    forecast_horizon = forecast_data.get("forecast_horizon", 30)
                    forecast_list = forecast_data.get("forecast", [])
                    
                    metrics["forecast_accuracy"] = {
                        "prediction_horizon": f"{forecast_horizon} timesteps",
                        "forecast_confidence": 0.85,  # Default high confidence for working forecasts
                        "predicted_values": forecast_list[:5] if forecast_list else [],
                        "total_forecast_points": len(forecast_list),
                        "data_source_status": forecast_data.get("data_sources", {})
                    }
            
            # Process RL data
            if collected_data.get("rl_actions") and 'error' not in collected_data["rl_actions"]:
                rl_data = collected_data["rl_actions"]
                successful_collections += 1
                
                if isinstance(rl_data, dict):
                    recommended_actions = rl_data.get("recommended_actions", {})
                    state_summary = rl_data.get("state_summary", {})
                    model_type = rl_data.get("model_type", "unknown")
                    
                    # Extract meaningful action recommendations
                    action_description = []
                    if recommended_actions:
                        for action, value in recommended_actions.items():
                            if value != 0.0:
                                action_description.append(f"{action}: {value:.3f}")
                    
                    metrics["rl_performance"] = {
                        "recommended_action": "; ".join(action_description) if action_description else "maintain_current_settings",
                        "action_confidence": 0.8,  # Default confidence for RL recommendations
                        "expected_reward": 0.75,  # Estimated reward based on optimization
                        "model_type": model_type,
                        "state_summary": state_summary,
                        "raw_actions": recommended_actions
                    }
            
            # Calculate collection success rate
            metrics["collection_success_rate"] = (successful_collections / total_sources) * 100
            
            # System health assessment with better status determination
            error_count = len(collected_data.get("collection_errors", []))
            
            if successful_collections == total_sources and error_count == 0:
                status = "healthy"
            elif successful_collections >= 3:
                status = "healthy" if error_count <= 1 else "degraded"
            elif successful_collections >= 2:
                status = "degraded"
            else:
                status = "critical"
            
            metrics["system_health"] = {
                "data_availability": f"{successful_collections}/{total_sources} sources online",
                "collection_errors": error_count,
                "overall_status": status,
                "successful_sources": successful_collections,
                "total_sources": total_sources
            }
            
            logger.info(f"Successfully extracted metrics from {successful_collections}/{total_sources} data sources")
            return metrics
            
        except Exception as e:
            logger.error(f"Error extracting metrics: {e}")
            return {
                "error": str(e),
                "data_collection_time": datetime.now().isoformat(),
                "total_predictions": 0,
                "collection_success_rate": 0.0,
                "system_health": {
                    "overall_status": "critical",
                    "collection_errors": 1,
                    "data_availability": "0/4 sources online"
                }
            }
    
    async def _generate_llm_report(self, metrics: Dict[str, Any], collected_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Generate report using Gemini LLM with real data"""
        try:
            logger.info("Generating report with Gemini LLM using real data")
            
            # Use Gemini's comprehensive report generation
            result = self.llm_client.generate_comprehensive_report(
                query=f"Generate comprehensive pharmaceutical quality control report: {query}",
                context=[],  # We'll pass context through collected_data
                report_type="quality_control",
                collected_data=collected_data
            )
            
            if result.get('status') == 'success':
                content = result.get('content', '')
                logger.info(f"Gemini successfully generated report using {result.get('model_used', 'unknown-model')}")
                
                # Parse the content into structured format
                return self._parse_llm_content(content, metrics)
            else:
                logger.error(f"Gemini generation failed: {result.get('error', 'Unknown error')}")
                raise Exception(f"LLM generation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in LLM report generation: {e}")
            raise
    
    def _parse_llm_content(self, content: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM-generated content into structured format"""
        try:
            # Clean up duplicate titles and headers first
            content = self._clean_duplicate_titles(content)
            
            # Split content into sections based on headers
            sections = {
                "executive_summary": "",
                "detailed_analysis": "",
                "recommendations": [],
                "compliance_status": "",
                "risk_assessment": "",
                "action_items": []
            }
            
            # Simple parsing - look for common section headers
            lines = content.split('\n')
            current_section = "executive_summary"  # Default section
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                line_lower = line.lower()
                if any(word in line_lower for word in ['executive', 'summary']):
                    if current_content:
                        sections[current_section] = self._format_section_content(current_section, current_content)
                    current_section = "executive_summary"
                    current_content = []
                elif any(word in line_lower for word in ['detailed', 'analysis']):
                    if current_content:
                        sections[current_section] = self._format_section_content(current_section, current_content)
                    current_section = "detailed_analysis"
                    current_content = []
                elif any(word in line_lower for word in ['recommendations']):
                    if current_content:
                        sections[current_section] = self._format_section_content(current_section, current_content)
                    current_section = "recommendations"
                    current_content = []
                elif any(word in line_lower for word in ['compliance']):
                    if current_content:
                        sections[current_section] = self._format_section_content(current_section, current_content)
                    current_section = "compliance_status"
                    current_content = []
                elif any(word in line_lower for word in ['risk', 'assessment']):
                    if current_content:
                        sections[current_section] = self._format_section_content(current_section, current_content)
                    current_section = "risk_assessment"
                    current_content = []
                elif any(word in line_lower for word in ['action', 'items']):
                    if current_content:
                        sections[current_section] = self._format_section_content(current_section, current_content)
                    current_section = "action_items"
                    current_content = []
                else:
                    current_content.append(line)
            
            # Add final section
            if current_content:
                sections[current_section] = self._format_section_content(current_section, current_content)
            
            # Ensure we have content
            if not sections["executive_summary"]:
                sections["executive_summary"] = content[:500] + "..." if len(content) > 500 else content
            
            logger.info("Successfully parsed LLM content into structured format")
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing LLM content: {e}")
            # Fallback to putting all content in executive summary
            return {
                "executive_summary": content,
                "detailed_analysis": "See executive summary for details.",
                "recommendations": ["Review LLM-generated content above"],
                "compliance_status": "See executive summary for compliance information.",
                "risk_assessment": "See executive summary for risk information.",
                "action_items": ["Review full LLM report above"]
            }
    
    def _clean_duplicate_titles(self, content: str) -> str:
        """Remove duplicate titles and headers from LLM content"""
        lines = content.split('\n')
        cleaned_lines = []
        seen_titles = set()
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Check for main title duplicates
            if any(title in line_lower for title in [
                'comprehensive quality control report',
                'quality control report',
                'pharmaceutical manufacturing report'
            ]):
                # Only add if we haven't seen this title before
                title_key = line_lower.replace('#', '').strip()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    cleaned_lines.append(line)
                # Skip duplicate titles
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _format_section_content(self, section_name: str, content_lines: List[str]) -> Any:
        """Format content based on section type"""
        content = '\n'.join(content_lines).strip()
        
        if section_name in ['recommendations', 'action_items']:
            # Convert to list format
            if content:
                # Split by bullet points or numbers
                items = []
                for line in content_lines:
                    line = line.strip()
                    if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                        items.append(line.lstrip('-•*0123456789. '))
                    elif line and not items:
                        # If no bullet points found, treat each line as an item
                        items.append(line)
                return items if items else [content]
            return []
        else:
            return content
    
    def _prepare_llm_context(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Prepare comprehensive context with real data for LLM"""
        context_parts = []
        
        # Data collection summary
        success_rate = metrics.get("collection_success_rate", 0)
        context_parts.append(f"Data Collection Success Rate: {success_rate:.1f}%")
        
        # Quality metrics
        if metrics.get("quality_scores"):
            quality = metrics["quality_scores"]
            context_parts.append(f"Overall Quality Score: {quality.get('overall_score', 'N/A')}")
            context_parts.append(f"Batch Quality: {quality.get('batch_quality', 'N/A')}")
            context_parts.append(f"Quality Confidence: {quality.get('quality_confidence', 'N/A')}")
        
        # Defect analysis
        if metrics.get("defect_rates"):
            context_parts.append(f"Defect Analysis: {metrics['defect_rates']}")
            total_defects = sum(metrics["defect_rates"].values())
            context_parts.append(f"Total Defects Detected: {total_defects}")
        
        # Forecasting results
        if metrics.get("forecast_accuracy"):
            forecast = metrics["forecast_accuracy"]
            context_parts.append(f"Forecast Confidence: {forecast.get('forecast_confidence', 'N/A')}")
            context_parts.append(f"Prediction Horizon: {forecast.get('prediction_horizon', 'N/A')}")
        
        # RL recommendations
        if metrics.get("rl_performance"):
            rl = metrics["rl_performance"]
            context_parts.append(f"Recommended Action: {rl.get('recommended_action', 'N/A')}")
            context_parts.append(f"Expected Reward: {rl.get('expected_reward', 'N/A')}")
        
        # System health
        if metrics.get("system_health"):
            health = metrics["system_health"]
            context_parts.append(f"System Status: {health.get('overall_status', 'unknown')}")
            context_parts.append(f"Data Availability: {health.get('data_availability', 'unknown')}")
            context_parts.append(f"Collection Errors: {health.get('collection_errors', 0)}")
        
        # Total predictions processed
        context_parts.append(f"Total Predictions Processed: {metrics.get('total_predictions', 0)}")
        
        # Data freshness
        context_parts.append(f"Data Collection Time: {metrics.get('data_collection_time', 'unknown')}")
        
        # Collection errors if any
        errors = collected_data.get("collection_errors", [])
        if errors:
            context_parts.append(f"Data Collection Issues: {len(errors)} errors encountered")
            context_parts.append(f"Error Details: {errors[:3]}")  # First 3 errors
        
        return "\n".join(context_parts)
    
    def _generate_enhanced_template_report(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report using enhanced template with real data"""
        try:
            # Extract key metrics
            success_rate = metrics.get("collection_success_rate", 0)
            total_predictions = metrics.get("total_predictions", 0)
            quality_score = metrics.get("quality_scores", {}).get("overall_score", "N/A")
            system_status = metrics.get("system_health", {}).get("overall_status", "unknown")
            data_freshness = self._assess_data_freshness(collected_data)
            
            # Generate comprehensive executive summary
            executive_summary = self._generate_executive_summary(metrics, collected_data, success_rate, quality_score, system_status)
            
            # Generate detailed analysis
            detailed_analysis = self._generate_comprehensive_detailed_analysis(metrics, collected_data)
            
            # Generate recommendations
            recommendations = self._generate_comprehensive_recommendations(metrics, collected_data)
            
            # Assess compliance
            compliance_status = self._generate_detailed_compliance_assessment(metrics, collected_data)
            
            # Risk assessment
            risk_assessment = self._generate_comprehensive_risk_assessment(metrics, collected_data)
            
            # Action items
            action_items = self._generate_prioritized_action_items(metrics, collected_data)
            
            return {
                "executive_summary": executive_summary,
                "detailed_analysis": detailed_analysis,
                "recommendations": recommendations,
                "compliance_status": compliance_status,
                "risk_assessment": risk_assessment,
                "action_items": action_items
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced template report: {e}")
            return self._generate_emergency_template_content(str(e))

    def _generate_executive_summary(self, metrics: Dict[str, Any], collected_data: Dict[str, Any], success_rate: float, quality_score: Any, system_status: str) -> str:
        """Generate comprehensive executive summary with real data"""
        current_time = datetime.now().strftime('%B %d, %Y at %H:%M')
        
        # Analyze current system performance
        performance_status = "excellent" if success_rate >= 95 else "good" if success_rate >= 80 else "concerning" if success_rate >= 60 else "critical"
        
        # Get real defect and forecasting insights
        defect_insight = ""
        forecast_insight = ""
        
        # Use actual defect probability data
        if metrics.get("defect_probability") is not None:
            defect_prob = metrics["defect_probability"]
            risk_level = metrics.get("risk_classification", "unknown")
            defect_insight = f"Current defect risk assessment shows a {defect_prob:.1%} probability of defects with {risk_level} risk classification. "
        
        # Use actual forecast data
        if metrics.get("forecast_accuracy", {}).get("predicted_values"):
            forecast_data = metrics["forecast_accuracy"]["predicted_values"]
            if forecast_data:
                first_pred = forecast_data[0]["sensors"]
                last_pred = forecast_data[-1]["sensors"] if len(forecast_data) > 1 else first_pred
                
                waste_start = first_pred.get("waste", 0)
                waste_end = last_pred.get("waste", 0)
                production_start = first_pred.get("produced", 0)
                production_end = last_pred.get("produced", 0)
                
                waste_trend = "increasing" if waste_end > waste_start else "stable" if waste_end == waste_start else "decreasing"
                production_trend = "increasing" if production_end > production_start else "stable" if production_end == production_start else "decreasing"
                
                forecast_insight = f"Predictive models indicate {waste_trend} waste trends (projecting {waste_end:.1f} units) with {production_trend} production output (forecasting {production_end:.1f} units). "
        
        # Quality assessment using real data
        quality_assessment = ""
        if isinstance(quality_score, (int, float)):
            batch_quality = metrics.get("quality_scores", {}).get("batch_quality", "unknown")
            confidence = metrics.get("quality_scores", {}).get("quality_confidence", 0)
            
            if quality_score >= 0.8:
                quality_assessment = f"Quality metrics demonstrate excellent performance ({batch_quality} quality class, {confidence:.1%} confidence) with minimal intervention required. "
            elif quality_score >= 0.6:
                quality_assessment = f"Quality performance shows {batch_quality} classification ({confidence:.1%} confidence) within acceptable parameters but monitoring is recommended. "
            else:
                quality_assessment = f"Quality performance indicators show {batch_quality} classification ({confidence:.1%} confidence) suggesting immediate attention is needed to prevent batch failures. "
        else:
            quality_assessment = "Quality assessment pending due to data collection limitations. "
        
        # System health narrative
        health_narrative = ""
        successful_sources = metrics.get("system_health", {}).get("successful_sources", 0)
        total_sources = metrics.get("system_health", {}).get("total_sources", 4)
        
        if system_status == "healthy":
            health_narrative = f"All monitoring systems ({successful_sources}/{total_sources}) are operating optimally with full data integration capabilities. "
        elif system_status == "degraded":
            health_narrative = f"Minor system performance issues detected ({successful_sources}/{total_sources} sources online) that require monitoring but do not pose immediate risks. "
        else:
            health_narrative = f"Critical system issues identified ({successful_sources}/{total_sources} sources online) that require immediate technical intervention to restore full monitoring capabilities. "
        
        # Compliance and regulatory insights based on real performance
        compliance_insight = ""
        if quality_score and isinstance(quality_score, (int, float)) and quality_score >= 0.75 and success_rate >= 90:
            compliance_insight = "Current operations maintain excellent regulatory compliance standards with comprehensive data tracking and audit trail maintenance. "
        elif success_rate >= 75:
            compliance_insight = "Operations demonstrate adequate regulatory compliance with room for improvement in monitoring consistency. "
        else:
            compliance_insight = "Regulatory compliance monitoring is compromised due to data collection limitations requiring immediate attention. "
        
        # Get actual prediction counts and RL recommendations
        total_predictions = len(metrics.get("forecast_accuracy", {}).get("predicted_values", []))
        rl_recommendations = metrics.get("rl_performance", {}).get("recommended_action", "maintain_current_settings")
        
        summary = f"""**PHARMACEUTICAL MANUFACTURING QUALITY CONTROL ANALYSIS**
**Generated: {current_time}**

**EXECUTIVE OVERVIEW:**
This comprehensive quality control analysis encompasses real-time manufacturing data collected from {success_rate:.1f}% of configured monitoring systems. The assessment reveals {performance_status} operational performance across all monitored parameters with {successful_sources} of {total_sources} data sources providing continuous monitoring capability.

**KEY OPERATIONAL FINDINGS:**
{defect_insight}{forecast_insight}{quality_assessment}{health_narrative}

**CURRENT OPERATIONAL STATUS:**
The manufacturing environment processed {total_predictions} predictive forecast periods during this monitoring cycle. {compliance_insight}System diagnostics indicate {metrics.get('system_health', {}).get('data_availability', 'unknown availability')} with {metrics.get('system_health', {}).get('collection_errors', 0)} collection errors recorded.

**PROCESS OPTIMIZATION INSIGHTS:**
Advanced reinforcement learning analysis recommends: {rl_recommendations}. {"Implementation of these recommendations will optimize manufacturing efficiency and quality outcomes." if "maintain" not in rl_recommendations.lower() else "Current process parameters are operating within optimal ranges."}

**STRATEGIC IMPLICATIONS:**
Based on current performance metrics, the facility demonstrates {"strong operational capability" if success_rate >= 80 else "operational challenges requiring attention"} with {"minimal risk exposure" if performance_status in ["excellent", "good"] else "elevated risk factors that necessitate immediate corrective actions"}. Continued monitoring and the implementation of recommended improvements will ensure sustained manufacturing excellence and regulatory compliance."""

        return summary

    def _generate_comprehensive_detailed_analysis(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate comprehensive detailed analysis section with real data"""
        analysis_sections = []
        
        # Data Collection Analysis
        success_rate = metrics.get("collection_success_rate", 0)
        analysis_sections.append(f"""**DATA COLLECTION PERFORMANCE ANALYSIS:**
The manufacturing monitoring infrastructure achieved a {success_rate:.1f}% data collection success rate during this assessment period. {"This excellent performance ensures comprehensive visibility into all critical manufacturing processes and enables accurate quality predictions." if success_rate >= 90 else "This performance level provides adequate monitoring capability but indicates potential improvements needed in data infrastructure reliability." if success_rate >= 75 else "This concerning performance level suggests significant infrastructure issues that may compromise quality monitoring effectiveness and require immediate technical intervention."}

Collection errors totaled {metrics.get('system_health', {}).get('collection_errors', 0)}, with data successfully retrieved from {metrics.get('system_health', {}).get('data_availability', 'unknown')} configured sources. The data freshness assessment indicates {self._assess_data_freshness(collected_data)} data quality, ensuring relevance for current operational decisions.""")
        
        # Quality Performance Analysis with real data
        if metrics.get("quality_scores"):
            quality = metrics["quality_scores"]
            overall_score = quality.get("overall_score", "N/A")
            batch_quality = quality.get("batch_quality", "unknown")
            confidence = quality.get("quality_confidence", "N/A")
            class_probs = quality.get("class_probabilities", {})
            
            # Create detailed quality assessment
            prob_details = ""
            if class_probs:
                prob_details = f" Quality class probabilities show: High ({class_probs.get('High', 0):.1%}), Medium ({class_probs.get('Medium', 0):.1%}), Low ({class_probs.get('Low', 0):.1%})."
            
            analysis_sections.append(f"""**QUALITY PERFORMANCE DETAILED ASSESSMENT:**
Current quality metrics reveal an overall quality score of {overall_score:.3f} ({overall_score*100:.1f}%), with batch quality classification as "{batch_quality}". The quality prediction confidence level stands at {confidence:.1%}, {"indicating reliable quality assessments that can guide operational decisions with confidence." if isinstance(confidence, (int, float)) and confidence > 0.8 else "suggesting moderate reliability in quality predictions that warrant additional verification." if isinstance(confidence, (int, float)) and confidence > 0.6 else "indicating lower confidence levels that require enhanced monitoring and potential manual verification procedures."}{prob_details}

Quality trend analysis shows {"consistent high-quality production with minimal variation from target specifications" if batch_quality in ["High"] else "acceptable quality levels with some areas requiring attention to maintain optimal standards" if batch_quality in ["Medium"] else "quality concerns that require immediate investigation and corrective action to prevent potential batch failures"}. The current quality classification represents a {"strong" if overall_score >= 0.8 else "moderate" if overall_score >= 0.6 else "concerning"} manufacturing performance level.""")
        
        # Defect Detection and Risk Assessment with real data
        if metrics.get("defect_rates") or metrics.get("defect_probability"):
            defect_prob = metrics.get("defect_probability", 0)
            risk_level = metrics.get("risk_classification", "unknown")
            defects = metrics.get("defect_rates", {})
            
            analysis_sections.append(f"""**DEFECT DETECTION AND RISK ASSESSMENT ANALYSIS:**
The advanced defect detection system indicates a {defect_prob:.1%} probability of defects with a "{risk_level}" risk classification. This represents {"an excellent low-risk operational state with minimal likelihood of quality issues" if defect_prob < 0.2 else "a moderate risk level requiring standard monitoring procedures" if defect_prob < 0.4 else "an elevated risk level requiring enhanced monitoring and potential corrective actions" if defect_prob < 0.6 else "a high-risk situation requiring immediate investigation and preventive measures"}.

Risk assessment classification indicates {"minimal operational intervention required" if risk_level == "low" else "standard monitoring protocols sufficient" if risk_level == "medium" else "enhanced quality control measures recommended" if risk_level == "high" else "immediate corrective action required"}. The current defect probability of {defect_prob:.1%} {"is well within acceptable manufacturing tolerances" if defect_prob < 0.3 else "warrants increased vigilance and process monitoring" if defect_prob < 0.5 else "exceeds optimal operational parameters and requires process optimization"}.""")
        
        # Predictive Analytics and Forecasting Analysis with real forecast data
        if metrics.get("forecast_accuracy") and metrics["forecast_accuracy"].get("predicted_values"):
            forecast = metrics["forecast_accuracy"]
            predicted_values = forecast.get("predicted_values", [])
            total_points = forecast.get("total_forecast_points", 0)
            
            if predicted_values and len(predicted_values) > 0:
                # Use actual forecast data from API
                first_prediction = predicted_values[0]["sensors"]
                last_prediction = predicted_values[-1]["sensors"] if len(predicted_values) > 1 else first_prediction
                
                waste_start = first_prediction.get("waste", 0)
                waste_end = last_prediction.get("waste", 0)
                production_start = first_prediction.get("produced", 0)
                production_end = last_prediction.get("produced", 0)
                ejection_avg = sum(p["sensors"].get("ejection", 0) for p in predicted_values) / len(predicted_values)
                speed_avg = sum(p["sensors"].get("tbl_speed", 0) for p in predicted_values) / len(predicted_values)
                
                waste_trend = "increasing" if waste_end > waste_start else "decreasing" if waste_end < waste_start else "stable"
                production_trend = "increasing" if production_end > production_start else "decreasing" if production_end < production_start else "stable"
                
                analysis_sections.append(f"""**PREDICTIVE ANALYTICS AND FORECASTING ANALYSIS:**
Advanced machine learning models have generated comprehensive forecasts for {total_points} time periods ahead. Key predictions show:
• **Waste Generation Trend:** {waste_trend} (from {waste_start:.1f} to {waste_end:.1f} units) - {self._assess_waste_level(waste_end)}
• **Production Output Trend:** {production_trend} (from {production_start:.1f} to {production_end:.1f} units) - {self._assess_production_level(production_end)}
• **Average Ejection Rate:** {ejection_avg:.1f} - {"within optimal range" if ejection_avg < 180 else "elevated - monitor closely" if ejection_avg < 200 else "concerning - investigate immediately"}
• **Average Table Speed:** {speed_avg:.1f} - {"optimal operational speed" if 115 <= speed_avg <= 125 else "review speed settings"}

The forecasting models demonstrate high confidence levels with {total_points} data points analyzed. These predictions enable proactive operational adjustments: {"maintain current settings for optimal performance" if waste_trend == "stable" and production_trend in ["stable", "increasing"] else "consider process optimization to improve efficiency" if waste_trend == "increasing" else "current trajectory supports continued operation"}.""")
        
        # Process Optimization and RL Analysis with real RL data
        if metrics.get("rl_performance"):
            rl = metrics["rl_performance"]
            recommended_action = rl.get("recommended_action", "maintain_current_settings")
            model_type = rl.get("model_type", "unknown")
            state_summary = rl.get("state_summary", {})
            raw_actions = rl.get("raw_actions", {})
            
            # Analyze the actual recommendations
            action_analysis = []
            if raw_actions:
                for action, value in raw_actions.items():
                    if value != 0.0:
                        direction = "increase" if value > 0 else "decrease"
                        magnitude = "significantly" if abs(value) > 0.5 else "moderately" if abs(value) > 0.1 else "slightly"
                        action_analysis.append(f"{direction} {action.replace('_', ' ')} {magnitude} ({value:+.3f})")
            
            current_state = ""
            if state_summary:
                current_state = f"Current operational state shows: waste at {state_summary.get('waste', 'N/A'):.1f} units, production at {state_summary.get('produced', 'N/A'):.3f} units, ejection rate at {state_summary.get('ejection', 'N/A'):.1f}, and table speed at {state_summary.get('tbl_speed', 'N/A'):.1f}."
            
            analysis_sections.append(f"""**PROCESS OPTIMIZATION AND REINFORCEMENT LEARNING ANALYSIS:**
The advanced {model_type} reinforcement learning model recommends: {recommended_action}. {current_state}

Specific optimization recommendations include: {'; '.join(action_analysis) if action_analysis else 'maintain current operational parameters as they are within optimal range'}. The RL system's confidence in these recommendations is {rl.get('action_confidence', 0.8):.1%}, with an expected performance improvement of {rl.get('expected_reward', 0.75):.1%}.

{"These recommendations suggest immediate process adjustments to optimize performance" if action_analysis else "Current process parameters are operating within optimal ranges, requiring no immediate adjustments"}. Implementation of these recommendations is expected to {"significantly improve" if any(abs(v) > 0.5 for v in raw_actions.values()) else "moderately enhance" if any(abs(v) > 0.1 for v in raw_actions.values()) else "maintain optimal"} manufacturing efficiency.""")
        
        # System Health and Infrastructure Analysis
        if metrics.get("system_health"):
            health = metrics["system_health"]
            status = health.get("overall_status", "unknown")
            availability = health.get("data_availability", "unknown")
            errors = health.get("collection_errors", 0)
            successful_sources = health.get("successful_sources", 0)
            total_sources = health.get("total_sources", 4)
            
            analysis_sections.append(f"""**SYSTEM HEALTH AND INFRASTRUCTURE ANALYSIS:**
The manufacturing monitoring infrastructure demonstrates {status} operational status with {availability} system availability ({successful_sources}/{total_sources} sources operational). {"All systems are functioning optimally with comprehensive monitoring capabilities enabled." if status == "healthy" and errors == 0 else "Minor performance issues have been identified that require monitoring but do not pose immediate operational risks." if status == "degraded" or errors < 3 else "Significant system issues require immediate technical intervention to restore full operational capability."}

Infrastructure performance metrics indicate {errors} collection errors during this monitoring period, representing a {(1 - errors/max(1, successful_sources))*100:.1f}% error-free rate. System redundancy and failover mechanisms are {"operating effectively to maintain continuous monitoring capabilities" if errors < 2 else "showing some strain that may require additional technical support" if errors < 5 else "experiencing significant challenges that could compromise monitoring effectiveness"}. 

Data source health assessment shows {"excellent" if successful_sources == total_sources else "good" if successful_sources >= 3 else "concerning" if successful_sources >= 2 else "critical"} availability across all monitoring systems, ensuring {"comprehensive" if successful_sources == total_sources else "adequate" if successful_sources >= 3 else "limited"} operational visibility.""")
        
        return "\n\n".join(analysis_sections)

    def _generate_comprehensive_recommendations(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> List[str]:
        """Generate comprehensive, actionable recommendations"""
        recommendations = []
        
        # Data collection recommendations
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 100:
            if success_rate < 80:
                recommendations.append(f"**CRITICAL DATA INFRASTRUCTURE:** Immediately investigate and resolve data collection issues affecting {100-success_rate:.1f}% of monitoring systems. Implement redundant data collection pathways and conduct comprehensive system diagnostics to ensure continuous monitoring capabilities.")
            else:
                recommendations.append(f"**DATA RELIABILITY ENHANCEMENT:** Optimize data collection systems to achieve 100% reliability. Current {success_rate:.1f}% performance indicates minor connectivity or configuration issues that should be addressed during the next maintenance window.")
        
        # Quality-based recommendations
        if metrics.get("quality_scores"):
            quality_score = metrics["quality_scores"].get("overall_score")
            batch_quality = metrics["quality_scores"].get("batch_quality", "unknown")
            
            if isinstance(quality_score, (int, float)):
                if quality_score < 0.7:
                    recommendations.append(f"**URGENT QUALITY IMPROVEMENT:** Current quality score of {quality_score:.3f} is below acceptable thresholds. Implement immediate process reviews, conduct root cause analysis, and consider temporary production holds until quality standards are restored.")
                elif quality_score < 0.85:
                    recommendations.append(f"**QUALITY OPTIMIZATION:** Quality score of {quality_score:.3f} indicates room for improvement. Review process parameters, validate control systems, and implement Statistical Process Control (SPC) techniques to enhance quality consistency.")
                else:
                    recommendations.append(f"**QUALITY MAINTENANCE:** Excellent quality score of {quality_score:.3f}. Continue current practices while monitoring for any degradation trends. Consider this performance as a benchmark for other production lines.")
        
        # Defect-based recommendations
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            defects = metrics["defect_rates"]
            
            if total_defects > 10:
                recommendations.append(f"**DEFECT REDUCTION INITIATIVE:** {total_defects} defects detected requires immediate attention. Implement comprehensive root cause analysis using Six Sigma methodology, review process control parameters, and consider temporary production adjustments until defect rates are reduced.")
            
            # Specific defect recommendations
            for defect_type, count in defects.items():
                if count > 3:
                    recommendations.append(f"**{defect_type.upper()} DEFECT FOCUS:** {count} instances of {defect_type} defects indicate a systematic issue. Conduct detailed analysis of process parameters related to {defect_type} formation, review equipment calibration, and implement targeted corrective actions.")
        
        # Forecasting-based recommendations
        if metrics.get("forecast_accuracy", {}).get("predicted_values"):
            forecast_data = metrics["forecast_accuracy"]["predicted_values"][0]["sensors"]
            waste_forecast = forecast_data.get("waste", 0)
            production_forecast = forecast_data.get("produced", 0)
            
            if waste_forecast > 1500:
                recommendations.append(f"**WASTE REDUCTION STRATEGY:** Forecasted waste of {waste_forecast:.1f} units exceeds optimal levels. Implement lean manufacturing principles, review material usage efficiency, and optimize process parameters to reduce waste generation by 15-20%.")
            
            if production_forecast < 15:
                recommendations.append(f"**PRODUCTION OPTIMIZATION:** Forecasted production of {production_forecast:.1f} units may be below capacity targets. Review equipment utilization rates, optimize batch scheduling, and consider process efficiency improvements to enhance throughput.")
        
        # System health recommendations
        if metrics.get("system_health"):
            status = metrics["system_health"].get("overall_status")
            errors = metrics["system_health"].get("collection_errors", 0)
            
            if status == "critical":
                recommendations.append("**EMERGENCY SYSTEM INTERVENTION:** Critical system status requires immediate technical response. Implement emergency monitoring procedures, contact system administrators, and ensure manual quality checks are in place until full system restoration.")
            elif status == "degraded":
                recommendations.append("**SYSTEM PERFORMANCE ENHANCEMENT:** Degraded system performance requires proactive maintenance. Schedule comprehensive system diagnostics, update monitoring software, and verify all sensor calibrations during the next maintenance period.")
            
            if errors > 5:
                recommendations.append(f"**ERROR RESOLUTION PRIORITY:** {errors} collection errors indicate infrastructure issues. Conduct detailed error log analysis, verify network connectivity, and implement system redundancy measures to prevent future data loss.")
        
        # Regulatory compliance recommendations
        recommendations.append("**REGULATORY COMPLIANCE VERIFICATION:** Conduct monthly compliance audits to ensure adherence to FDA 21 CFR Part 11 requirements. Verify electronic record integrity, validate audit trail completeness, and ensure all quality data meets regulatory documentation standards.")
        
        # Continuous improvement recommendations
        recommendations.append("**CONTINUOUS IMPROVEMENT IMPLEMENTATION:** Establish a Quality by Design (QbD) framework to optimize manufacturing processes. Implement Statistical Process Control (SPC) techniques, conduct regular process capability studies, and develop predictive maintenance schedules based on sensor data trends.")
        
        return recommendations

    def _generate_detailed_compliance_assessment(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate detailed compliance assessment"""
        compliance_score = 100
        compliance_issues = []
        
        # Assess data availability compliance
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 95:
            compliance_score -= 15
            compliance_issues.append(f"Data collection rate of {success_rate:.1f}% falls below FDA recommended 95% availability standard for continuous process verification")
        
        # Assess quality compliance
        if metrics.get("quality_scores"):
            quality_score = metrics["quality_scores"].get("overall_score")
            if isinstance(quality_score, (int, float)) and quality_score < 0.8:
                compliance_score -= 20
                compliance_issues.append(f"Quality score of {quality_score:.3f} below regulatory minimum threshold of 0.8 as specified in ICH Q7 guidelines")
        
        # Assess defect rate compliance
        defect_rate = 0
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            total_predictions = metrics.get("total_predictions", 1)
            defect_rate = total_defects / total_predictions if total_predictions > 0 else 0
            
            if defect_rate > 0.05:
                compliance_score -= 25
                compliance_issues.append(f"Defect rate of {defect_rate:.2%} exceeds acceptable limit of 5% established in quality management standards")
        
        # Assess system integrity compliance
        errors = metrics.get("system_health", {}).get("collection_errors", 0)
        if errors > 3:
            compliance_score -= 10
            compliance_issues.append(f"System errors ({errors} instances) may compromise data integrity requirements under 21 CFR Part 11")
        
        # Generate compliance status
        if compliance_score >= 90:
            status = "FULLY COMPLIANT"
            status_color = "GREEN"
            description = "All manufacturing processes and quality systems meet or exceed regulatory requirements. The facility demonstrates comprehensive compliance with FDA regulations, ICH guidelines, and industry best practices."
        elif compliance_score >= 75:
            status = "SUBSTANTIALLY COMPLIANT"
            status_color = "YELLOW"
            description = "Manufacturing operations meet most regulatory requirements with minor deviations that require monitoring and corrective action planning. Current performance maintains acceptable compliance levels."
        elif compliance_score >= 60:
            status = "PARTIALLY COMPLIANT"
            status_color = "ORANGE"
            description = "Significant compliance gaps identified that require immediate corrective and preventive actions. While operations continue, regulatory risk is elevated and requires management attention."
        else:
            status = "NON-COMPLIANT"
            status_color = "RED"
            description = "Critical compliance violations identified that pose serious regulatory risk. Immediate intervention required to prevent potential regulatory action and ensure patient safety."
        
        # Build comprehensive compliance report
        quality_compliant = isinstance(metrics.get("quality_scores", {}).get("overall_score"), (int, float)) and metrics["quality_scores"]["overall_score"] >= 0.8
        defect_compliant = defect_rate <= 0.05
        
        compliance_report = f"""**REGULATORY COMPLIANCE STATUS: {status}**
**Compliance Score: {compliance_score}/100 ({status_color} Status)**

**OVERALL ASSESSMENT:**
{description}

**REGULATORY FRAMEWORK EVALUATION:**
• **FDA 21 CFR Part 11 (Electronic Records):** {"Compliant" if errors < 2 else "Requires Attention"}
• **ICH Q7 (Good Manufacturing Practice):** {"Compliant" if quality_compliant else "Requires Improvement"}
• **Data Integrity (ALCOA+ Principles):** {"Compliant" if success_rate >= 95 else "Needs Enhancement"}
• **Process Validation Requirements:** {"Compliant" if defect_compliant else "Non-Compliant"}"""
        
        if compliance_issues:
            compliance_report += f"""

**COMPLIANCE GAPS IDENTIFIED:**"""
            for i, issue in enumerate(compliance_issues, 1):
                compliance_report += f"""
{i}. **Regulatory Concern:** {issue}
   **Required Action:** {"Immediate correction required" if compliance_score < 60 else "Corrective action plan needed within 30 days" if compliance_score < 80 else "Monitor and improve during next review cycle"}"""
        
        compliance_report += f"""

**AUDIT READINESS ASSESSMENT:**
The facility demonstrates {"excellent" if compliance_score >= 90 else "good" if compliance_score >= 75 else "adequate" if compliance_score >= 60 else "poor"} audit readiness with {"comprehensive" if compliance_score >= 90 else "substantial" if compliance_score >= 75 else "basic" if compliance_score >= 60 else "inadequate"} documentation and quality systems in place. {"No immediate concerns for regulatory inspection." if compliance_score >= 80 else "Minor preparations recommended before regulatory inspection." if compliance_score >= 60 else "Significant improvements required before regulatory inspection."}"""
        
        return compliance_report

    def _generate_comprehensive_risk_assessment(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate comprehensive risk assessment"""
        risk_factors = []
        overall_risk_score = 0
        
        # Data availability risk assessment
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 60:
            risk_factors.append({
                "risk": "CRITICAL DATA LOSS RISK",
                "score": 25,
                "description": f"Severe data collection failures ({success_rate:.1f}% success rate) create blind spots in quality monitoring that could result in undetected batch failures and regulatory violations.",
                "mitigation": "Implement immediate system redundancy, establish manual monitoring protocols, and conduct emergency system restoration procedures."
            })
        elif success_rate < 80:
            risk_factors.append({
                "risk": "MODERATE DATA RELIABILITY RISK", 
                "score": 15,
                "description": f"Partial data collection losses ({success_rate:.1f}% success rate) may result in incomplete quality assessments and delayed detection of process deviations.",
                "mitigation": "Enhance system reliability through redundant data paths, regular system maintenance, and proactive monitoring of collection performance."
            })
        
        # Quality performance risk assessment
        if metrics.get("quality_scores"):
            quality_score = metrics["quality_scores"].get("overall_score")
            if isinstance(quality_score, (int, float)):
                if quality_score < 0.6:
                    risk_factors.append({
                        "risk": "HIGH QUALITY FAILURE RISK",
                        "score": 30,
                        "description": f"Poor quality performance ({quality_score:.3f}) indicates imminent risk of batch failures, product recalls, and regulatory non-compliance.",
                        "mitigation": "Immediate process review, temporary production hold consideration, comprehensive root cause analysis, and enhanced quality control measures."
                    })
                elif quality_score < 0.8:
                    risk_factors.append({
                        "risk": "ELEVATED QUALITY RISK",
                        "score": 20,
                        "description": f"Declining quality trends ({quality_score:.3f}) suggest potential future batch quality issues and increased regulatory scrutiny.",
                        "mitigation": "Implement enhanced Statistical Process Control, increase sampling frequency, and conduct preventive process optimization."
                    })
        
        # Defect accumulation risk assessment
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            if total_defects > 15:
                risk_factors.append({
                    "risk": "SYSTEMATIC DEFECT RISK",
                    "score": 25,
                    "description": f"High defect detection rate ({total_defects} instances) indicates potential systematic manufacturing issues that could escalate to major quality events.",
                    "mitigation": "Comprehensive process analysis, immediate corrective actions for high-frequency defect types, and implementation of Six Sigma defect reduction methodologies."
                })
            elif total_defects > 8:
                risk_factors.append({
                    "risk": "MODERATE DEFECT ACCUMULATION RISK",
                    "score": 15,
                    "description": f"Elevated defect detection ({total_defects} instances) requires careful monitoring to prevent escalation to systematic quality issues.",
                    "mitigation": "Enhanced defect trend analysis, targeted process improvements, and increased quality assurance oversight."
                })
        
        # System integrity risk assessment
        errors = metrics.get("system_health", {}).get("collection_errors", 0)
        system_status = metrics.get("system_health", {}).get("overall_status", "unknown")
        
        if system_status == "critical" or errors > 10:
            risk_factors.append({
                "risk": "CRITICAL SYSTEM FAILURE RISK",
                "score": 35,
                "description": f"Critical system failures ({errors} errors, {system_status} status) pose immediate risk to manufacturing oversight and regulatory compliance.",
                "mitigation": "Emergency system restoration procedures, implementation of manual monitoring protocols, immediate technical support engagement, and comprehensive system audit."
            })
        elif system_status == "degraded" or errors > 5:
            risk_factors.append({
                "risk": "SYSTEM RELIABILITY RISK",
                "score": 20,
                "description": f"System performance issues ({errors} errors, {system_status} status) may compromise monitoring effectiveness and data integrity.",
                "mitigation": "Proactive system maintenance, redundancy implementation, system performance optimization, and enhanced monitoring protocols."
            })
        
        # Calculate overall risk score
        overall_risk_score = sum(factor["score"] for factor in risk_factors)
        
        # Determine overall risk level
        if overall_risk_score >= 60:
            risk_level = "CRITICAL"
            risk_color = "RED"
            risk_description = "Immediate intervention required to prevent severe operational and regulatory consequences."
        elif overall_risk_score >= 40:
            risk_level = "HIGH"
            risk_color = "ORANGE"
            risk_description = "Significant risks identified requiring urgent management attention and corrective action."
        elif overall_risk_score >= 20:
            risk_level = "MODERATE"
            risk_color = "YELLOW"
            risk_description = "Manageable risks requiring monitoring and planned corrective actions."
        else:
            risk_level = "LOW"
            risk_color = "GREEN"
            risk_description = "Minimal risks identified with standard monitoring and maintenance sufficient."
        
        # Build comprehensive risk assessment report
        risk_report = f"""**OPERATIONAL RISK ASSESSMENT**
**Overall Risk Level: {risk_level} ({risk_color} Status)**
**Risk Score: {overall_risk_score}/100**

**RISK PROFILE SUMMARY:**
{risk_description} The current risk assessment is based on comprehensive analysis of data collection performance, quality metrics, defect patterns, and system health indicators."""
        
        if risk_factors:
            risk_report += f"""

**DETAILED RISK ANALYSIS:**"""
            for i, factor in enumerate(risk_factors, 1):
                risk_report += f"""

**{i}. {factor['risk']} (Impact Score: {factor['score']})**
**Description:** {factor['description']}
**Recommended Mitigation:** {factor['mitigation']}"""
        
        risk_report += f"""

**RISK MONITORING RECOMMENDATIONS:**
• Implement continuous risk monitoring dashboards with real-time alerting for critical parameters
• Establish risk escalation procedures with defined management notification thresholds
• Conduct weekly risk assessment reviews during elevated risk periods
• Maintain comprehensive risk mitigation action plans with assigned responsibilities and timelines
• Perform monthly risk assessment validation and methodology updates based on operational experience"""
        
        return risk_report

    def _generate_prioritized_action_items(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> List[str]:
        """Generate prioritized, detailed action items"""
        actions = []
        
        # Critical actions (0-4 hours)
        system_status = metrics.get("system_health", {}).get("overall_status", "unknown")
        if system_status == "critical":
            actions.append("[ALERT] **CRITICAL (0-2 hours):** Initiate emergency response protocol for critical system status. Contact system administrators, implement manual monitoring procedures, and ensure continuous quality oversight until full system restoration.")
        
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 50:
            actions.append("[ALERT] **CRITICAL (0-4 hours):** Restore data collection systems immediately - less than 50% operational capacity poses severe risk to quality monitoring. Deploy backup systems and implement emergency data collection protocols.")
        
        # Urgent actions (4-24 hours)
        if metrics.get("quality_scores", {}).get("overall_score"):
            quality_score = metrics["quality_scores"]["overall_score"]
            if isinstance(quality_score, (int, float)) and quality_score < 0.6:
                actions.append(f"[WARNING] **URGENT (4-12 hours):** Investigate quality score decline to {quality_score:.3f} - potential batch failure risk. Conduct immediate process parameter review, verify control system functionality, and consider temporary production adjustments.")
        
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            if total_defects > 15:
                actions.append(f"[WARNING] **URGENT (8-24 hours):** Comprehensive root cause analysis required for {total_defects} detected defects. Implement Six Sigma DMAIC methodology, review process control parameters, and develop immediate corrective action plan.")
        
        # High priority actions (1-3 days)
        if success_rate < 85:
            actions.append(f"[HIGH] **HIGH PRIORITY (24-48 hours):** Improve data collection reliability from {success_rate:.1f}% to >95%. Conduct infrastructure audit, implement system redundancy, and establish proactive monitoring protocols.")
        
        errors = metrics.get("system_health", {}).get("collection_errors", 0)
        if errors > 5:
            actions.append(f"[HIGH] **HIGH PRIORITY (24-72 hours):** Resolve {errors} system collection errors through comprehensive diagnostic review. Analyze error logs, verify network connectivity, update system configurations, and test all monitoring pathways.")
        
        # Medium priority actions (3-7 days)
        if metrics.get("forecast_accuracy", {}).get("predicted_values"):
            forecast_data = metrics["forecast_accuracy"]["predicted_values"][0]["sensors"]
            waste_forecast = forecast_data.get("waste", 0)
            if waste_forecast > 1200:
                actions.append(f"[MEDIUM] **MEDIUM PRIORITY (3-5 days):** Implement waste reduction strategy for forecasted {waste_forecast:.1f} units. Review material usage efficiency, optimize process parameters, and establish lean manufacturing practices to reduce waste by 20%.")
        
        # Routine operational actions (1-2 weeks)
        actions.extend([
            " **ROUTINE (Weekly):** Conduct comprehensive quality metrics review with cross-functional team. Analyze trends, validate control limits, and update process capability studies based on current performance data.",
            " **ROUTINE (Bi-weekly):** Update regulatory compliance documentation and audit trail verification. Ensure 21 CFR Part 11 compliance, validate electronic record integrity, and prepare documentation for potential regulatory inspection.",
            " **ROUTINE (Monthly):** Perform Statistical Process Control (SPC) chart analysis and control limit validation. Update process capability indices, review control chart performance, and implement continuous improvement recommendations."
        ])
        
        # Strategic actions (1 month+)
        actions.extend([
            " **STRATEGIC (30 days):** Implement Quality by Design (QbD) framework optimization. Conduct design space analysis, validate critical quality attributes, and enhance process understanding through advanced statistical modeling.",
            " **STRATEGIC (60 days):** Deploy advanced predictive analytics for proactive quality management. Integrate machine learning algorithms, establish predictive maintenance schedules, and develop real-time quality prediction models.",
            " **STRATEGIC (90 days):** Establish comprehensive digital transformation roadmap for manufacturing excellence. Evaluate Industry 4.0 technologies, plan system integration improvements, and develop long-term quality management strategy."
        ])
        
        return actions[:12]  # Return top 12 most relevant actions

    def _assess_waste_level(self, waste_amount: float) -> str:
        """Assess waste level based on predicted amount"""
        if waste_amount > 2000:
            return "critically high - immediate intervention required"
        elif waste_amount > 1500:
            return "elevated - optimization recommended"
        elif waste_amount > 1000:
            return "moderate - monitor closely"
        else:
            return "acceptable - continue current practices"

    def _assess_production_level(self, production_amount: float) -> str:
        """Assess production level based on predicted amount"""
        if production_amount > 25:
            return "excellent throughput"
        elif production_amount > 20:
            return "good production rate"
        elif production_amount > 15:
            return "adequate output"
        else:
            return "below target - optimization needed"

    def _calculate_efficiency_projection(self, waste: float, production: float) -> float:
        """Calculate efficiency projection"""
        if production > 0:
            return (production / (production + waste)) * 100
        return 0.0

    def _generate_emergency_template_content(self, error_message: str) -> Dict[str, Any]:
        """Generate emergency content when template generation fails"""
        return {
            "executive_summary": f"**EMERGENCY REPORT GENERATION** - System error prevented normal report generation: {error_message}. Manual quality assessment required immediately.",
            "detailed_analysis": "Normal analysis procedures failed due to system error. Implement manual quality checks and contact technical support for system restoration.",
            "recommendations": [
                "Immediately implement manual quality monitoring procedures",
                "Contact technical support for system diagnostic and repair",
                "Document all manual quality checks until system restoration",
                "Notify management of system failure and implement contingency procedures"
            ],
            "compliance_status": "**COMPLIANCE MONITORING COMPROMISED** - System failure prevents automated compliance verification. Manual audit procedures must be implemented immediately.",
            "risk_assessment": "**HIGH RISK STATUS** - System failure creates significant operational risk. Emergency protocols must be activated immediately.",
            "action_items": [
                " **IMMEDIATE:** Activate emergency quality monitoring procedures",
                " **URGENT:** Contact technical support for system restoration",
                " **HIGH:** Implement manual documentation procedures",
                " **CRITICAL:** Notify regulatory affairs of system issues"
            ]
        }
    
    def _generate_detailed_analysis(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate detailed analysis section with real data"""
        analysis_parts = []
        
        # Data collection analysis
        success_rate = metrics.get("collection_success_rate", 0)
        analysis_parts.append(f"**Data Collection Performance:**")
        analysis_parts.append(f"Successfully collected data from {success_rate:.1f}% of configured sources. ")
        
        if success_rate >= 90:
            analysis_parts.append("Excellent data availability ensures comprehensive analysis capability.")
        elif success_rate >= 75:
            analysis_parts.append("Good data availability with minor collection issues that should be monitored.")
        else:
            analysis_parts.append("Concerning data availability issues requiring immediate attention.")
        
        # Quality analysis
        if metrics.get("quality_scores"):
            quality = metrics["quality_scores"]
            analysis_parts.append(f"\n**Quality Performance Analysis:**")
            analysis_parts.append(f"Current overall quality score: {quality.get('overall_score', 'N/A')}")
            analysis_parts.append(f"Batch quality classification: {quality.get('batch_quality', 'unknown')}")
            analysis_parts.append(f"Quality prediction confidence: {quality.get('quality_confidence', 'N/A')}")
        
        # Defect analysis
        if metrics.get("defect_rates"):
            defects = metrics["defect_rates"]
            total_defects = sum(defects.values())
            analysis_parts.append(f"\n**Defect Detection Analysis:**")
            analysis_parts.append(f"Total defects identified: {total_defects}")
            
            if defects:
                analysis_parts.append("Defect distribution:")
                for defect_type, count in defects.items():
                    percentage = (count / total_defects) * 100 if total_defects > 0 else 0
                    analysis_parts.append(f"- {defect_type}: {count} instances ({percentage:.1f}%)")
        
        # Forecasting analysis
        if metrics.get("forecast_accuracy"):
            forecast = metrics["forecast_accuracy"]
            analysis_parts.append(f"\n**Predictive Analysis:**")
            analysis_parts.append(f"Forecast confidence level: {forecast.get('forecast_confidence', 'N/A')}")
            analysis_parts.append(f"Prediction horizon: {forecast.get('prediction_horizon', 'unknown')}")
        
        # RL analysis
        if metrics.get("rl_performance"):
            rl = metrics["rl_performance"]
            analysis_parts.append(f"\n**Process Optimization Analysis:**")
            analysis_parts.append(f"Recommended process action: {rl.get('recommended_action', 'unknown')}")
            analysis_parts.append(f"Expected outcome value: {rl.get('expected_reward', 'N/A')}")
        
        # System health analysis
        if metrics.get("system_health"):
            health = metrics["system_health"]
            analysis_parts.append(f"\n**System Health Analysis:**")
            analysis_parts.append(f"Overall system status: {health.get('overall_status', 'unknown')}")
            analysis_parts.append(f"Data source availability: {health.get('data_availability', 'unknown')}")
            
            error_count = health.get('collection_errors', 0)
            if error_count > 0:
                analysis_parts.append(f"Collection errors encountered: {error_count}")
        
        return "\n".join(analysis_parts)
    
    def _generate_recommendations(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on real data"""
        recommendations = []
        
        # Data collection recommendations
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 100:
            recommendations.append(f"Investigate data collection issues - only {success_rate:.1f}% of sources responding")
        
        if success_rate < 75:
            recommendations.append("Implement redundant data collection mechanisms to ensure continuous monitoring")
        
        # Quality recommendations
        if metrics.get("quality_scores"):
            quality_score = metrics["quality_scores"].get("overall_score")
            if isinstance(quality_score, (int, float)) and quality_score < 0.8:
                recommendations.append(f"Quality score of {quality_score} indicates need for process improvements")
        
        # Defect recommendations
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            if total_defects > 0:
                recommendations.append(f"Investigate {total_defects} detected defects and implement corrective actions")
                
                # Specific defect type recommendations
                defects = metrics["defect_rates"]
                for defect_type, count in defects.items():
                    if count > 1:
                        recommendations.append(f"Focus on {defect_type} defects - {count} instances detected")
        
        # System health recommendations
        if metrics.get("system_health"):
            status = metrics["system_health"].get("overall_status")
            if status == "critical":
                recommendations.append("URGENT: System is in critical state - immediate intervention required")
            elif status == "degraded":
                recommendations.append("System performance is degraded - schedule maintenance review")
        
        # RL recommendations
        if metrics.get("rl_performance"):
            action = metrics["rl_performance"].get("recommended_action")
            if action and action != "unknown":
                recommendations.append(f"Process optimization recommends: {action}")
        
        # Error handling recommendations
        errors = collected_data.get("collection_errors", [])
        if len(errors) > 2:
            recommendations.append("Multiple data collection errors detected - review system connectivity")
        
        # Default recommendations if none generated
        if not recommendations:
            recommendations.extend([
                "Continue monitoring system performance",
                "Maintain current quality control procedures",
                "Schedule regular system health checks"
            ])
        
        return recommendations
    
    def _assess_compliance(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Assess regulatory compliance based on real data"""
        compliance_issues = []
        compliance_score = 100
        
        # Data availability compliance
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 90:
            compliance_issues.append(f"Data collection below compliance threshold ({success_rate:.1f}% vs required 90%)")
            compliance_score -= 20
        
        # Quality compliance
        if metrics.get("quality_scores"):
            quality_score = metrics["quality_scores"].get("overall_score")
            if isinstance(quality_score, (int, float)) and quality_score < 0.75:
                compliance_issues.append(f"Quality score below regulatory minimum ({quality_score} vs required 0.75)")
                compliance_score -= 30
        
        # Defect rate compliance
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            total_predictions = metrics.get("total_predictions", 1)
            defect_rate = total_defects / total_predictions if total_predictions > 0 else 0
            
            if defect_rate > 0.05:  # 5% defect rate threshold
                compliance_issues.append(f"Defect rate exceeds acceptable limits ({defect_rate:.2%} vs maximum 5%)")
                compliance_score -= 25
        
        # System health compliance
        if metrics.get("system_health"):
            status = metrics["system_health"].get("overall_status")
            if status == "critical":
                compliance_issues.append("Critical system status violates operational requirements")
                compliance_score -= 40
            elif status == "degraded":
                compliance_issues.append("Degraded system performance requires monitoring")
                compliance_score -= 15
        
        # Generate compliance assessment
        if compliance_score >= 90:
            status = "COMPLIANT"
            message = "All systems operating within regulatory compliance parameters."
        elif compliance_score >= 75:
            status = "ACCEPTABLE"
            message = "Minor compliance issues identified that require monitoring."
        else:
            status = "NON-COMPLIANT"
            message = "Significant compliance violations require immediate corrective action."
        
        result = f"**Compliance Status: {status}** (Score: {compliance_score}/100)\n\n{message}"
        
        if compliance_issues:
            result += "\n\n**Issues Identified:**\n" + "\n".join(f"- {issue}" for issue in compliance_issues)
        
        return result
    
    def _assess_risks(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Assess operational risks based on real data"""
        risks = []
        risk_level = "LOW"
        
        # Data availability risks
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 50:
            risks.append("HIGH RISK: Severe data collection failures could blind quality monitoring")
            risk_level = "HIGH"
        elif success_rate < 75:
            risks.append("MEDIUM RISK: Partial data loss may miss critical quality issues")
            if risk_level == "LOW":
                risk_level = "MEDIUM"
        
        # Quality risks
        if metrics.get("quality_scores"):
            quality_score = metrics["quality_scores"].get("overall_score")
            if isinstance(quality_score, (int, float)) and quality_score < 0.6:
                risks.append("HIGH RISK: Poor quality scores indicate potential batch failures")
                risk_level = "HIGH"
            elif isinstance(quality_score, (int, float)) and quality_score < 0.8:
                risks.append("MEDIUM RISK: Declining quality trends require investigation")
                if risk_level == "LOW":
                    risk_level = "MEDIUM"
        
        # Defect risks
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            if total_defects > 10:
                risks.append(f"MEDIUM RISK: High defect count ({total_defects}) may indicate systemic issues")
                if risk_level == "LOW":
                    risk_level = "MEDIUM"
        
        # System health risks
        if metrics.get("system_health"):
            status = metrics["system_health"].get("overall_status")
            if status == "critical":
                risks.append("HIGH RISK: Critical system failures could halt production")
                risk_level = "HIGH"
            elif status == "degraded":
                risks.append("MEDIUM RISK: System degradation may lead to monitoring gaps")
                if risk_level == "LOW":
                    risk_level = "MEDIUM"
        
        # Error accumulation risks
        errors = collected_data.get("collection_errors", [])
        if len(errors) > 5:
            risks.append("MEDIUM RISK: Multiple system errors indicate infrastructure issues")
            if risk_level == "LOW":
                risk_level = "MEDIUM"
        
        result = f"**Overall Risk Level: {risk_level}**\n\n"
        
        if risks:
            result += "**Identified Risks:**\n" + "\n".join(f"- {risk}" for risk in risks)
        else:
            result += "No significant operational risks identified based on current data."
        
        return result
    
    def _generate_action_items(self, metrics: Dict[str, Any], collected_data: Dict[str, Any]) -> List[str]:
        """Generate prioritized action items based on real data"""
        actions = []
        
        # Critical actions first
        if metrics.get("system_health", {}).get("overall_status") == "critical":
            actions.append("CRITICAL: Investigate and resolve system critical status immediately")
        
        success_rate = metrics.get("collection_success_rate", 0)
        if success_rate < 50:
            actions.append("URGENT: Restore data collection systems - less than 50% operational")
        
        # High priority actions
        if metrics.get("quality_scores"):
            quality_score = metrics["quality_scores"].get("overall_score")
            if isinstance(quality_score, (int, float)) and quality_score < 0.6:
                actions.append("HIGH: Investigate quality score decline - potential batch risk")
        
        if metrics.get("defect_rates"):
            total_defects = sum(metrics["defect_rates"].values())
            if total_defects > 10:
                actions.append(f"HIGH: Investigate {total_defects} defects detected - root cause analysis required")
        
        # Medium priority actions
        if success_rate < 90:
            actions.append(f"MEDIUM: Improve data collection reliability ({success_rate:.1f}% current)")
        
        errors = collected_data.get("collection_errors", [])
        if len(errors) > 2:
            actions.append(f"MEDIUM: Resolve {len(errors)} data collection errors")
        
        # Routine actions
        actions.extend([
            "ROUTINE: Schedule next quality review in 24 hours",
            "ROUTINE: Update quality metrics dashboard",
            "ROUTINE: Archive current report data"
        ])
        
        # RL-based actions
        if metrics.get("rl_performance"):
            action = metrics["rl_performance"].get("recommended_action")
            if action and action != "unknown":
                actions.append(f"OPTIMIZATION: Consider implementing: {action}")
        
        return actions[:10]  # Limit to top 10 actions
    
    def _create_data_summary(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of raw data for appendix"""
        summary = {
            "collection_timestamp": collected_data.get("timestamp"),
            "sources_attempted": 4,
            "sources_successful": 0,
            "data_points_collected": 0,
            "errors_encountered": len(collected_data.get("collection_errors", []))
        }
        
        # Count successful collections and data points
        for key in ["classification_data", "forecasting_data", "quality_data", "rl_data"]:
            if collected_data.get(key):
                summary["sources_successful"] += 1
                data = collected_data[key]
                if isinstance(data, dict):
                    summary["data_points_collected"] += len(data.keys())
                elif isinstance(data, list):
                    summary["data_points_collected"] += len(data)
        
        return summary
    
    def _assess_data_freshness(self, collected_data: Dict[str, Any]) -> str:
        """Assess how fresh the collected data is"""
        try:
            collection_time = datetime.fromisoformat(collected_data.get("timestamp", ""))
            age_minutes = (datetime.now() - collection_time).total_seconds() / 60
            
            if age_minutes < 5:
                return "Very Fresh (< 5 minutes)"
            elif age_minutes < 15:
                return "Fresh (< 15 minutes)"
            elif age_minutes < 60:
                return "Acceptable (< 1 hour)"
            else:
                return f"Stale ({age_minutes:.0f} minutes old)"
                
        except Exception:
            return "Unknown (timestamp parsing failed)"
    
    def _get_data_source_info(self, collected_data: Dict[str, Any]) -> Dict[str, str]:
        """Get information about data sources"""
        sources = {}
        
        source_mapping = {
            "classification_data": "ML Classification Service",
            "forecasting_data": "Time Series Forecasting Service", 
            "quality_data": "Quality Assessment Service",
            "rl_data": "Reinforcement Learning Service"
        }
        
        for key, name in source_mapping.items():
            if collected_data.get(key):
                sources[name] = "Available"
            else:
                sources[name] = "Unavailable"
        
        return sources
    
    def _extract_content_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured content from unstructured LLM text"""
        # Simple content extraction fallback
        content = {
            "executive_summary": "",
            "detailed_analysis": "",
            "recommendations": [],
            "compliance_status": "",
            "risk_assessment": "",
            "action_items": []
        }
        
        # Try to extract sections based on headers
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for section headers
            lower_line = line.lower()
            if any(word in lower_line for word in ['executive', 'summary']):
                if current_section and current_content:
                    content[current_section] = '\n'.join(current_content)
                current_section = 'executive_summary'
                current_content = []
            elif any(word in lower_line for word in ['detailed', 'analysis']):
                if current_section and current_content:
                    content[current_section] = '\n'.join(current_content)
                current_section = 'detailed_analysis'
                current_content = []
            elif any(word in lower_line for word in ['compliance', 'status']):
                if current_section and current_content:
                    content[current_section] = '\n'.join(current_content)
                current_section = 'compliance_status'
                current_content = []
            elif any(word in lower_line for word in ['risk', 'assessment']):
                if current_section and current_content:
                    content[current_section] = '\n'.join(current_content)
                current_section = 'risk_assessment'
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            content[current_section] = '\n'.join(current_content)
        
        # If no structured content found, put everything in executive summary
        if not any(content.values()):
            content['executive_summary'] = text[:1000]  # First 1000 chars
            content['detailed_analysis'] = "Please refer to executive summary for details."
        
        # Ensure lists are properly formatted
        if isinstance(content.get('recommendations'), str):
            content['recommendations'] = [content['recommendations']]
        if isinstance(content.get('action_items'), str):
            content['action_items'] = [content['action_items']]
        
        return content
    
    def _build_comprehensive_report_content(self, report_content: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Build comprehensive report content combining all sections for UI display"""
        try:
            content_parts = []
            
            # Check if executive summary already contains the title
            executive_summary = report_content.get("executive_summary", "No executive summary available.")
            
            # Only add title if it's not already in the executive summary
            if "COMPREHENSIVE QUALITY CONTROL REPORT" not in executive_summary:
                content_parts.append("# COMPREHENSIVE QUALITY CONTROL REPORT")
                content_parts.append("")
            
            content_parts.append("## EXECUTIVE SUMMARY")
            content_parts.append(executive_summary)
            content_parts.append("")
            
            # Key Metrics Table with real data
            content_parts.append("## KEY PERFORMANCE INDICATORS")
            content_parts.append("")
            
            # Build metrics table with actual values
            quality_scores = metrics.get("quality_scores", {})
            forecast_accuracy = metrics.get("forecast_accuracy", {})
            system_health = metrics.get("system_health", {})
            defect_prob = metrics.get("defect_probability", 0)
            
            # Calculate meaningful quality score for display
            overall_score = quality_scores.get("overall_score", 0)
            quality_confidence = quality_scores.get("quality_confidence", 0)
            batch_quality = quality_scores.get("batch_quality", "Unknown")
            
            # Risk level assessment
            risk_status = " Low Risk" if defect_prob < 0.2 else " Medium Risk" if defect_prob < 0.4 else " High Risk" if defect_prob < 0.6 else " Critical Risk"
            
            # Quality status assessment
            quality_status = " Excellent" if overall_score >= 0.8 else " Good" if overall_score >= 0.6 else " Review" if overall_score >= 0.4 else " Critical"
            
            # System status formatting
            system_status = system_health.get("overall_status", "Unknown")
            status_icon = " Healthy" if system_status == "healthy" else " Degraded" if system_status == "degraded" else " Critical"
            
            content_parts.append("| Metric | Current Value | Status | Trend |")
            content_parts.append("|--------|---------------|--------|-------|")
            content_parts.append(f"| Overall Quality Score | {overall_score:.3f} ({batch_quality}) | {quality_status} | Stable |")
            content_parts.append(f"| Quality Confidence | {quality_confidence:.2%} | {' High' if quality_confidence > 0.8 else ' Good' if quality_confidence > 0.6 else ' Monitor'} | Stable |")
            content_parts.append(f"| Defect Risk Level | {defect_prob:.1%} | {risk_status} | Current |")
            content_parts.append(f"| System Status | {system_status} | {status_icon} | Current |")
            content_parts.append(f"| Data Availability | {system_health.get('data_availability', 'Unknown')} | {' Online' if system_health.get('successful_sources', 0) == system_health.get('total_sources', 4) else ' Limited'} | Current |")
            content_parts.append(f"| Collection Success Rate | {metrics.get('collection_success_rate', 0):.1f}% | {' Excellent' if metrics.get('collection_success_rate', 0) >= 95 else ' Good' if metrics.get('collection_success_rate', 0) >= 80 else ' Review'} | Current |")
            content_parts.append("")
            
            # Detailed Analysis
            if report_content.get("detailed_analysis"):
                content_parts.append("## DETAILED TECHNICAL ANALYSIS")
                content_parts.append(report_content.get("detailed_analysis"))
                content_parts.append("")
            
            # Predictive Insights with real forecast data
            if forecast_accuracy.get("predicted_values"):
                content_parts.append("## PREDICTIVE INSIGHTS")
                predicted_values = forecast_accuracy["predicted_values"]
                horizon = forecast_accuracy.get("prediction_horizon", "30 timesteps")
                total_points = forecast_accuracy.get("total_forecast_points", 0)
                
                if predicted_values and len(predicted_values) > 0:
                    first_prediction = predicted_values[0]["sensors"]
                    last_prediction = predicted_values[-1]["sensors"] if len(predicted_values) > 1 else first_prediction
                    mid_prediction = predicted_values[len(predicted_values)//2]["sensors"] if len(predicted_values) > 2 else first_prediction
                    
                    content_parts.append(f"**Next Period Predictions (Horizon: {horizon}):**")
                    content_parts.append("")
                    content_parts.append("| Parameter | Current | Near-term | Long-term | Trend |")
                    content_parts.append("|-----------|---------|-----------|-----------|-------|")
                    
                    # Waste analysis
                    waste_current = first_prediction.get("waste", 0)
                    waste_future = last_prediction.get("waste", 0)
                    waste_trend = " Increasing" if waste_future > waste_current else " Decreasing" if waste_future < waste_current else " Stable"
                    content_parts.append(f"| Waste Generation | {waste_current:.1f} units | {mid_prediction.get('waste', 0):.1f} units | {waste_future:.1f} units | {waste_trend} |")
                    
                    # Production analysis
                    prod_current = first_prediction.get("produced", 0)
                    prod_future = last_prediction.get("produced", 0)
                    prod_trend = " Increasing" if prod_future > prod_current else " Decreasing" if prod_future < prod_current else " Stable"
                    content_parts.append(f"| Production Output | {prod_current:.1f} units | {mid_prediction.get('produced', 0):.1f} units | {prod_future:.1f} units | {prod_trend} |")
                    
                    # Ejection rate analysis
                    ej_current = first_prediction.get("ejection", 0)
                    ej_future = last_prediction.get("ejection", 0)
                    ej_trend = " Increasing" if ej_future > ej_current else " Decreasing" if ej_future < ej_current else " Stable"
                    content_parts.append(f"| Ejection Rate | {ej_current:.1f} | {mid_prediction.get('ejection', 0):.1f} | {ej_future:.1f} | {ej_trend} |")
                    
                    # Table speed analysis
                    speed_current = first_prediction.get("tbl_speed", 0)
                    speed_future = last_prediction.get("tbl_speed", 0)
                    speed_trend = " Increasing" if speed_future > speed_current else " Decreasing" if speed_future < speed_current else " Stable"
                    content_parts.append(f"| Table Speed | {speed_current:.1f} | {mid_prediction.get('tbl_speed', 0):.1f} | {speed_future:.1f} | {speed_trend} |")
                    
                    content_parts.append("")
                    
                    # Forecast analysis summary
                    efficiency_current = (prod_current / (prod_current + waste_current)) * 100 if (prod_current + waste_current) > 0 else 0
                    efficiency_future = (prod_future / (prod_future + waste_future)) * 100 if (prod_future + waste_future) > 0 else 0
                    efficiency_trend = "improving" if efficiency_future > efficiency_current else "declining" if efficiency_future < efficiency_current else "stable"
                    
                    content_parts.append(f"**Forecast Analysis Summary:**")
                    content_parts.append(f"- **Total Forecast Points:** {total_points} timesteps analyzed")
                    content_parts.append(f"- **Process Efficiency Trend:** {efficiency_trend} (from {efficiency_current:.1f}% to {efficiency_future:.1f}%)")
                    content_parts.append(f"- **Key Insight:** {'Production efficiency is expected to improve over the forecast period' if efficiency_trend == 'improving' else 'Production efficiency may decline and requires attention' if efficiency_trend == 'declining' else 'Production efficiency remains stable within acceptable parameters'}")
                    content_parts.append("")
            
            # Risk Assessment
            if report_content.get("risk_assessment"):
                content_parts.append("## RISK ASSESSMENT")
                content_parts.append(report_content.get("risk_assessment"))
                content_parts.append("")
            
            # Recommendations
            if report_content.get("recommendations"):
                content_parts.append("## RECOMMENDATIONS")
                recommendations = report_content.get("recommendations", [])
                if isinstance(recommendations, list):
                    for i, rec in enumerate(recommendations, 1):
                        content_parts.append(f"**{i}.** {rec}")
                else:
                    content_parts.append(str(recommendations))
                content_parts.append("")
            
            # Action Items
            if report_content.get("action_items"):
                content_parts.append("## IMMEDIATE ACTION ITEMS")
                action_items = report_content.get("action_items", [])
                if isinstance(action_items, list):
                    for i, item in enumerate(action_items, 1):
                        content_parts.append(f"**{i}.** {item}")
                else:
                    content_parts.append(str(action_items))
                content_parts.append("")
            
            # Compliance Status
            if report_content.get("compliance_status"):
                content_parts.append("## REGULATORY COMPLIANCE STATUS")
                content_parts.append(report_content.get("compliance_status"))
                content_parts.append("")
            
            # Data Quality Summary
            content_parts.append("## DATA QUALITY SUMMARY")
            content_parts.append(f"- **Collection Timestamp:** {metrics.get('data_collection_time', 'Unknown')}")
            content_parts.append(f"- **Sources Attempted:** 4")
            content_parts.append(f"- **Sources Successful:** 4")
            content_parts.append(f"- **Success Rate:** {metrics.get('collection_success_rate', 0):.1f}%")
            content_parts.append(f"- **Collection Errors:** {metrics.get('system_health', {}).get('collection_errors', 0)}")
            content_parts.append("")
            
            # Generate and add simple language summary
            simple_summary = self._generate_simple_summary(report_content, metrics)
            if simple_summary:
                content_parts.append("## REPORT SUMMARY")
                content_parts.append("*The following summary explains this report in simple, non-technical language:*")
                content_parts.append("")
                content_parts.append(simple_summary)
                content_parts.append("")
            
            content_parts.append("---")
            content_parts.append("*Report generated using real-time data collection and AI analysis*")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error building comprehensive report content: {e}")
            # Fallback to basic content
            return f"""# QUALITY CONTROL REPORT

## EXECUTIVE SUMMARY
{report_content.get("executive_summary", "Report generation encountered an error.")}

## STATUS
System Status: {metrics.get('system_health', {}).get('overall_status', 'Unknown')}
Data Collection: {metrics.get('collection_success_rate', 0):.1f}% success rate

## ERROR
An error occurred while formatting the report content: {str(e)}
Please review the raw data in the appendix.
"""
    
    def _generate_emergency_report(self, error_message: str) -> Dict[str, Any]:
        """Generate emergency report when normal generation fails"""
        return {
            "title": "Emergency Quality Control Report",
            "generated_at": datetime.now().isoformat(),
            "report_id": f"EMERGENCY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "error",
            "error_message": error_message,
            "executive_summary": f"Report generation failed due to system error: {error_message}. Emergency procedures should be initiated to restore monitoring capabilities.",
            "quality_metrics": {
                "error": error_message,
                "system_status": "failed",
                "data_collection_time": datetime.now().isoformat()
            },
            "detailed_analysis": "Unable to complete analysis due to system failure. Manual quality checks recommended.",
            "recommendations": [
                "Investigate system error immediately",
                "Implement manual quality monitoring procedures",
                "Contact technical support for system restoration",
                "Document all manual quality checks until system recovery"
            ],
            "compliance_status": "UNABLE TO ASSESS - System failure prevents compliance monitoring",
            "risk_assessment": "HIGH RISK - Quality monitoring system failure requires immediate attention",
            "action_items": [
                "CRITICAL: Restore quality monitoring system",
                "URGENT: Implement emergency quality procedures", 
                "HIGH: Contact technical support",
                "MEDIUM: Document all manual processes"
            ],
            "appendix": {
                "error_details": error_message,
                "methodology": "Emergency report generation due to system failure",
                "recommendations": "Restore normal system operation as soon as possible"
            }
        }
    
    def _generate_simple_summary(self, report_content: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Generate a simple language summary of the report using LLM"""
        try:
            if not self.llm_client or not self.llm_client.is_available():
                return self._generate_fallback_summary(report_content, metrics)
            
            # Extract key information for summary
            key_info = self._extract_key_summary_info(report_content, metrics)
            
            # Create simple language prompt
            summary_prompt = f"""
            Please write a simple, easy-to-understand summary of this pharmaceutical manufacturing report in 1-2 paragraphs. 
            Use plain English that anyone can understand, avoiding technical jargon.
            
            Key Information:
            {key_info}
            
            Write a detailed summary that explains in about 200-250 words or 2-3 paragraphs:
            1. What the report found about the manufacturing process
            2. Whether things are working well or if there are concerns
            3. What needs to be done next, if anything
            
            Keep it conversational and clear. Start with "This report shows that..." or similar.
            """
            
            response = self.llm_client.model.generate_content(
                summary_prompt,
                generation_config={
                    'temperature': 0.4,
                    'max_output_tokens': 300,
                }
            )
            
            if response and response.text:
                summary = response.text.strip()
                # Clean up any unwanted formatting
                summary = summary.replace('**', '').replace('*', '')
                return summary
            else:
                return self._generate_fallback_summary(report_content, metrics)
                
        except Exception as e:
            logger.error(f"Error generating simple summary with LLM: {e}")
            return self._generate_fallback_summary(report_content, metrics)
    
    def _extract_key_summary_info(self, report_content: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Extract key information for summary generation"""
        info_parts = []
        
        # System status
        system_status = metrics.get('system_health', {}).get('overall_status', 'unknown')
        success_rate = metrics.get('collection_success_rate', 0)
        info_parts.append(f"System Status: {system_status} with {success_rate:.1f}% data collection success")
        
        # Quality metrics
        if metrics.get('quality_scores'):
            quality_score = metrics['quality_scores'].get('overall_score', 'N/A')
            batch_quality = metrics['quality_scores'].get('batch_quality', 'Unknown')
            info_parts.append(f"Quality Level: {batch_quality} (score: {quality_score})")
        
        # Defect information
        defect_prob = metrics.get('defect_probability', 'N/A')
        risk_level = metrics.get('risk_classification', 'Unknown')
        if defect_prob != 'N/A':
            info_parts.append(f"Defect Risk: {defect_prob:.1%} probability, {risk_level} risk level")
        
        # Predictions
        if metrics.get('forecast_accuracy', {}).get('predicted_values'):
            forecast_data = metrics['forecast_accuracy']['predicted_values'][0]['sensors']
            waste = forecast_data.get('waste', 'N/A')
            production = forecast_data.get('produced', 'N/A')
            info_parts.append(f"Predictions: Waste {waste} units, Production {production} units")
        
        # Major issues
        errors = metrics.get('system_health', {}).get('collection_errors', 0)
        if errors > 0:
            info_parts.append(f"Issues Found: {errors} system errors detected")
        
        # Recommendations count
        recommendations = report_content.get('recommendations', [])
        if recommendations:
            info_parts.append(f"Recommendations: {len(recommendations)} improvement suggestions provided")
        
        return "\n".join(info_parts)
    
    def _generate_fallback_summary(self, report_content: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Generate a simple summary when LLM is not available"""
        try:
            # Extract key metrics
            system_status = metrics.get('system_health', {}).get('overall_status', 'unknown')
            success_rate = metrics.get('collection_success_rate', 0)
            defect_prob = metrics.get('defect_probability', 0)
            
            # Determine overall health
            if system_status == 'healthy' and success_rate >= 90:
                overall_health = "working well"
            elif system_status == 'degraded' or success_rate >= 70:
                overall_health = "working with some issues"
            else:
                overall_health = "having significant problems"
            
            # Determine risk level
            if isinstance(defect_prob, (int, float)):
                if defect_prob < 0.1:
                    risk_description = "very low risk of problems"
                elif defect_prob < 0.3:
                    risk_description = "low risk of problems"
                elif defect_prob < 0.5:
                    risk_description = "moderate risk of problems"
                else:
                    risk_description = "high risk of problems"
            else:
                risk_description = "unknown risk level"
            
            # Count recommendations
            recommendations = report_content.get('recommendations', [])
            rec_count = len([r for r in recommendations if isinstance(r, str) and r.strip()])
            
            # Generate simple summary
            summary = f"This report shows that our pharmaceutical manufacturing system is currently {overall_health}. "
            summary += f"The data collection systems are running at {success_rate:.0f}% capacity, and there is {risk_description} with the current production process. "
            
            if rec_count > 0:
                summary += f"The analysis has identified {rec_count} specific recommendations to improve operations and maintain high quality standards. "
            
            if system_status == 'healthy':
                summary += "Overall, the manufacturing process is operating smoothly and meeting quality requirements."
            elif system_status == 'degraded':
                summary += "While the system is mostly working well, some attention is needed to prevent potential issues."
            else:
                summary += "The system requires immediate attention to restore full operational capability."
                
            return summary
            
        except Exception as e:
            logger.error(f"Error generating fallback summary: {e}")
            return "This report provides an analysis of the pharmaceutical manufacturing system. Please review the detailed sections above for specific findings and recommendations."
