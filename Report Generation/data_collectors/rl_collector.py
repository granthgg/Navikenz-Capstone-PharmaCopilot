"""
Reinforcement Learning (RL) Data Collector for PharmaCopilot
Collects and manages RL action recommendations and optimization data
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class RLCollector:
    """
    Collects RL action recommendations from multiple RL models and manages optimization history
    """
    
    def __init__(self, api_base_url: str = "http://165.22.211.17:8000"):
        self.api_base_url = api_base_url
        self.rl_endpoints = {
            'baseline_model': f"{api_base_url}/api/rl_action/baseline",
            'current_model': f"{api_base_url}/api/rl_action/current", 
            'new_model': f"{api_base_url}/api/rl_action/new"
        }
        self.recent_actions = []
        self.max_history = 100  # Keep last 100 RL action sets
        
    async def collect_data(self) -> Dict[str, Any]:
        """Collect current RL action recommendations from all models"""
        try:
            rl_record = {
                'timestamp': datetime.now().isoformat(),
                'baseline_model': await self._collect_rl_actions('baseline_model'),
                'current_model': await self._collect_rl_actions('current_model'),
                'new_model': await self._collect_rl_actions('new_model')
            }
            
            self._add_to_history(rl_record)
            logger.info("Successfully collected RL action data from all models")
            return rl_record
            
        except Exception as e:
            logger.error(f"Error collecting RL data: {e}")
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'baseline_model': {'api_status': 'error', 'error': str(e)},
                'current_model': {'api_status': 'error', 'error': str(e)},
                'new_model': {'api_status': 'error', 'error': str(e)}
            }
            self._add_to_history(error_record)
            return error_record
    
    async def _collect_rl_actions(self, model_name: str) -> Dict[str, Any]:
        """Collect RL actions from a specific model"""
        try:
            endpoint = self.rl_endpoints.get(model_name)
            if not endpoint:
                return {
                    'api_status': 'error',
                    'error': f'Unknown model: {model_name}'
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'api_status': 'success',
                            'model_type': model_name,
                            'recommended_actions': data.get('recommended_actions', {}),
                            'state_summary': data.get('state_summary', {}),
                            'action_confidence': data.get('confidence', 0.0),
                            'expected_reward': data.get('expected_reward', 0.0),
                            'model_info': data.get('model_info', {}),
                            'optimization_target': data.get('optimization_target', 'unknown')
                        }
                    else:
                        return {
                            'api_status': 'error',
                            'error': f'HTTP {response.status}',
                            'endpoint': endpoint,
                            'model_type': model_name
                        }
        except Exception as e:
            return {
                'api_status': 'error',
                'error': str(e),
                'endpoint': endpoint,
                'model_type': model_name
            }
    
    def get_rl_summary(self, hours: int = 6) -> Dict[str, Any]:
        """Get summary of recent RL action recommendations"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_actions = [
                a for a in self.recent_actions 
                if datetime.fromisoformat(a['timestamp']) >= cutoff_time
            ]
            
            if not recent_actions:
                return {
                    'status': 'no_recent_data',
                    'message': f'No RL action data available in last {hours} hours',
                    'hours_analyzed': hours
                }
            
            # Analyze each model's performance
            model_analysis = {}
            for model_name in self.rl_endpoints.keys():
                model_analysis[model_name] = self._analyze_model_performance(recent_actions, model_name)
            
            # Get consensus recommendations
            consensus_analysis = self._analyze_action_consensus(recent_actions)
            
            # Calculate overall system performance
            total_model_calls = len(recent_actions) * 3  # 3 models per collection
            successful_calls = sum(
                sum(1 for model in ['baseline_model', 'current_model', 'new_model'] 
                    if action.get(model, {}).get('api_status') == 'success')
                for action in recent_actions
            )
            
            success_rate = (successful_calls / total_model_calls) * 100 if total_model_calls > 0 else 0
            
            return {
                'status': 'success',
                'hours_analyzed': hours,
                'total_action_sets': len(recent_actions),
                'model_analysis': model_analysis,
                'consensus_analysis': consensus_analysis,
                'successful_model_calls': successful_calls,
                'total_model_calls': total_model_calls,
                'overall_success_rate': success_rate,
                'data_quality': 'excellent' if success_rate > 90 else 'good' if success_rate > 75 else 'limited'
            }
            
        except Exception as e:
            logger.error(f"Error generating RL summary: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'hours_analyzed': hours
            }
    
    def _analyze_model_performance(self, actions: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
        """Analyze performance of a specific RL model"""
        try:
            model_data = [
                action.get(model_name, {}) for action in actions
                if action.get(model_name, {}).get('api_status') == 'success'
            ]
            
            if not model_data:
                return {
                    'status': 'no_successful_data',
                    'model': model_name,
                    'total_calls': len(actions)
                }
            
            # Calculate average metrics
            avg_confidence = sum(m.get('action_confidence', 0) for m in model_data) / len(model_data)
            avg_reward = sum(m.get('expected_reward', 0) for m in model_data) / len(model_data)
            
            # Analyze action consistency
            all_actions = [m.get('recommended_actions', {}) for m in model_data]
            action_types = set()
            for actions_dict in all_actions:
                if isinstance(actions_dict, dict):
                    action_types.update(actions_dict.keys())
            
            # Get most recent recommendation
            latest_recommendation = model_data[-1] if model_data else {}
            
            # Determine model stability (consistent recommendations)
            if len(model_data) >= 3:
                recent_actions = [m.get('recommended_actions', {}) for m in model_data[-3:]]
                stability = self._calculate_action_stability(recent_actions)
            else:
                stability = 'insufficient_data'
            
            return {
                'status': 'success',
                'model': model_name,
                'successful_calls': len(model_data),
                'total_calls': len(actions),
                'success_rate': (len(model_data) / len(actions)) * 100,
                'average_confidence': avg_confidence,
                'average_expected_reward': avg_reward,
                'action_types_seen': list(action_types),
                'latest_recommendation': latest_recommendation.get('recommended_actions', {}),
                'model_stability': stability
            }
            
        except Exception as e:
            logger.error(f"Error analyzing model {model_name}: {e}")
            return {
                'status': 'error',
                'model': model_name,
                'error': str(e)
            }
    
    def _calculate_action_stability(self, recent_actions: List[Dict[str, Any]]) -> str:
        """Calculate how stable/consistent recent actions are"""
        try:
            if len(recent_actions) < 2:
                return 'insufficient_data'
            
            # Compare action values across recent recommendations
            all_action_keys = set()
            for actions in recent_actions:
                if isinstance(actions, dict):
                    all_action_keys.update(actions.keys())
            
            if not all_action_keys:
                return 'no_actions'
            
            # Check variance in action values
            high_variance_count = 0
            for key in all_action_keys:
                values = []
                for actions in recent_actions:
                    if isinstance(actions, dict) and key in actions:
                        val = actions[key]
                        if isinstance(val, (int, float)):
                            values.append(val)
                
                if len(values) >= 2:
                    avg_val = sum(values) / len(values)
                    max_deviation = max(abs(v - avg_val) for v in values)
                    
                    # If max deviation is more than 50% of average, consider high variance
                    if avg_val != 0 and max_deviation / abs(avg_val) > 0.5:
                        high_variance_count += 1
            
            # Determine stability
            if high_variance_count == 0:
                return 'very_stable'
            elif high_variance_count <= len(all_action_keys) * 0.3:
                return 'stable'
            elif high_variance_count <= len(all_action_keys) * 0.6:
                return 'moderate'
            else:
                return 'unstable'
                
        except Exception as e:
            logger.error(f"Error calculating action stability: {e}")
            return 'error'
    
    def _analyze_action_consensus(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze consensus between different RL models"""
        try:
            if not actions:
                return {'status': 'no_data'}
            
            # Get latest action set for consensus analysis
            latest_actions = actions[-1] if actions else {}
            
            successful_models = []
            model_recommendations = {}
            
            for model_name in self.rl_endpoints.keys():
                model_data = latest_actions.get(model_name, {})
                if model_data.get('api_status') == 'success':
                    successful_models.append(model_name)
                    model_recommendations[model_name] = model_data.get('recommended_actions', {})
            
            if len(successful_models) < 2:
                return {
                    'status': 'insufficient_models',
                    'successful_models': successful_models,
                    'message': 'Need at least 2 models for consensus analysis'
                }
            
            # Find common action keys
            all_action_keys = set()
            for recommendations in model_recommendations.values():
                if isinstance(recommendations, dict):
                    all_action_keys.update(recommendations.keys())
            
            # Analyze consensus for each action
            consensus_actions = {}
            consensus_level = 'high'
            
            for action_key in all_action_keys:
                values = []
                models_with_action = []
                
                for model_name, recommendations in model_recommendations.items():
                    if isinstance(recommendations, dict) and action_key in recommendations:
                        val = recommendations[action_key]
                        if isinstance(val, (int, float)):
                            values.append(val)
                            models_with_action.append(model_name)
                
                if len(values) >= 2:
                    avg_value = sum(values) / len(values)
                    max_deviation = max(abs(v - avg_value) for v in values)
                    
                    # Calculate consensus level for this action
                    if avg_value != 0:
                        relative_deviation = max_deviation / abs(avg_value)
                        if relative_deviation > 0.5:
                            action_consensus = 'low'
                        elif relative_deviation > 0.2:
                            action_consensus = 'medium'
                        else:
                            action_consensus = 'high'
                    else:
                        action_consensus = 'high' if max_deviation < 0.1 else 'low'
                    
                    consensus_actions[action_key] = {
                        'average_value': avg_value,
                        'values_by_model': dict(zip(models_with_action, values)),
                        'consensus_level': action_consensus,
                        'participating_models': models_with_action
                    }
                    
                    # Update overall consensus level
                    if action_consensus == 'low':
                        consensus_level = 'low'
                    elif action_consensus == 'medium' and consensus_level == 'high':
                        consensus_level = 'medium'
            
            # Generate consensus recommendation
            consensus_recommendation = {}
            for action_key, action_data in consensus_actions.items():
                if action_data['consensus_level'] in ['high', 'medium']:
                    consensus_recommendation[action_key] = action_data['average_value']
            
            return {
                'status': 'success',
                'successful_models': successful_models,
                'consensus_level': consensus_level,
                'consensus_actions': consensus_actions,
                'consensus_recommendation': consensus_recommendation,
                'timestamp': latest_actions.get('timestamp'),
                'models_analyzed': len(successful_models)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing action consensus: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights on process optimization based on RL recommendations"""
        try:
            if not self.recent_actions:
                return {'status': 'no_data', 'message': 'No RL action data available'}
            
            # Analyze recent trends in recommendations
            recent_data = self.recent_actions[-10:] if len(self.recent_actions) >= 10 else self.recent_actions
            
            optimization_insights = {
                'status': 'success',
                'analysis_period': f'Last {len(recent_data)} action sets',
                'key_insights': [],
                'recommended_focus_areas': [],
                'process_stability': 'unknown'
            }
            
            # Analyze most common recommendations across models
            action_frequency = {}
            for action_set in recent_data:
                for model_name in self.rl_endpoints.keys():
                    model_data = action_set.get(model_name, {})
                    if model_data.get('api_status') == 'success':
                        actions = model_data.get('recommended_actions', {})
                        for action_key, value in actions.items():
                            if isinstance(value, (int, float)) and abs(value) > 0.01:  # Significant actions only
                                if action_key not in action_frequency:
                                    action_frequency[action_key] = []
                                action_frequency[action_key].append(value)
            
            # Identify focus areas
            for action_key, values in action_frequency.items():
                if len(values) >= 3:  # At least 3 recommendations
                    avg_value = sum(values) / len(values)
                    frequency = len(values) / (len(recent_data) * 3) * 100  # Percentage across all model calls
                    
                    if frequency > 50:  # Recommended by more than 50% of model calls
                        if abs(avg_value) > 0.5:
                            priority = "high"
                        elif abs(avg_value) > 0.2:
                            priority = "medium"
                        else:
                            priority = "low"
                        
                        optimization_insights['recommended_focus_areas'].append({
                            'parameter': action_key,
                            'average_adjustment': avg_value,
                            'frequency_percent': frequency,
                            'priority': priority,
                            'direction': 'increase' if avg_value > 0 else 'decrease',
                            'magnitude': 'large' if abs(avg_value) > 0.5 else 'medium' if abs(avg_value) > 0.2 else 'small'
                        })
            
            # Sort by priority and frequency
            optimization_insights['recommended_focus_areas'].sort(
                key=lambda x: (x['priority'] == 'high', x['frequency_percent']), 
                reverse=True
            )
            
            # Generate insights
            if optimization_insights['recommended_focus_areas']:
                top_recommendation = optimization_insights['recommended_focus_areas'][0]
                optimization_insights['key_insights'].append(
                    f"Primary optimization target: {top_recommendation['parameter']} "
                    f"({top_recommendation['direction']} by {abs(top_recommendation['average_adjustment']):.3f})"
                )
                
                high_priority_count = sum(1 for area in optimization_insights['recommended_focus_areas'] if area['priority'] == 'high')
                if high_priority_count > 3:
                    optimization_insights['key_insights'].append(
                        f"Multiple high-priority areas detected ({high_priority_count}), suggesting system-wide optimization opportunity"
                    )
                elif high_priority_count == 0:
                    optimization_insights['key_insights'].append("Process appears well-optimized with only minor adjustments recommended")
            else:
                optimization_insights['key_insights'].append("No consistent optimization patterns detected - process may be well-optimized")
            
            return optimization_insights
            
        except Exception as e:
            logger.error(f"Error generating optimization insights: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _add_to_history(self, rl_record: Dict[str, Any]):
        """Add RL record to history with size management"""
        self.recent_actions.append(rl_record)
        
        # Keep only recent records
        if len(self.recent_actions) > self.max_history:
            self.recent_actions = self.recent_actions[-self.max_history:]
    
    def get_historical_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical RL action data"""
        return self.recent_actions[-limit:] if self.recent_actions else []
    
    def clear_history(self):
        """Clear historical data"""
        self.recent_actions.clear()
        logger.info("RL action history cleared")
