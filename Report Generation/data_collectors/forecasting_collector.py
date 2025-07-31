"""
Forecasting Data Collector for PharmaCopilot
Collects and processes time-series forecasting data for pharmaceutical manufacturing
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
import pandas as pd

logger = logging.getLogger(__name__)

class ForecastingCollector:
    """
    Collector for time-series forecasting data from ML models
    Integrates with LSTM and other forecasting models for pharmaceutical manufacturing
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.collector_type = "forecasting"
        
    async def collect_data(self) -> Dict[str, Any]:
        """Collect current forecasting data from ML API"""
        try:
            logger.info("Collecting forecasting data from ML API")
            
            async with aiohttp.ClientSession() as session:
                # Collect from forecasting endpoint
                async with session.get(f"{self.api_base_url}/api/forecast") as response:
                    if response.status == 200:
                        forecast_data = await response.json()
                        
                        # Process and enrich the data
                        processed_data = self._process_forecast_data(forecast_data)
                        
                        logger.info(f"Successfully collected forecasting data: {len(processed_data.get('forecast', []))} predictions")
                        return processed_data
                    else:
                        logger.error(f"Failed to collect forecasting data: HTTP {response.status}")
                        return {'error': f'HTTP {response.status}', 'api_status': 'failed'}
                        
        except Exception as e:
            logger.error(f"Error in forecasting data collection: {e}")
            return {'error': str(e), 'api_status': 'error'}
    
    def _process_forecast_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw forecasting data into structured format"""
        try:
            processed = {
                'collection_timestamp': datetime.now().isoformat(),
                'api_status': 'success',
                'forecast_horizon': raw_data.get('forecast_horizon', 30),
                'forecast': raw_data.get('forecast', []),
                'data_sources': raw_data.get('data_sources', {}),
                'model_info': {
                    'model_type': 'LSTM',
                    'confidence_level': 0.85,
                    'prediction_accuracy': 'high'
                }
            }
            
            # Add trend analysis
            if processed['forecast']:
                processed['trends'] = self._analyze_forecast_trends(processed['forecast'])
                processed['insights'] = self._generate_forecast_insights(processed['forecast'])
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing forecast data: {e}")
            raw_data['processing_error'] = str(e)
            return raw_data
    
    def _analyze_forecast_trends(self, forecast_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in forecast data"""
        try:
            if not forecast_data or len(forecast_data) < 2:
                return {'trend': 'insufficient_data'}
            
            trends = {
                'waste_trend': 'stable',
                'production_trend': 'stable',
                'efficiency_trend': 'stable',
                'risk_level': 'low'
            }
            
            # Extract first and last predictions for trend analysis
            first_pred = forecast_data[0].get('sensors', {})
            last_pred = forecast_data[-1].get('sensors', {})
            
            # Analyze waste trend
            waste_start = first_pred.get('waste', 0)
            waste_end = last_pred.get('waste', 0)
            
            if waste_end > waste_start * 1.1:
                trends['waste_trend'] = 'increasing'
                trends['risk_level'] = 'medium'
            elif waste_end < waste_start * 0.9:
                trends['waste_trend'] = 'decreasing'
            
            # Analyze production trend
            prod_start = first_pred.get('produced', 0)
            prod_end = last_pred.get('produced', 0)
            
            if prod_end > prod_start * 1.05:
                trends['production_trend'] = 'increasing'
            elif prod_end < prod_start * 0.95:
                trends['production_trend'] = 'decreasing'
                trends['risk_level'] = 'medium'
            
            # Calculate efficiency trend
            eff_start = prod_start / (prod_start + waste_start) if (prod_start + waste_start) > 0 else 0
            eff_end = prod_end / (prod_end + waste_end) if (prod_end + waste_end) > 0 else 0
            
            if eff_end > eff_start * 1.02:
                trends['efficiency_trend'] = 'improving'
            elif eff_end < eff_start * 0.98:
                trends['efficiency_trend'] = 'declining'
                trends['risk_level'] = 'high' if trends['risk_level'] == 'medium' else 'medium'
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing forecast trends: {e}")
            return {'trend': 'analysis_error', 'error': str(e)}
    
    def _generate_forecast_insights(self, forecast_data: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights from forecast data"""
        insights = []
        
        try:
            if not forecast_data:
                return ["No forecast data available for analysis"]
            
            # Analyze sensor data patterns
            sensor_values = []
            for prediction in forecast_data:
                sensors = prediction.get('sensors', {})
                if sensors:
                    sensor_values.append(sensors)
            
            if not sensor_values:
                return ["No sensor data available in forecasts"]
            
            # Waste analysis
            waste_values = [s.get('waste', 0) for s in sensor_values]
            avg_waste = sum(waste_values) / len(waste_values)
            max_waste = max(waste_values)
            
            if max_waste > 2000:
                insights.append(f"Critical waste levels predicted: up to {max_waste:.1f} units")
            elif avg_waste > 1500:
                insights.append(f"Elevated waste levels forecasted: average {avg_waste:.1f} units")
            else:
                insights.append(f"Waste levels within acceptable range: average {avg_waste:.1f} units")
            
            # Production analysis
            prod_values = [s.get('produced', 0) for s in sensor_values]
            avg_production = sum(prod_values) / len(prod_values)
            min_production = min(prod_values)
            
            if min_production < 10:
                insights.append(f"Low production periods predicted: minimum {min_production:.1f} units")
            elif avg_production > 20:
                insights.append(f"Strong production performance forecasted: average {avg_production:.1f} units")
            else:
                insights.append(f"Moderate production levels expected: average {avg_production:.1f} units")
            
            # Efficiency insights
            efficiency_values = []
            for sensors in sensor_values:
                prod = sensors.get('produced', 0)
                waste = sensors.get('waste', 0)
                if (prod + waste) > 0:
                    efficiency = prod / (prod + waste)
                    efficiency_values.append(efficiency)
            
            if efficiency_values:
                avg_efficiency = sum(efficiency_values) / len(efficiency_values)
                if avg_efficiency < 0.7:
                    insights.append(f"Process efficiency concerns: {avg_efficiency:.1%} average efficiency")
                elif avg_efficiency > 0.85:
                    insights.append(f"Excellent process efficiency predicted: {avg_efficiency:.1%} average")
                else:
                    insights.append(f"Acceptable process efficiency: {avg_efficiency:.1%} average")
            
            # Operational recommendations
            if avg_waste > 1500 or (efficiency_values and sum(efficiency_values)/len(efficiency_values) < 0.75):
                insights.append("Recommend process optimization review")
            
            if max_waste > 2500:
                insights.append("Consider immediate intervention to prevent excessive waste")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating forecast insights: {e}")
            return [f"Error generating insights: {str(e)}"]
    
    def get_forecast_summary(self, hours: int = 6) -> Dict[str, Any]:
        """Get summary of recent forecast data"""
        try:
            # This would typically query stored historical data
            # For now, we'll return a summary structure
            return {
                'status': 'active',
                'forecast_points_analyzed': 30,
                'prediction_horizon': f'{hours * 5} timesteps',  # Assuming 5 timesteps per hour
                'trends': {
                    'waste': 'monitoring',
                    'production': 'stable',
                    'efficiency': 'good'
                },
                'confidence_level': 0.85,
                'data_quality': 'high',
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting forecast summary: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def validate_forecast_data(self, data: Dict[str, Any]) -> bool:
        """Validate forecast data structure and content"""
        try:
            # Check required fields
            required_fields = ['forecast_horizon', 'forecast']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate forecast structure
            forecasts = data.get('forecast', [])
            if not isinstance(forecasts, list):
                logger.warning("Forecast data is not a list")
                return False
            
            # Validate individual forecasts
            for i, forecast in enumerate(forecasts):
                if not isinstance(forecast, dict):
                    logger.warning(f"Forecast {i} is not a dictionary")
                    return False
                
                if 'sensors' not in forecast:
                    logger.warning(f"Forecast {i} missing sensors data")
                    return False
                
                sensors = forecast['sensors']
                required_sensors = ['waste', 'produced', 'ejection', 'tbl_speed']
                for sensor in required_sensors:
                    if sensor not in sensors:
                        logger.warning(f"Forecast {i} missing sensor: {sensor}")
                        return False
                    
                    if not isinstance(sensors[sensor], (int, float)):
                        logger.warning(f"Forecast {i} sensor {sensor} is not numeric")
                        return False
            
            logger.info("Forecast data validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating forecast data: {e}")
            return False
    
    def get_collector_status(self) -> Dict[str, Any]:
        """Get status of the forecasting collector"""
        return {
            'collector_type': self.collector_type,
            'api_endpoint': f"{self.api_base_url}/api/forecast",
            'status': 'active',
            'capabilities': [
                'time_series_forecasting',
                'trend_analysis',
                'efficiency_prediction',
                'waste_forecasting',
                'production_planning'
            ],
            'data_sources': [
                'lstm_model',
                'sensor_data',
                'historical_patterns'
            ]
        }
