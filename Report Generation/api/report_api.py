from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import logging
import sys
import os
import json

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from report_generators.quality_report import QualityControlReportGenerator
from knowledge_base.knowledge_manager import KnowledgeBaseManager
from data_collectors.forecasting_collector import ForecastingCollector
from data_collectors.classification_collector import ClassificationCollector
from data_collectors.rl_collector import RLCollector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PharmaCopilot Report Generation API",
    description="AI-powered pharmaceutical manufacturing report generation with RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for components
kb_manager = None
data_collectors = {}
report_generators = {}

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global kb_manager, data_collectors, report_generators
    
    logger.info("Initializing Report Generation API components...")
    
    try:
        # Initialize knowledge base manager
        kb_manager = KnowledgeBaseManager()
        logger.info("Knowledge base manager initialized")
        
        # Initialize default documentation
        kb_manager.initialize_default_documentation()
        logger.info("Default documentation loaded")
        
        # Initialize data collectors
        data_collectors = {
            'forecasting': ForecastingCollector(),
            'classification': ClassificationCollector(),
            'rl': RLCollector()
        }
        logger.info("Data collectors initialized")
        
        # Initialize report generators
        report_generators = {
            'quality_control': QualityControlReportGenerator()
        }
        logger.info("Report generators initialized")
        
        logger.info("Report Generation API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.get("/api/reports/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check component status
        kb_status = kb_manager is not None
        collectors_status = len(data_collectors) > 0
        generators_status = len(report_generators) > 0
        
        # Get knowledge base stats if available
        kb_stats = None
        if kb_manager:
            try:
                kb_stats = kb_manager.get_collection_stats()
            except Exception as e:
                logger.warning(f"Could not get KB stats: {e}")
        
        return {
            "status": "healthy" if all([kb_status, collectors_status, generators_status]) else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "knowledge_base": "available" if kb_status else "unavailable",
                "data_collectors": "available" if collectors_status else "unavailable", 
                "report_generators": "available" if generators_status else "unavailable"
            },
            "available_generators": list(report_generators.keys()),
            "knowledge_base_stats": kb_stats
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

class ReportRequest(BaseModel):
    report_type: str
    query: str = "Generate comprehensive pharmaceutical manufacturing report"
    additional_context: Optional[Dict[str, Any]] = None

@app.post("/api/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate a specific type of report using RAG"""
    
    report_type = request.report_type
    query = request.query
    additional_context = request.additional_context
    
    # Handle common variations of report types
    report_type_mapping = {
        "quality_control": "quality_control",
        "quality": "quality_control", 
        "qc": "quality_control",
        "defect_analysis": "quality_control",
        "manufacturing_report": "quality_control",
        "pharma_report": "quality_control",
        "comprehensive": "quality_control",
        "string": "quality_control"  # Default for "string" input
    }
    
    # Map the input to a valid report type
    mapped_report_type = report_type_mapping.get(report_type.lower(), report_type)
    
    if mapped_report_type not in report_generators:
        available_types = list(report_generators.keys())
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid report type '{report_type}'",
                "mapped_type": mapped_report_type,
                "available_types": available_types,
                "suggestions": [
                    "Use 'quality_control' for comprehensive quality reports",
                    "Use 'quality' or 'qc' as shorthand for quality_control",
                    "Use 'manufacturing_report' or 'pharma_report' for general reports"
                ],
                "note": "The system currently supports quality control reports with comprehensive pharmaceutical manufacturing analysis"
            }
        )
    
    try:
        logger.info(f"Generating {mapped_report_type} report with query: {query}")
        
        generator = report_generators[mapped_report_type]
        report = await generator.generate_report(query, additional_context)
        
        return {
            "status": "success",
            "report": report,
            "generated_at": datetime.now().isoformat(),
            "report_type_used": mapped_report_type,
            "original_request_type": report_type
        }
        
    except Exception as e:
        logger.error(f"Error generating {mapped_report_type} report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating {mapped_report_type} report: {str(e)}"
        )

@app.get("/api/reports/generate")
async def generate_report_get(
    report_type: str = "quality_control",
    query: str = "Generate comprehensive pharmaceutical manufacturing report",
    additional_context: str = None
):
    """Generate a report using GET request (for compatibility)"""
    
    # Handle common variations of report types
    report_type_mapping = {
        "quality_control": "quality_control",
        "quality": "quality_control", 
        "qc": "quality_control",
        "defect_analysis": "quality_control",
        "manufacturing_report": "quality_control",
        "pharma_report": "quality_control",
        "comprehensive": "quality_control",
        "string": "quality_control"  # Default for "string" input
    }
    
    # Map the input to a valid report type
    mapped_report_type = report_type_mapping.get(report_type.lower(), report_type)
    
    if mapped_report_type not in report_generators:
        available_types = list(report_generators.keys())
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid report type '{report_type}'",
                "mapped_type": mapped_report_type,
                "available_types": available_types,
                "suggestions": [
                    "Use 'quality_control' for comprehensive quality reports",
                    "Use 'quality' or 'qc' as shorthand for quality_control",
                    "Use 'manufacturing_report' or 'pharma_report' for general reports"
                ],
                "note": "The system currently supports quality control reports with comprehensive pharmaceutical manufacturing analysis"
            }
        )
    
    try:
        logger.info(f"Generating {mapped_report_type} report with query: {query}")
        
        # Parse additional_context if provided
        parsed_context = None
        if additional_context:
            try:
                parsed_context = json.loads(additional_context)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in additional_context: {additional_context}")
                parsed_context = {"raw_context": additional_context}
        
        generator = report_generators[mapped_report_type]
        report = await generator.generate_report(query, parsed_context)
        
        return {
            "status": "success",
            "report": report,
            "generated_at": datetime.now().isoformat(),
            "report_type_used": mapped_report_type,
            "original_request_type": report_type
        }
        
    except Exception as e:
        logger.error(f"Error generating {mapped_report_type} report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating {mapped_report_type} report: {str(e)}"
        )

@app.get("/api/reports/types")
async def get_report_types():
    """Get available report types and their descriptions"""
    return {
        "available_types": list(report_generators.keys()),
        "aliases": {
            "quality_control": ["quality", "qc", "defect_analysis", "manufacturing_report", "pharma_report", "comprehensive"],
            "quality": ["quality_control", "qc", "defect_analysis"],
            "qc": ["quality_control", "quality", "defect_analysis"],
            "manufacturing_report": ["quality_control", "pharma_report", "comprehensive"],
            "pharma_report": ["quality_control", "manufacturing_report", "comprehensive"]
        },
        "descriptions": {
            "quality_control": "Comprehensive quality control and defect analysis reports with regulatory compliance",
            "quality": "Shorthand for quality_control reports",
            "qc": "Shorthand for quality_control reports",
            "manufacturing_report": "General pharmaceutical manufacturing reports",
            "pharma_report": "Pharmaceutical industry specific reports",
            "comprehensive": "Comprehensive analysis reports"
        },
        "supported_features": {
            "rag_powered": True,
            "real_time_data": True,
            "historical_analysis": True,
            "regulatory_compliance": True,
            "multiple_models": True,
            "ai_generated": True
        },
        "default_type": "quality_control",
        "note": "All report types currently map to quality_control for comprehensive pharmaceutical manufacturing analysis"
    }

@app.get("/api/knowledge/status")
async def get_knowledge_status():
    """Get knowledge base status and statistics"""
    try:
        if not kb_manager:
            return {
                "status": "unavailable",
                "error": "Knowledge base manager not initialized"
            }
            
        stats = kb_manager.get_collection_stats()
        
        return {
            "status": "available",
            "collections": stats,
            "last_updated": datetime.now().isoformat(),
            "features": {
                "vector_search": True,
                "embeddings": True,
                "historical_data": True,
                "documentation": True
            }
        }
    except Exception as e:
        logger.error(f"Error getting knowledge status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting knowledge status: {str(e)}")

@app.post("/api/knowledge/add-documentation")
async def add_documentation(
    doc_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Add documentation to the knowledge base"""
    try:
        if not kb_manager:
            raise HTTPException(status_code=503, detail="Knowledge base not available")
            
        success = kb_manager.add_documentation(
            doc_type=doc_type,
            content=content,
            metadata=metadata or {}
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Documentation of type '{doc_type}' added successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to add documentation to knowledge base"
            }
            
    except Exception as e:
        logger.error(f"Error adding documentation: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding documentation: {str(e)}")

@app.post("/api/data/collect")
async def collect_current_data(background_tasks: BackgroundTasks):
    """Manually trigger data collection from all sources"""
    try:
        # Run data collection in background
        background_tasks.add_task(collect_and_store_data)
        
        return {
            "status": "initiated",
            "message": "Data collection started in background",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error initiating data collection: {e}")
        raise HTTPException(status_code=500, detail=f"Error initiating data collection: {str(e)}")

async def collect_and_store_data():
    """Background task to collect and store data"""
    try:
        # Collect from all sources
        tasks = []
        
        for collector_name, collector in data_collectors.items():
            if collector:
                tasks.append(collector.collect_data())
                
        # Run all collections concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Store results in knowledge base
        if kb_manager:
            for i, (collector_name, result) in enumerate(zip(data_collectors.keys(), results)):
                if not isinstance(result, Exception) and result:
                    kb_manager.add_historical_data(collector_name, result)
                    
        logger.info(f"Background data collection completed, processed {len(results)} sources")
        
    except Exception as e:
        logger.error(f"Error in background data collection: {e}")

@app.get("/api/data/summaries")
async def get_data_summaries(hours: int = 6):
    """Get summarized data from recent collections"""
    try:
        summaries = {}
        
        # Get summaries from each collector
        for collector_name, collector in data_collectors.items():
            if collector:
                try:
                    if collector_name == 'forecasting':
                        summary = collector.get_forecast_summary(hours)
                    elif collector_name == 'classification':
                        summary = collector.get_classification_summary(hours)
                    elif collector_name == 'rl':
                        summary = collector.get_rl_summary(hours)
                    else:
                        summary = {"status": "unknown_collector"}
                        
                    summaries[collector_name] = summary
                    
                except Exception as e:
                    logger.error(f"Error getting {collector_name} summary: {e}")
                    summaries[collector_name] = {"status": "error", "message": str(e)}
        
        return {
            "status": "success",
            "summaries": summaries,
            "hours_analyzed": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting data summaries: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting data summaries: {str(e)}")

@app.get("/api/reports/quality/metrics")
async def get_quality_metrics():
    """Get current quality metrics summary"""
    try:
        if 'quality_control' not in report_generators:
            raise HTTPException(status_code=503, detail="Quality control generator not available")
            
        generator = report_generators['quality_control']
        metrics = generator.get_quality_metrics_summary()
        
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting quality metrics: {str(e)}")

@app.post("/api/knowledge/search")
async def search_knowledge_base(
    query: str,
    collection: str = "historical_data",
    max_results: int = 10
):
    """Search the knowledge base for relevant information"""
    try:
        if not kb_manager:
            raise HTTPException(status_code=503, detail="Knowledge base not available")
            
        results = kb_manager.search_relevant_context(
            query=query,
            collection=collection,
            n_results=max_results
        )
        
        return {
            "status": "success",
            "query": query,
            "collection": collection,
            "results": results,
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching knowledge base: {str(e)}")

@app.post("/api/knowledge/cleanup")
async def cleanup_knowledge_base(days_to_keep: int = 30):
    """Clean up old data from knowledge base"""
    try:
        if not kb_manager:
            raise HTTPException(status_code=503, detail="Knowledge base not available")
            
        kb_manager.cleanup_old_embeddings(days_to_keep)
        
        return {
            "status": "success",
            "message": f"Cleaned up data older than {days_to_keep} days",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up knowledge base: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist",
        "timestamp": datetime.now().isoformat()
    }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "error": "Unexpected error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 