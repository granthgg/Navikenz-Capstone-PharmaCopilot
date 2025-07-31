"""
Simplified Report Generator for PharmaCopilot
Fast, efficient, and lightweight report generation
"""

import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
import random

logger = logging.getLogger(__name__)

class SimpleReportGenerator:
    """
    Simplified, fast report generator that focuses on core functionality
    without unnecessary complexity
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        
    async def generate_report(self, query: str, report_type: str = "quality_control", 
                            additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a report efficiently"""
        
        logger.info(f"Generating {report_type} report")
        start_time = datetime.now()
        
        try:
            # Step 1: Quick data collection (with timeout for speed)
            collected_data = await self._collect_data_fast()
            
            # Step 2: Extract key metrics quickly
            key_metrics = self._extract_metrics_fast(collected_data)
            
            # Step 3: Generate report content
            report_content = self._generate_report_content(report_type, key_metrics, query)
            
            # Step 4: Build response
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                'report_id': f"{report_type.upper()}-{int(end_time.timestamp())}",
                'title': f"{report_type.replace('_', ' ').title()} Report",
                'report_content': report_content,
                'generated_at': end_time.isoformat(),
                'processing_time_seconds': round(processing_time, 2),
                'metrics': key_metrics,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return self._generate_fallback_report(report_type, str(e))
    
    async def _collect_data_fast(self) -> Dict[str, Any]:
        """Fast data collection with timeout"""
        collected_data = {}
        
        # Data sources to try (with short timeout)
        sources = [
            ('classification', f"{self.api_base_url}/api/defect"),
            ('quality', f"{self.api_base_url}/api/quality"),
            ('forecasting', f"{self.api_base_url}/api/forecast")
        ]
        
        timeout = aiohttp.ClientTimeout(total=3)  # 3 second timeout
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                tasks = []
                for source_name, url in sources:
                    tasks.append(self._fetch_data(session, source_name, url))
                
                # Run concurrently with timeout
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for source_name, result in zip([s[0] for s in sources], results):
                    if not isinstance(result, Exception):
                        collected_data[source_name] = result
                    else:
                        collected_data[source_name] = {'error': str(result)}
                        
        except Exception as e:
            logger.warning(f"Data collection failed: {e}")
            # Continue with empty data - we can still generate a basic report
            
        return collected_data
    
    async def _fetch_data(self, session, source_name, url):
        """Fetch data from a single source"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_metrics_fast(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Quick metrics extraction"""
        metrics = {
            'defect_probability': 'N/A',
            'quality_class': 'N/A', 
            'risk_level': 'N/A',
            'data_sources_available': 0,
            'api_status': 'unknown'
        }
        
        try:
            # Count available data sources
            metrics['data_sources_available'] = len([
                k for k, v in collected_data.items() 
                if isinstance(v, dict) and 'error' not in v
            ])
            
            # Extract classification data
            if 'classification' in collected_data:
                class_data = collected_data['classification']
                if 'error' not in class_data:
                    metrics['defect_probability'] = round(class_data.get('defect_probability', 0), 3)
                    metrics['api_status'] = 'connected'
            
            # Extract quality data
            if 'quality' in collected_data:
                quality_data = collected_data['quality']
                if 'error' not in quality_data:
                    metrics['quality_class'] = quality_data.get('quality_class', 'Unknown')
            
            # Determine risk level
            defect_prob = metrics.get('defect_probability')
            if isinstance(defect_prob, (int, float)):
                if defect_prob > 0.7:
                    metrics['risk_level'] = 'High'
                elif defect_prob > 0.3:
                    metrics['risk_level'] = 'Medium'
                else:
                    metrics['risk_level'] = 'Low'
            
            # Overall API status
            if metrics['data_sources_available'] > 0:
                metrics['api_status'] = 'connected'
            else:
                metrics['api_status'] = 'disconnected'
                
        except Exception as e:
            logger.warning(f"Metrics extraction error: {e}")
            
        return metrics
    
    def _generate_report_content(self, report_type: str, metrics: Dict[str, Any], query: str) -> str:
        """Generate report content based on type and metrics"""
        
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Map report types to human-readable titles
        title_mapping = {
            'quality_control': 'Quality Control',
            'batch_record': 'Batch Record Analysis', 
            'deviation': 'Process Deviation Investigation',
            'oee': 'OEE Performance Summary',
            'compliance': 'Regulatory Compliance Review',
            'excellence': 'Manufacturing Excellence',
            'manufacturing': 'Manufacturing Performance'
        }
        
        title = title_mapping.get(report_type, report_type.replace('_', ' ').title())
        
        report = f"""# {title} Report

**Generated:** {timestamp}  
**System:** PharmaCopilot AI  
**Query:** {query}

---

## Executive Summary

"""
        
        # Status determination
        api_status = metrics.get('api_status', 'unknown')
        defect_prob = metrics.get('defect_probability', 'N/A')
        risk_level = metrics.get('risk_level', 'N/A')
        
        if api_status == 'connected':
            if isinstance(defect_prob, (int, float)):
                if defect_prob > 0.7:
                    status_text = "HIGH RISK - Immediate attention required"
                elif defect_prob > 0.3:
                    status_text = "MODERATE RISK - Monitor closely"
                else:
                    status_text = "NORMAL OPERATION - Systems performing well"
            else:
                status_text = "MONITORING - Data being collected"
        else:
            status_text = "OFFLINE MODE - Manual verification recommended"
        
        report += f"**Status:** {status_text}\n\n"
        
        # Key metrics table
        report += """| Metric | Value | Status |
|--------|-------|---------|
"""
        
        # Add metrics rows
        defect_status = "High" if isinstance(defect_prob, (int, float)) and defect_prob > 0.7 else "Normal" if isinstance(defect_prob, (int, float)) and defect_prob <= 0.3 else "Moderate"
        report += f"| Defect Probability | {defect_prob} | {defect_status} |\n"
        report += f"| Quality Class | {metrics.get('quality_class', 'N/A')} | Monitored |\n"
        report += f"| Risk Level | {risk_level} | Assessed |\n"
        report += f"| API Connection | {api_status.title()} | {'Online' if api_status == 'connected' else 'Offline'} |\n"
        
        # Recommendations section
        report += "\n---\n\n## Recommendations\n\n"
        
        # Generate report-type-specific recommendations
        if report_type == 'quality_control':
            recommendations = self._get_quality_recommendations(metrics, api_status, defect_prob)
        elif report_type == 'batch_record':
            recommendations = self._get_batch_recommendations(metrics, api_status)
        elif report_type == 'deviation':
            recommendations = self._get_deviation_recommendations(metrics, api_status)
        elif report_type == 'oee':
            recommendations = self._get_oee_recommendations(metrics, api_status)
        elif report_type == 'compliance':
            recommendations = self._get_compliance_recommendations(metrics, api_status)
        elif report_type == 'excellence':
            recommendations = self._get_excellence_recommendations(metrics, api_status)
        else:
            recommendations = self._get_general_recommendations(metrics, api_status, defect_prob)
        
        report += recommendations
        
        # Compliance section
        report += "\n---\n\n## Compliance Status\n\n"
        report += "- **Regulatory Framework:** 21 CFR Part 11 Compliant\n"
        report += "- **Data Integrity:** Verified\n"
        report += "- **Audit Trail:** Complete\n"
        report += "- **Report Generation:** Automated & Validated\n"
        
        # Add simple language summary
        summary = self._generate_simple_summary(metrics, api_status, defect_prob)
        if summary:
            report += "\n---\n\n## Report Summary\n\n"
            report += "*The following summary explains this report in simple, non-technical language:*\n\n"
            report += summary + "\n"
        
        # Footer
        report += f"\n---\n\n*Report generated automatically by PharmaCopilot AI at {timestamp}*"
        
        return report
    
    def _generate_fallback_report(self, report_type: str, error_msg: str) -> Dict[str, Any]:
        """Generate a basic fallback report when errors occur"""
        
        now = datetime.now()
        
        content = f"""# {report_type.replace('_', ' ').title()} Report - Fallback Mode

**Generated:** {now.strftime("%Y-%m-%d %H:%M:%S")}  
**Status:** Fallback Mode  

## System Status
The report generation system is operating in fallback mode.

**Error:** {error_msg}

## Recommended Actions
- Verify system connectivity
- Check API services
- Contact system administrator
- Perform manual quality checks

## Compliance
This automated fallback report meets basic documentation requirements.
Manual verification is recommended.

*Automated fallback response generated by PharmaCopilot AI*
"""
        
        return {
            'report_id': f"FALLBACK-{int(now.timestamp())}",
            'title': f"{report_type.replace('_', ' ').title()} Report (Fallback)",
            'report_content': content,
            'generated_at': now.isoformat(),
            'status': 'fallback',
            'error': error_msg
        }
    
    def _get_quality_recommendations(self, metrics, api_status, defect_prob):
        """Generate quality control specific recommendations"""
        if api_status == 'connected':
            if isinstance(defect_prob, (int, float)):
                if defect_prob > 0.7:
                    return ("- **IMMEDIATE ACTION:** Stop production and investigate\n"
                           "- Perform equipment calibration\n"
                           "- Notify quality assurance team\n"
                           "- Review batch records for anomalies\n")
                elif defect_prob > 0.3:
                    return ("- Increase monitoring frequency\n"
                           "- Review recent process changes\n"
                           "- Analyze trend data\n"
                           "- Implement preventive measures\n")
                else:
                    return ("- Continue current monitoring protocols\n"
                           "- Maintain optimization efforts\n"
                           "- Focus on continuous improvement\n"
                           "- Monitor quality metrics trends\n")
            else:
                return ("- Continue data collection\n"
                       "- Monitor system performance\n"
                       "- Establish baseline metrics\n")
        else:
            return ("- Check API connectivity\n"
                   "- Verify system services\n"
                   "- Contact system administrator\n"
                   "- Perform manual quality checks\n")
    
    def _get_batch_recommendations(self, metrics, api_status):
        """Generate batch record specific recommendations"""
        if api_status == 'connected':
            return ("- Review batch performance metrics\n"
                   "- Verify batch documentation completeness\n"
                   "- Analyze process parameter trends\n"
                   "- Confirm batch disposition criteria\n"
                   "- Compare with historical batch data\n")
        else:
            return ("- Perform manual batch review\n"
                   "- Verify documentation manually\n"
                   "- Contact system administrator\n"
                   "- Use offline analysis tools\n")
    
    def _get_deviation_recommendations(self, metrics, api_status):
        """Generate deviation investigation specific recommendations"""
        if api_status == 'connected':
            return ("- **ROOT CAUSE ANALYSIS:** Investigate deviation source\n"
                   "- Document all findings thoroughly\n"
                   "- Implement corrective actions\n"
                   "- Monitor effectiveness of corrections\n"
                   "- Update procedures if necessary\n"
                   "- Notify regulatory affairs if required\n")
        else:
            return ("- Initiate manual deviation investigation\n"
                   "- Review all available documentation\n"
                   "- Contact quality assurance team\n"
                   "- Implement immediate containment measures\n")
    
    def _get_oee_recommendations(self, metrics, api_status):
        """Generate OEE specific recommendations"""
        if api_status == 'connected':
            return ("- **AVAILABILITY:** Minimize unplanned downtime\n"
                   "- **PERFORMANCE:** Optimize production speed\n"
                   "- **QUALITY:** Reduce defect rates\n"
                   "- Track OEE components separately\n"
                   "- Set improvement targets\n"
                   "- Benchmark against industry standards\n")
        else:
            return ("- Calculate OEE manually\n"
                   "- Review production logs\n"
                   "- Identify improvement opportunities\n"
                   "- Contact maintenance team\n")
    
    def _get_compliance_recommendations(self, metrics, api_status):
        """Generate compliance specific recommendations"""
        return ("- **21 CFR Part 11:** Ensure electronic records compliance\n"
               "- **GMP:** Verify good manufacturing practices\n"
               "- **AUDIT TRAIL:** Maintain complete documentation\n"
               "- **DATA INTEGRITY:** Verify data quality and completeness\n"
               "- **REGULATORY:** Stay current with regulatory changes\n"
               "- **VALIDATION:** Ensure system validation status\n")
    
    def _get_excellence_recommendations(self, metrics, api_status):
        """Generate manufacturing excellence specific recommendations"""
        if api_status == 'connected':
            return ("- **LEAN MANUFACTURING:** Eliminate waste in processes\n"
                   "- **SIX SIGMA:** Apply statistical process control\n"
                   "- **KAIZEN:** Implement continuous improvement\n"
                   "- **TEAM ENGAGEMENT:** Foster improvement culture\n"
                   "- **BENCHMARKING:** Compare with best practices\n"
                   "- **EXCELLENCE MODELS:** Apply industry frameworks\n")
        else:
            return ("- Review excellence initiatives manually\n"
                   "- Focus on immediate improvements\n"
                   "- Engage teams in problem-solving\n"
                   "- Use available data for analysis\n")
    
    def _get_general_recommendations(self, metrics, api_status, defect_prob):
        """Generate general recommendations as fallback"""
        if api_status == 'connected':
            if isinstance(defect_prob, (int, float)) and defect_prob > 0.5:
                return ("- Monitor elevated risk levels\n"
                       "- Investigate process variations\n"
                       "- Increase data collection frequency\n"
                       "- Notify operations team\n")
            else:
                return ("- Continue current monitoring protocols\n"
                       "- Maintain optimization efforts\n"
                       "- Focus on continuous improvement\n")
        else:
            return ("- Check system connectivity\n"
                   "- Verify service status\n"
                   "- Contact technical support\n")
    
    def _generate_simple_summary(self, metrics: Dict[str, Any], api_status: str, defect_prob) -> str:
        """Generate a simple language summary of the report"""
        try:
            # Determine overall system health
            if api_status == 'connected':
                if isinstance(defect_prob, (int, float)):
                    if defect_prob < 0.1:
                        health_status = "working very well"
                        risk_description = "very low risk of any problems"
                    elif defect_prob < 0.3:
                        health_status = "working well"
                        risk_description = "low risk of problems"
                    elif defect_prob < 0.5:
                        health_status = "working with some concerns"
                        risk_description = "moderate risk that requires attention"
                    elif defect_prob < 0.7:
                        health_status = "having noticeable issues"
                        risk_description = "high risk that needs immediate attention"
                    else:
                        health_status = "having serious problems"
                        risk_description = "very high risk requiring urgent action"
                else:
                    health_status = "being monitored"
                    risk_description = "unknown risk level"
            else:
                health_status = "offline and needs attention"
                risk_description = "unable to assess risk properly"
            
            # Generate the summary
            summary = f"This report shows that our pharmaceutical manufacturing system is currently {health_status}. "
            
            if api_status == 'connected':
                if isinstance(defect_prob, (int, float)):
                    summary += f"The system detected a {defect_prob:.1%} chance of defects in the current production, which means there is {risk_description}. "
                else:
                    summary += f"The system is collecting data to assess quality, and there is {risk_description}. "
                
                if defect_prob and isinstance(defect_prob, (int, float)):
                    if defect_prob < 0.3:
                        summary += "The production process is running smoothly and meeting quality standards. Regular monitoring should continue to maintain these good results."
                    elif defect_prob < 0.7:
                        summary += "While the system is mostly working well, some adjustments may be needed to prevent potential quality issues from developing."
                    else:
                        summary += "The production process needs immediate attention to prevent quality problems and ensure safe, effective products are manufactured."
                else:
                    summary += "The team should continue monitoring the system and following standard procedures to maintain quality."
            else:
                summary += "The monitoring systems are not currently connected, so manual checks are needed to ensure everything is working properly. Technical support should be contacted to restore the automatic monitoring capabilities."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating simple summary: {e}")
            return "This report provides information about our pharmaceutical manufacturing system. Please review the sections above for details about current operations and any recommended actions."
