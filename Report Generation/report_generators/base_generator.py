import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import pandas as pd

from knowledge_base.knowledge_manager import KnowledgeBaseManager
from llm_integration.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class BaseReportGenerator:
    """
    Base class for report generators in the PharmaCopilot system.
    Provides common functionality for data collection, context retrieval, and report generation.
    """
    
    def __init__(self, api_base_url: str = "http://165.22.211.17:8000"):
        self.api_base_url = api_base_url
        self.kb_manager = KnowledgeBaseManager()
        # Initialize Gemini client with API key
        self.llm_client = GeminiClient(api_key="AIzaSyCXvrGe95R2dOYX_p587K2QaJZhPOAqNGM")
        self.report_type = "base"
        
    async def collect_current_data(self) -> Dict[str, Any]:
        """Collect current data from all available APIs"""
        collected_data = {}
        
        # Collect from different data sources - using correct endpoints
        data_sources = [
            ('forecasting', f"{self.api_base_url}/api/forecast"),
            ('classification', f"{self.api_base_url}/api/defect"),
            ('quality', f"{self.api_base_url}/api/quality"),
            ('rl_actions', f"{self.api_base_url}/api/rl_action/baseline")
        ]
        
        async with aiohttp.ClientSession() as session:
            for source_name, url in data_sources:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            collected_data[source_name] = data
                        else:
                            logger.warning(f"Failed to collect data from {source_name}: {response.status}")
                            collected_data[source_name] = {'error': f'HTTP {response.status}'}
                except Exception as e:
                    logger.error(f"Error collecting data from {source_name}: {e}")
                    collected_data[source_name] = {'error': str(e)}
        
        return collected_data
    
    def get_relevant_context(self, query: str, data_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get relevant context from knowledge base"""
        if data_types is None:
            data_types = ['historical_data', 'documentation']
        
        try:
            # Search in historical_data collection first
            historical_context = self.kb_manager.search_relevant_context(
                query=query,
                collection='historical_data',
                n_results=5
            )
            
            # Search in documentation collection
            documentation_context = self.kb_manager.search_relevant_context(
                query=query,
                collection='documentation',
                n_results=5
            )
            
            # Combine results
            context_items = historical_context + documentation_context
            
            # Sort by relevance score
            context_items.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return context_items
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return []
    
    def get_recent_summaries(self, hours: int = 24) -> Dict[str, Any]:
        """Get recent data summaries for trend analysis"""
        try:
            summaries = {}
            
            # Get summaries from different data sources
            data_sources = ['classification', 'forecasting', 'rl_actions']
            
            for source in data_sources:
                try:
                    summary = self.kb_manager.get_recent_summary(source, hours)
                    summaries[source] = summary
                except Exception as e:
                    logger.error(f"Error getting summary for {source}: {e}")
                    summaries[source] = {'error': str(e)}
            
            return summaries
        except Exception as e:
            logger.error(f"Error getting recent summaries: {e}")
            return {}
    
    def extract_key_metrics(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from collected data"""
        metrics = {}
        
        try:
            # Extract classification metrics (defect prediction)
            if 'classification' in collected_data and 'error' not in collected_data['classification']:
                classification_data = collected_data['classification']
                metrics['defect_probability'] = classification_data.get('defect_probability', 'N/A')
                metrics['risk_level'] = classification_data.get('risk_level', 'N/A')
                metrics['confidence_score'] = classification_data.get('confidence', 'N/A')
            
            # Extract quality metrics
            if 'quality' in collected_data and 'error' not in collected_data['quality']:
                quality_data = collected_data['quality']
                metrics['quality_class'] = quality_data.get('quality_class', 'N/A')
                metrics['quality_confidence'] = quality_data.get('confidence', 'N/A')
            
            # Extract forecasting metrics
            if 'forecasting' in collected_data and 'error' not in collected_data['forecasting']:
                forecasting_data = collected_data['forecasting']
                metrics['forecast_horizon'] = forecasting_data.get('forecast_horizon', 'N/A')
                metrics['forecast_points'] = len(forecasting_data.get('forecast', []))
            
            # Extract RL metrics
            if 'rl_actions' in collected_data and 'error' not in collected_data['rl_actions']:
                rl_data = collected_data['rl_actions']
                metrics['recommended_actions'] = rl_data.get('recommended_actions', 'N/A')
                metrics['model_type'] = rl_data.get('model_type', 'N/A')
            
            # Calculate risk level based on defect probability
            defect_prob = metrics.get('defect_probability', 0)
            if isinstance(defect_prob, (int, float)):
                if defect_prob > 0.8:
                    metrics['risk_level'] = 'Critical'
                elif defect_prob > 0.6:
                    metrics['risk_level'] = 'High'
                elif defect_prob > 0.4:
                    metrics['risk_level'] = 'Medium'
                elif defect_prob > 0.2:
                    metrics['risk_level'] = 'Low'
                else:
                    metrics['risk_level'] = 'Very Low'
            else:
                metrics['risk_level'] = 'Unknown'
                
        except Exception as e:
            logger.error(f"Error extracting key metrics: {e}")
            metrics = {'error': str(e)}
        
        return metrics
    
    def build_context_string(self, context_items: List[Dict[str, Any]]) -> str:
        """Build a context string from context items"""
        if not context_items:
            return "No relevant historical context available."
        
        context_parts = []
        for item in context_items:
            if 'content' in item:
                context_parts.append(item['content'])
            elif 'data' in item:
                context_parts.append(str(item['data']))
        
        return "\n\n".join(context_parts)
    
    def format_report_response(self, content: str, metadata: Dict[str, Any], 
                             generation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format the final report response"""
        return {
            'report_content': content,
            'generation_timestamp': datetime.now().isoformat(),
            'metadata': metadata,
            'generation_result': generation_result,
            'status': 'success'
        }
    
    async def generate_report(self, query: str, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Base report generation method - should be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_report method") 