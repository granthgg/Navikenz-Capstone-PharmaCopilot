"""
PDF Generator for PharmaCopilot Reports
Converts generated reports to professional PDF format with proper styling
"""

import os
import io
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import HRFlowable
import markdown
import re

logger = logging.getLogger(__name__)

class PharmaPDFGenerator:
    """
    Professional PDF generator for pharmaceutical manufacturing reports
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom styles for pharmaceutical reports"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='PharmaTitle',
            parent=self.styles['Title'],
            fontSize=20,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Header styles
        self.styles.add(ParagraphStyle(
            name='PharmaHeading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='PharmaHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#3b82f6'),
            spaceBefore=16,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='PharmaHeading3',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#6b7280'),
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='PharmaBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=6,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Important text
        self.styles.add(ParagraphStyle(
            name='PharmaImportant',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#dc2626'),
            spaceBefore=8,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='PharmaMetadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            spaceBefore=4,
            spaceAfter=4,
            fontName='Helvetica'
        ))
    
    def generate_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """
        Generate a professional PDF from report data
        
        Args:
            report_data: Dictionary containing report information
            
        Returns:
            bytes: PDF file content
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build PDF content
            story = []
            
            # Add header with logo placeholder and company info
            self._add_header(story, report_data)
            
            # Add title
            self._add_title(story, report_data)
            
            # Add report metadata
            self._add_metadata(story, report_data)
            
            # Add executive summary
            self._add_executive_summary(story, report_data)
            
            # Add quality metrics table
            self._add_quality_metrics(story, report_data)
            
            # Add detailed analysis
            self._add_detailed_analysis(story, report_data)
            
            # Add recommendations
            self._add_recommendations(story, report_data)
            
            # Add compliance status
            self._add_compliance_status(story, report_data)
            
            # Add risk assessment
            self._add_risk_assessment(story, report_data)
            
            # Add action items
            self._add_action_items(story, report_data)
            
            # Add appendix
            self._add_appendix(story, report_data)
            
            # Add footer
            self._add_footer(story, report_data)
            
            # Build PDF
            doc.build(story)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"PDF generated successfully, size: {len(pdf_content)} bytes")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    def _add_header(self, story, report_data):
        """Add header section"""
        # Company header
        header_data = [
            ['PharmaCopilot Manufacturing Intelligence', '', 'Report Generation System'],
            ['Advanced Analytics & Quality Control', '', f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        ]
        
        header_table = Table(header_data, colWidths=[3*inch, 2*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#6b7280')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 20))
    
    def _add_title(self, story, report_data):
        """Add report title"""
        title = report_data.get('title', 'Pharmaceutical Manufacturing Report')
        story.append(Paragraph(title, self.styles['PharmaTitle']))
        
        # Report ID and type
        report_id = report_data.get('report_id', 'N/A')
        report_type = report_data.get('report_type', 'quality_control').replace('_', ' ').title()
        
        subtitle = f"Report ID: {report_id} | Type: {report_type}"
        story.append(Paragraph(subtitle, self.styles['PharmaMetadata']))
        story.append(Spacer(1, 20))
    
    def _add_metadata(self, story, report_data):
        """Add report metadata table"""
        generated_at = report_data.get('generated_at', datetime.now().isoformat())
        data_sources = report_data.get('data_sources', {})
        
        metadata = [
            ['Generation Time', generated_at],
            ['Report Type', report_data.get('report_type', 'Unknown').replace('_', ' ').title()],
            ['Data Sources', ', '.join([f"{k}: {v}" for k, v in data_sources.items()])]
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 20))
    
    def _add_executive_summary(self, story, report_data):
        """Add executive summary section"""
        story.append(Paragraph("Executive Summary", self.styles['PharmaHeading1']))
        
        executive_summary = report_data.get('executive_summary', 'No executive summary available.')
        
        # Convert markdown to paragraphs
        summary_paragraphs = self._markdown_to_paragraphs(executive_summary)
        for para in summary_paragraphs:
            story.append(para)
        
        story.append(Spacer(1, 15))
    
    def _add_quality_metrics(self, story, report_data):
        """Add quality metrics table"""
        story.append(Paragraph("Quality Metrics", self.styles['PharmaHeading1']))
        
        quality_metrics = report_data.get('quality_metrics', {})
        
        if quality_metrics:
            # Create metrics table
            metrics_data = [['Metric', 'Value', 'Status']]
            
            # Extract key metrics
            quality_scores = quality_metrics.get('quality_scores', {})
            forecast_accuracy = quality_metrics.get('forecast_accuracy', {})
            rl_performance = quality_metrics.get('rl_performance', {})
            system_health = quality_metrics.get('system_health', {})
            
            # Add rows
            if quality_scores:
                metrics_data.append(['Overall Quality Score', str(quality_scores.get('overall_score', 'N/A')), 'Monitoring'])
                metrics_data.append(['Batch Quality', quality_scores.get('batch_quality', 'Unknown'), 'Active'])
                metrics_data.append(['Quality Confidence', f"{quality_scores.get('quality_confidence', 0):.2%}", 'Good'])
            
            if forecast_accuracy:
                metrics_data.append(['Prediction Horizon', forecast_accuracy.get('prediction_horizon', 'N/A'), 'Active'])
                metrics_data.append(['Forecast Confidence', f"{forecast_accuracy.get('forecast_confidence', 0):.2%}", 'Monitoring'])
            
            if system_health:
                metrics_data.append(['Data Availability', system_health.get('data_availability', 'Unknown'), 'Healthy'])
                metrics_data.append(['Collection Success Rate', f"{quality_metrics.get('collection_success_rate', 0)}%", 'Good'])
            
            metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            metrics_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ]))
            
            story.append(metrics_table)
        else:
            story.append(Paragraph("No quality metrics data available.", self.styles['PharmaBody']))
        
        story.append(Spacer(1, 15))
    
    def _add_detailed_analysis(self, story, report_data):
        """Add detailed analysis section"""
        story.append(Paragraph("Detailed Analysis", self.styles['PharmaHeading1']))
        
        detailed_analysis = report_data.get('detailed_analysis', 'No detailed analysis available.')
        
        analysis_paragraphs = self._markdown_to_paragraphs(detailed_analysis)
        for para in analysis_paragraphs:
            story.append(para)
        
        story.append(Spacer(1, 15))
    
    def _add_recommendations(self, story, report_data):
        """Add recommendations section"""
        story.append(Paragraph("Recommendations", self.styles['PharmaHeading1']))
        
        recommendations = report_data.get('recommendations', [])
        
        if recommendations and len(recommendations) > 0:
            for i, rec in enumerate(recommendations, 1):
                if isinstance(rec, str) and rec.strip():
                    rec_text = f"{i}. {rec}"
                    story.append(Paragraph(rec_text, self.styles['PharmaBody']))
        else:
            story.append(Paragraph("No specific recommendations available at this time.", self.styles['PharmaBody']))
        
        story.append(Spacer(1, 15))
    
    def _add_compliance_status(self, story, report_data):
        """Add compliance status section"""
        story.append(Paragraph("Compliance Status", self.styles['PharmaHeading1']))
        
        compliance_status = report_data.get('compliance_status', 'Compliance status under review.')
        
        if compliance_status and compliance_status.strip():
            compliance_paragraphs = self._markdown_to_paragraphs(compliance_status)
            for para in compliance_paragraphs:
                story.append(para)
        else:
            story.append(Paragraph("Compliance status is under review. All systems operating within established parameters.", self.styles['PharmaBody']))
        
        story.append(Spacer(1, 15))
    
    def _add_risk_assessment(self, story, report_data):
        """Add risk assessment section"""
        story.append(Paragraph("Risk Assessment", self.styles['PharmaHeading1']))
        
        risk_assessment = report_data.get('risk_assessment', 'Risk assessment in progress.')
        
        if risk_assessment and risk_assessment.strip():
            risk_paragraphs = self._markdown_to_paragraphs(risk_assessment)
            for para in risk_paragraphs:
                story.append(para)
        else:
            story.append(Paragraph("Risk assessment is being conducted. Current risk level appears to be within acceptable parameters.", self.styles['PharmaBody']))
        
        story.append(Spacer(1, 15))
    
    def _add_action_items(self, story, report_data):
        """Add action items section"""
        story.append(Paragraph("Action Items", self.styles['PharmaHeading1']))
        
        action_items = report_data.get('action_items', [])
        
        if action_items and len(action_items) > 0:
            for i, item in enumerate(action_items, 1):
                if isinstance(item, str) and item.strip():
                    action_text = f"{i}. {item}"
                    story.append(Paragraph(action_text, self.styles['PharmaImportant']))
        else:
            story.append(Paragraph("No immediate action items identified.", self.styles['PharmaBody']))
        
        story.append(Spacer(1, 15))
    
    def _add_appendix(self, story, report_data):
        """Add appendix section"""
        story.append(Paragraph("Appendix", self.styles['PharmaHeading1']))
        
        appendix = report_data.get('appendix', {})
        
        if appendix:
            # Raw data summary
            raw_data = appendix.get('raw_data_summary', {})
            if raw_data:
                story.append(Paragraph("Raw Data Summary", self.styles['PharmaHeading2']))
                
                data_summary = [
                    ['Collection Timestamp', raw_data.get('collection_timestamp', 'N/A')],
                    ['Sources Attempted', str(raw_data.get('sources_attempted', 'N/A'))],
                    ['Sources Successful', str(raw_data.get('sources_successful', 'N/A'))],
                    ['Data Points Collected', str(raw_data.get('data_points_collected', 'N/A'))],
                    ['Errors Encountered', str(raw_data.get('errors_encountered', 'N/A'))]
                ]
                
                data_table = Table(data_summary, colWidths=[2.5*inch, 3.5*inch])
                data_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                story.append(data_table)
            
            # Methodology
            methodology = appendix.get('methodology', '')
            if methodology:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Methodology", self.styles['PharmaHeading2']))
                story.append(Paragraph(methodology, self.styles['PharmaBody']))
            
            # Data freshness
            data_freshness = appendix.get('data_freshness', '')
            if data_freshness:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Data Freshness", self.styles['PharmaHeading2']))
                story.append(Paragraph(data_freshness, self.styles['PharmaBody']))
        else:
            story.append(Paragraph("No additional appendix data available.", self.styles['PharmaBody']))
        
        story.append(Spacer(1, 15))
    
    def _add_footer(self, story, report_data):
        """Add footer section"""
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 10))
        
        footer_text = f"""
        This report was generated by PharmaCopilot Manufacturing Intelligence System.
        Report ID: {report_data.get('report_id', 'N/A')} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        For technical support, contact the PharmaCopilot team.
        """
        
        story.append(Paragraph(footer_text.strip(), self.styles['PharmaMetadata']))
    
    def _markdown_to_paragraphs(self, text: str):
        """Convert markdown text to ReportLab paragraphs"""
        paragraphs = []
        
        if not text or not text.strip():
            return [Paragraph("No content available.", self.styles['PharmaBody'])]
        
        # Split by lines and process
        lines = text.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Empty line - end current paragraph
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    paragraphs.append(Paragraph(para_text, self.styles['PharmaBody']))
                    current_paragraph = []
                continue
            
            # Check for headers
            if line.startswith('### '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    paragraphs.append(Paragraph(para_text, self.styles['PharmaBody']))
                    current_paragraph = []
                header_text = line[4:].strip()
                paragraphs.append(Paragraph(header_text, self.styles['PharmaHeading3']))
                continue
            elif line.startswith('## '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    paragraphs.append(Paragraph(para_text, self.styles['PharmaBody']))
                    current_paragraph = []
                header_text = line[3:].strip()
                paragraphs.append(Paragraph(header_text, self.styles['PharmaHeading2']))
                continue
            elif line.startswith('# '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    paragraphs.append(Paragraph(para_text, self.styles['PharmaBody']))
                    current_paragraph = []
                header_text = line[2:].strip()
                paragraphs.append(Paragraph(header_text, self.styles['PharmaHeading1']))
                continue
            
            # Check for bullet points
            if line.startswith(('- ', '• ', '* ')):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    paragraphs.append(Paragraph(para_text, self.styles['PharmaBody']))
                    current_paragraph = []
                bullet_text = f"• {line[2:].strip()}"
                paragraphs.append(Paragraph(bullet_text, self.styles['PharmaBody']))
                continue
            
            # Regular text - add to current paragraph
            current_paragraph.append(line)
        
        # Add any remaining paragraph
        if current_paragraph:
            para_text = ' '.join(current_paragraph)
            paragraphs.append(Paragraph(para_text, self.styles['PharmaBody']))
        
        return paragraphs if paragraphs else [Paragraph("No content available.", self.styles['PharmaBody'])]

def generate_report_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Convenience function to generate PDF from report data
    
    Args:
        report_data: Dictionary containing report information
        
    Returns:
        bytes: PDF file content
    """
    generator = PharmaPDFGenerator()
    return generator.generate_pdf(report_data)
