"""
Classification Data Collector for PharmaCopilot
Collects and manages defect classification and quality prediction data
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ClassificationCollector:
    """
    Collects classification data (defect prediction and quality assessment) from prediction APIs
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.defect_endpoint = f"{api_base_url}/api/defect"
        self.quality_endpoint = f"{api_base_url}/api/quality"
        self.recent_classifications = []
        self.max_history = 100  # Keep last 100 classifications
        
    async def collect_data(self) -> Dict[str, Any]:
        """Collect current classification data from APIs"""
        try:
            classification_record = {
                'timestamp': datetime.now().isoformat(),
                'defect_prediction': await self._collect_defect_data(),
                'quality_prediction': await self._collect_quality_data()
            }
            
            self._add_to_history(classification_record)
            logger.info("Successfully collected classification data")
            return classification_record
            
        except Exception as e:
            logger.error(f"Error collecting classification data: {e}")
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'defect_prediction': {'api_status': 'error', 'error': str(e)},
                'quality_prediction': {'api_status': 'error', 'error': str(e)}
            }
            self._add_to_history(error_record)
            return error_record
    
    async def _collect_defect_data(self) -> Dict[str, Any]:
        """Collect defect prediction data"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.defect_endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'api_status': 'success',
                            'defect_probability': data.get('defect_probability', 0.0),
                            'risk_level': data.get('risk_level', 'unknown'),
                            'confidence': data.get('confidence', 0.0),
                            'model_info': data.get('model_info', {}),
                            'features_used': data.get('features_used', [])
                        }
                    else:
                        return {
                            'api_status': 'error',
                            'error': f'HTTP {response.status}',
                            'endpoint': self.defect_endpoint
                        }
        except Exception as e:
            return {
                'api_status': 'error',
                'error': str(e),
                'endpoint': self.defect_endpoint
            }
    
    async def _collect_quality_data(self) -> Dict[str, Any]:
        """Collect quality classification data"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.quality_endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'api_status': 'success',
                            'quality_class': data.get('quality_class', 'unknown'),
                            'confidence': data.get('confidence', 0.0),
                            'class_probabilities': data.get('class_probabilities', {}),
                            'model_info': data.get('model_info', {}),
                            'features_used': data.get('features_used', [])
                        }
                    else:
                        return {
                            'api_status': 'error',
                            'error': f'HTTP {response.status}',
                            'endpoint': self.quality_endpoint
                        }
        except Exception as e:
            return {
                'api_status': 'error',
                'error': str(e),
                'endpoint': self.quality_endpoint
            }
    
    def get_classification_summary(self, hours: int = 6) -> Dict[str, Any]:
        """Get summary of recent classification data"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_classifications = [
                c for c in self.recent_classifications 
                if datetime.fromisoformat(c['timestamp']) >= cutoff_time
            ]
            
            if not recent_classifications:
                return {
                    'status': 'no_recent_data',
                    'message': f'No classification data available in last {hours} hours',
                    'hours_analyzed': hours
                }
            
            # Analyze defect predictions
            defect_analysis = self._analyze_defect_predictions(recent_classifications)
            
            # Analyze quality predictions
            quality_analysis = self._analyze_quality_predictions(recent_classifications)
            
            # Calculate overall performance
            successful_defect_predictions = sum(
                1 for c in recent_classifications 
                if c.get('defect_prediction', {}).get('api_status') == 'success'
            )
            
            successful_quality_predictions = sum(
                1 for c in recent_classifications 
                if c.get('quality_prediction', {}).get('api_status') == 'success'
            )
            
            overall_success_rate = (
                (successful_defect_predictions + successful_quality_predictions) / 
                (len(recent_classifications) * 2)
            ) * 100 if recent_classifications else 0
            
            return {
                'status': 'success',
                'hours_analyzed': hours,
                'total_classifications': len(recent_classifications),
                'defect_analysis': defect_analysis,
                'quality_analysis': quality_analysis,
                'successful_defect_predictions': successful_defect_predictions,
                'successful_quality_predictions': successful_quality_predictions,
                'overall_success_rate': overall_success_rate,
                'data_quality': 'excellent' if overall_success_rate > 90 else 'good' if overall_success_rate > 75 else 'limited'
            }
            
        except Exception as e:
            logger.error(f"Error generating classification summary: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'hours_analyzed': hours
            }
    
    def _analyze_defect_predictions(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze defect prediction trends"""
        try:
            successful_defect_data = [
                c['defect_prediction'] for c in classifications
                if c.get('defect_prediction', {}).get('api_status') == 'success'
            ]
            
            if not successful_defect_data:
                return {'status': 'no_successful_data', 'type': 'defect_prediction'}
            
            # Extract defect probabilities
            defect_probs = [
                d.get('defect_probability', 0) for d in successful_defect_data
                if isinstance(d.get('defect_probability'), (int, float))
            ]
            
            if not defect_probs:
                return {'status': 'no_valid_probabilities', 'type': 'defect_prediction'}
            
            # Calculate statistics
            avg_defect_prob = sum(defect_probs) / len(defect_probs)
            max_defect_prob = max(defect_probs)
            min_defect_prob = min(defect_probs)
            
            # Determine trend
            if len(defect_probs) >= 2:
                recent_avg = sum(defect_probs[-3:]) / min(3, len(defect_probs))
                earlier_avg = sum(defect_probs[:3]) / min(3, len(defect_probs))
                
                if recent_avg > earlier_avg * 1.1:
                    trend = "increasing"
                elif recent_avg < earlier_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            # Risk level distribution
            risk_levels = [d.get('risk_level', 'unknown') for d in successful_defect_data]
            risk_distribution = {}
            for risk in risk_levels:
                risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            
            # Current risk assessment
            current_defect_prob = defect_probs[-1] if defect_probs else 0
            if current_defect_prob > 0.7:
                current_risk = "critical"
            elif current_defect_prob > 0.5:
                current_risk = "high"
            elif current_defect_prob > 0.3:
                current_risk = "medium"
            else:
                current_risk = "low"
            
            return {
                'status': 'success',
                'type': 'defect_prediction',
                'total_predictions': len(successful_defect_data),
                'average_defect_probability': avg_defect_prob,
                'max_defect_probability': max_defect_prob,
                'min_defect_probability': min_defect_prob,
                'current_defect_probability': current_defect_prob,
                'trend': trend,
                'current_risk_level': current_risk,
                'risk_distribution': risk_distribution,
                'confidence_avg': sum(d.get('confidence', 0) for d in successful_defect_data) / len(successful_defect_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing defect predictions: {e}")
            return {'status': 'error', 'error': str(e), 'type': 'defect_prediction'}
    
    def _analyze_quality_predictions(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze quality prediction trends"""
        try:
            successful_quality_data = [
                c['quality_prediction'] for c in classifications
                if c.get('quality_prediction', {}).get('api_status') == 'success'
            ]
            
            if not successful_quality_data:
                return {'status': 'no_successful_data', 'type': 'quality_prediction'}
            
            # Quality class distribution
            quality_classes = [q.get('quality_class', 'unknown') for q in successful_quality_data]
            class_distribution = {}
            for qc in quality_classes:
                class_distribution[qc] = class_distribution.get(qc, 0) + 1
            
            # Most common quality class
            most_common_class = max(class_distribution.keys(), key=lambda k: class_distribution[k]) if class_distribution else 'unknown'
            
            # Confidence statistics
            confidences = [
                q.get('confidence', 0) for q in successful_quality_data
                if isinstance(q.get('confidence'), (int, float))
            ]
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Current quality status
            current_quality = successful_quality_data[-1] if successful_quality_data else {}
            current_class = current_quality.get('quality_class', 'unknown')
            current_confidence = current_quality.get('confidence', 0)
            
            return {
                'status': 'success',
                'type': 'quality_prediction',
                'total_predictions': len(successful_quality_data),
                'class_distribution': class_distribution,
                'most_common_class': most_common_class,
                'current_quality_class': current_class,
                'current_confidence': current_confidence,
                'average_confidence': avg_confidence,
                'quality_stability': 'stable' if len(set(quality_classes[-5:])) <= 2 else 'variable'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing quality predictions: {e}")
            return {'status': 'error', 'error': str(e), 'type': 'quality_prediction'}
    
    def get_risk_assessment(self) -> Dict[str, Any]:
        """Get current risk assessment based on latest data"""
        try:
            if not self.recent_classifications:
                return {'status': 'no_data', 'message': 'No classification data available'}
            
            latest = self.recent_classifications[-1]
            defect_data = latest.get('defect_prediction', {})
            quality_data = latest.get('quality_prediction', {})
            
            # Combine risk factors
            risk_factors = []
            overall_risk_score = 0
            
            # Defect risk
            if defect_data.get('api_status') == 'success':
                defect_prob = defect_data.get('defect_probability', 0)
                if defect_prob > 0.7:
                    risk_factors.append("Critical defect probability detected")
                    overall_risk_score += 40
                elif defect_prob > 0.5:
                    risk_factors.append("High defect probability")
                    overall_risk_score += 25
                elif defect_prob > 0.3:
                    risk_factors.append("Moderate defect risk")
                    overall_risk_score += 15
            else:
                risk_factors.append("Defect prediction system unavailable")
                overall_risk_score += 20
            
            # Quality risk
            if quality_data.get('api_status') == 'success':
                quality_class = quality_data.get('quality_class', 'unknown')
                if quality_class.lower() in ['low', 'poor']:
                    risk_factors.append("Poor quality classification")
                    overall_risk_score += 30
                elif quality_class.lower() == 'medium':
                    risk_factors.append("Medium quality classification")
                    overall_risk_score += 15
            else:
                risk_factors.append("Quality prediction system unavailable")
                overall_risk_score += 15
            
            # Determine overall risk level
            if overall_risk_score >= 60:
                risk_level = "critical"
            elif overall_risk_score >= 40:
                risk_level = "high"
            elif overall_risk_score >= 20:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                'status': 'success',
                'overall_risk_level': risk_level,
                'risk_score': overall_risk_score,
                'risk_factors': risk_factors,
                'timestamp': latest.get('timestamp'),
                'defect_probability': defect_data.get('defect_probability', 'N/A'),
                'quality_class': quality_data.get('quality_class', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _add_to_history(self, classification_record: Dict[str, Any]):
        """Add classification record to history with size management"""
        self.recent_classifications.append(classification_record)
        
        # Keep only recent records
        if len(self.recent_classifications) > self.max_history:
            self.recent_classifications = self.recent_classifications[-self.max_history:]
    
    def get_historical_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical classification data"""
        return self.recent_classifications[-limit:] if self.recent_classifications else []
    
    def clear_history(self):
        """Clear historical data"""
        self.recent_classifications.clear()
        logger.info("Classification history cleared")
