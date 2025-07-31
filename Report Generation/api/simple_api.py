"""
Simplified FastAPI for PharmaCopilot Report Generation
Optimized for speed and efficiency
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Disable chromadb telemetry to prevent posthog errors
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False'

# Suppress noisy loggers
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)
logging.getLogger('tensorflow').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PharmaCopilot Report Generation API",
    description="Simplified pharmaceutical manufacturing report generation",
    version="2.0.0",
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

# Global report generator
report_generator = None

@app.on_event("startup")
async def startup_event():
    """Initialize proper report generator on startup"""
    global report_generator
    
    try:
        logger.info("Initializing proper report generator with LLM integration...")
        from report_generators.quality_report import QualityControlReportGenerator
        report_generator = QualityControlReportGenerator()
        logger.info("Report generator initialized successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Fallback to simple generator if needed
        try:
            from report_generators.simple_generator import SimpleReportGenerator
            report_generator = SimpleReportGenerator()
            logger.info("Fallback to simple generator")
        except Exception as fallback_error:
            logger.error(f"Fallback generator failed: {fallback_error}")
            report_generator = None

class ReportRequest(BaseModel):
    report_type: str = "quality_control"
    query: str = "Generate pharmaceutical manufacturing report"
    additional_context: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "PharmaCopilot Report Generation API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/api/reports/health",
            "generate": "/api/reports/generate",
            "types": "/api/reports/types",
            "docs": "/docs"
        }
    }

@app.get("/api/reports/health")
async def health_check():
    """Simplified health check"""
    try:
        generator_status = report_generator is not None
        
        return {
            "status": "healthy" if generator_status else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "report_generator": "available" if generator_status else "unavailable"
            },
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate a report using proper generator"""
    
    if not report_generator:
        raise HTTPException(status_code=503, detail="Report generator not available")
    
    try:
        logger.info(f"Generating {request.report_type} report")
        
        # Call the report generator with correct parameters
        report = await report_generator.generate_report(
            query=request.query,
            additional_context=request.additional_context
        )
        
        return {
            "status": "success",
            "report": report,
            "generated_at": datetime.now().isoformat(),
            "report_type": request.report_type
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/api/reports/generate")
async def generate_report_get(
    report_type: str = "quality_control",
    query: str = "Generate pharmaceutical manufacturing report"
):
    """Generate a report using GET request for easy testing"""
    
    request = ReportRequest(
        report_type=report_type,
        query=query
    )
    
    return await generate_report(request)

@app.post("/api/reports/download-pdf")
async def download_report_pdf(request: ReportRequest):
    """
    Generate and download a report as PDF
    """
    try:
        # First generate the report
        report_response = await generate_report(request)
        
        if report_response.get("status") != "success":
            raise HTTPException(status_code=500, detail="Failed to generate report")
        
        # Import PDF generator
        try:
            from utils.pdf_generator import generate_report_pdf
        except ImportError as e:
            logger.error(f"Failed to import PDF generator: {e}")
            raise HTTPException(status_code=500, detail="PDF generation not available")
        
        # Extract report data
        report_data = report_response.get("report", {})
        
        # Generate PDF
        pdf_content = generate_report_pdf(report_data)
        
        # Create filename
        report_id = report_data.get('report_id', 'report')
        filename = f"{report_id}.pdf"
        
        # Return PDF response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@app.get("/api/reports/download-pdf")
async def download_report_pdf_get(
    report_type: str = "quality_control",
    query: str = "Generate pharmaceutical manufacturing report"
):
    """
    Generate and download a report as PDF using GET request
    """
    request = ReportRequest(
        report_type=report_type,
        query=query
    )
    
    return await download_report_pdf(request)

@app.get("/api/reports/types")
async def get_report_types():
    """Get available report types"""
    return {
        "available_types": [
            "quality_control", 
            "batch_record", 
            "deviation", 
            "oee", 
            "compliance", 
            "excellence",
            "manufacturing"
        ],
        "default_type": "quality_control",
        "descriptions": {
            "quality_control": "Quality control and defect analysis reports",
            "batch_record": "Batch record analysis and performance review",
            "deviation": "Process deviation investigation and analysis", 
            "oee": "Overall Equipment Effectiveness performance summary",
            "compliance": "Regulatory compliance reports",
            "excellence": "Manufacturing excellence and optimization reports",
            "manufacturing": "General manufacturing performance reports"
        },
        "aliases": {
            "quality": "quality_control",
            "qc": "quality_control",
            "batch": "batch_record",
            "process": "deviation",
            "regulatory": "compliance"
        }
    }

# Simple error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist",
            "available_endpoints": ["/", "/docs", "/api/reports/health", "/api/reports/generate"]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
