import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LoadingSpinner, { ProgressBar } from './LoadingSpinner';

// Function to format report content from Markdown to HTML
const formatReportContent = (content) => {
  if (!content) return '';
  
  let formatted = content
    // Headers
    .replace(/^# (.*$)/gm, '<h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0;">$1</h1>')
    .replace(/^## (.*$)/gm, '<h2 style="color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 0.3rem; margin: 1.2rem 0 0.8rem 0;">$1</h2>')
    .replace(/^### (.*$)/gm, '<h3 style="color: #34495e; margin: 1rem 0 0.6rem 0;">$1</h3>')
    
    // Bold and emphasis
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #2c3e50;">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    
    // Code blocks
    .replace(/```([\s\S]*?)```/g, '<div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 1rem; margin: 0.5rem 0; font-family: monospace; font-size: 0.8rem; overflow-x: auto;">$1</div>')
    .replace(/`(.*?)`/g, '<code style="background: #f8f9fa; padding: 0.2rem 0.4rem; border-radius: 3px; font-family: monospace; color: #e74c3c;">$1</code>')
    
    // Lists
    .replace(/^- (.*$)/gm, '<li style="margin: 0.3rem 0;">$1</li>')
    .replace(/^• (.*$)/gm, '<li style="margin: 0.3rem 0;">$1</li>')
    
    // Status indicators and emojis
    .replace(/🔴/g, '<span style="color: #e74c3c; font-weight: bold;">🔴</span>')
    .replace(/🟡/g, '<span style="color: #f39c12; font-weight: bold;">🟡</span>')
    .replace(/🟢/g, '<span style="color: #27ae60; font-weight: bold;">🟢</span>')
    .replace(/✅/g, '<span style="color: #27ae60;">✅</span>')
    .replace(/❌/g, '<span style="color: #e74c3c;">❌</span>')
    .replace(/⚠️/g, '<span style="color: #f39c12;">⚠️</span>')
    .replace(/🚨/g, '<span style="color: #e74c3c; font-weight: bold;">🚨</span>')
    
    // Tables (basic support)
    .replace(/\|([^|\n]*)\|([^|\n]*)\|([^|\n]*)\|/g, 
      '<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; padding: 0.5rem; border: 1px solid #dee2e6; background: #f8f9fa; margin: 0.3rem 0;"><div style="font-weight: bold;">$1</div><div>$2</div><div>$3</div></div>')
    
    // Horizontal rules
    .replace(/^---$/gm, '<hr style="border: none; border-top: 2px solid #ecf0f1; margin: 1.5rem 0;">')
    
    // Line breaks and paragraphs
    .replace(/\n\n/g, '</p><p style="margin: 0.8rem 0;">')
    .replace(/\n/g, '<br>');
  
  // Wrap consecutive list items in ul tags
  formatted = formatted.replace(/(<li.*?<\/li>)+/g, (match) => {
    return '<ul style="margin: 0.5rem 0; padding-left: 1.5rem;">' + match + '</ul>';
  });
  
  // Wrap content in paragraphs
  if (!formatted.startsWith('<h1') && !formatted.startsWith('<div') && !formatted.startsWith('<ul')) {
    formatted = '<p style="margin: 0.8rem 0;">' + formatted + '</p>';
  }
  
  return formatted;
};

const ReportsView = () => {
  const [selectedReport, setSelectedReport] = useState(null);
  const [generatingReportType, setGeneratingReportType] = useState(null);
  const [generatedReport, setGeneratedReport] = useState(null);
  const [error, setError] = useState(null);
  const [reportHistory, setReportHistory] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);

  useEffect(() => {
    fetchSystemStatus();
    fetchAvailableReportTypes();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get('/api/reports/health');
      setSystemStatus(response.data);
    } catch (err) {
      console.error('Error fetching system status:', err);
      setSystemStatus({ status: 'unavailable' });
    }
  };

  const fetchAvailableReportTypes = async () => {
    try {
      const response = await axios.get('/api/reports/types');
      // Note: availableReports state is used for API-driven report types
      // Currently using static reportTypes array but keeping this for future API integration
      console.log('Available report types from API:', response.data.available_types);
    } catch (err) {
      console.error('Error fetching report types:', err);
      setError('Failed to load available report types');
    }
  };

  const handleGenerateReport = async (reportType) => {
    setGeneratingReportType(reportType);
    setError(null);
    setGeneratedReport(null); // Clear previous report
    
    try {
      // Map UI report names to API report types
      const reportTypeMapping = {
        'Quality Control Report': 'quality_control',
        'Batch Record Analysis': 'batch_record',
        'Process Deviation Investigation': 'deviation',
        'OEE Performance Summary': 'oee',
        'Regulatory Compliance Review': 'compliance',
        'Manufacturing Excellence Report': 'excellence'
      };
      
      const apiReportType = reportTypeMapping[reportType] || 'quality_control';
      
      // Show progress indicator
      console.log(`Starting report generation for: ${reportType} (${apiReportType})`);
      
      const response = await axios.post('/api/reports/generate', {
        report_type: apiReportType,
        query: `Generate comprehensive ${reportType} for pharmaceutical manufacturing`,
        additional_context: {
          timestamp: new Date().toISOString(),
          source: 'pharmacopilot_dashboard',
          report_requested: reportType
        }
      }, {
        timeout: 300000, // 5 minutes timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Report generation response:', response.data);
      
      if (response.data.status === 'success') {
        const report = response.data.report || response.data;
        setGeneratedReport(report);
        setSelectedReport(reportType);
        
        // Add to report history
        const historyItem = {
          id: report.report_id || `RPT-${Date.now()}`,
          title: reportType,
          date: new Date().toLocaleDateString(),
          time: new Date().toLocaleTimeString(),
          status: 'Generated',
          type: 'AI-Generated RAG Report',
          description: `AI-powered ${reportType} with real-time data analysis`,
          content: report.report_content,
          metadata: report.metadata,
          generation_details: report.generation_details,
          processing_time: report.processing_time
        };
        
        setReportHistory(prev => [historyItem, ...prev.slice(0, 9)]); // Keep last 10 reports
        
        console.log(`Report generated successfully in ${report.processing_time || 'unknown time'}`);
      } else {
        const errorMsg = response.data.message || response.data.error || 'Unknown error occurred';
        setError(`Failed to generate report: ${errorMsg}`);
        console.error('Report generation failed:', response.data);
      }
      
    } catch (err) {
      console.error('Report generation error:', err);
      
      let errorMsg = 'Unknown error occurred';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = 'Report generation timed out. The system may be processing a complex analysis. Please try again.';
      } else if (err.response?.status === 504) {
        errorMsg = 'Report generation timed out due to high processing load. Please try again in a moment.';
      } else if (err.response?.status === 503) {
        errorMsg = 'Report Generation service is temporarily unavailable. Please check system status.';
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.response?.data?.message) {
        errorMsg = err.response.data.message;
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      setError(`Error generating report: ${errorMsg}`);
    } finally {
      setGeneratingReportType(null);
    }
  };

  const handleViewReport = (report) => {
    setSelectedReport(report.title);
    if (report.content) {
      setGeneratedReport({
        report_content: report.content,
        metadata: report.metadata || {},
        generation_details: report.generation_details || {}
      });
    }
  };

  const handleDownloadPDF = async () => {
    if (!generatedReport || !selectedReport) {
      setError('No report available for download');
      return;
    }

    try {
      console.log('Downloading PDF for report:', selectedReport);
      
      // Map UI report names to API report types
      const reportTypeMapping = {
        'Quality Control Report': 'quality_control',
        'Batch Record Analysis': 'batch_record',
        'Process Deviation Investigation': 'deviation',
        'OEE Performance Summary': 'oee',
        'Regulatory Compliance Review': 'compliance',
        'Manufacturing Excellence Report': 'excellence'
      };
      
      const apiReportType = reportTypeMapping[selectedReport] || 'quality_control';
      
      // Make request to PDF download endpoint
      const response = await axios.post('/api/reports/download-pdf', {
        report_type: apiReportType,
        query: `Generate comprehensive ${selectedReport} for pharmaceutical manufacturing`,
        additional_context: {
          timestamp: new Date().toISOString(),
          source: 'pharmacopilot_dashboard',
          report_requested: selectedReport
        }
      }, {
        responseType: 'blob', // Important for handling binary data
        timeout: 300000, // 5 minutes timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Create blob and download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename
      const reportId = generatedReport.report_id || `RPT-${Date.now()}`;
      const filename = `${reportId}.pdf`;
      link.download = filename;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log(`PDF downloaded successfully: ${filename}`);
      
    } catch (err) {
      console.error('PDF download error:', err);
      
      let errorMsg = 'Failed to download PDF';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = 'PDF generation timed out. Please try again.';
      } else if (err.response?.status === 504) {
        errorMsg = 'PDF generation timed out due to high processing load. Please try again.';
      } else if (err.response?.status === 503) {
        errorMsg = 'PDF generation service is temporarily unavailable.';
      } else if (err.response?.data) {
        errorMsg = 'Failed to generate PDF. Please check if all required dependencies are installed.';
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      setError(`PDF Download Error: ${errorMsg}`);
    }
  };

  const reportTypes = [
    'Quality Control Report',
    'Batch Record Analysis',
    'Process Deviation Investigation',
    'OEE Performance Summary',
    'Regulatory Compliance Review',
    'Manufacturing Excellence Report'
  ];

  const getStatusIndicator = () => {
    if (!systemStatus) {
      return (
        <div className="status-indicator status-offline" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LoadingSpinner size="small" minimal={true} color="#000000" />
          System Status Loading...
        </div>
      );
    }
    
    if (systemStatus.status === 'healthy') {
      return <div className="status-indicator status-healthy">AI Report Generation Active</div>;
    } else if (systemStatus.status === 'degraded') {
      return <div className="status-indicator status-warning">Limited Functionality - Some Components Unavailable</div>;
    } else {
      return <div className="status-indicator status-offline">Report Generation System Unavailable</div>;
    }
  };

  return (
    <div className="panel reports-panel">
      {getStatusIndicator()}

      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ fontSize: '1rem', color: '#495057', marginBottom: '1rem' }}>
          Generate AI-Powered Report
        </h4>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(3, 1fr)', 
          gap: '0.75rem',
          marginBottom: '0.5rem'
        }}>
          {reportTypes.map((type, index) => (
            <button
              key={index}
              className={`btn ${generatingReportType === type ? 'btn-disabled' : 'btn-secondary'}`}
              onClick={() => handleGenerateReport(type)}
              disabled={generatingReportType !== null || systemStatus?.status === 'unavailable'}
              style={{ 
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center', 
                padding: '0.875rem 0.75rem',
                fontSize: '0.8rem',
                fontWeight: '500',
                background: generatingReportType === type ? '#e9ecef' : 
                           (systemStatus?.status === 'unavailable' ? '#f8f9fa' : '#f8f9fa'),
                color: generatingReportType === type ? '#7d7d7dff' : '#555555ff',
                border: '1px solid #000000',
                borderRadius: '4px',
                cursor: generatingReportType === type || systemStatus?.status === 'unavailable' ? 
                        'not-allowed' : 'pointer',
                transition: 'all 0.2s ease-in-out',
                minHeight: '64px',
                boxShadow: 'none',
                transform: 'translateY(0)'
              }}
              onMouseEnter={(e) => {
                if (generatingReportType !== type && systemStatus?.status !== 'unavailable') {
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.background = '#e9ecef';
                  e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
                }
              }}
              onMouseLeave={(e) => {
                if (generatingReportType !== type && systemStatus?.status !== 'unavailable') {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.background = '#f8f9fa';
                  e.target.style.boxShadow = 'none';
                }
              }}
            >
              <span style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                lineHeight: '1.3'
              }}>
                {generatingReportType === type && (
                  <LoadingSpinner size="small" minimal={true} color="currentColor" />
                )}
                {generatingReportType === type ? 'Processing...' : `Generate ${type}`}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Loading Indicator */}
      {generatingReportType && (
        <div className="loading-panel-modern" style={{
          marginBottom: '1rem',
          padding: '1.5rem',
          background: 'rgba(248, 249, 250, 0.95)',
          borderRadius: '12px',
          border: '1px solid rgba(0, 0, 0, 0.1)',
          backdropFilter: 'blur(8px)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', justifyContent: 'center' }}>
            <LoadingSpinner size="medium" color="#000000" />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: '600', color: '#000000', fontSize: '0.9rem' }}>
                Processing {generatingReportType}
              </div>
              <div style={{ color: '#666666', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                AI analyzing data and generating insights
              </div>
            </div>
          </div>
          <ProgressBar 
            animated={true}
            color="#000000"
            backgroundColor="rgba(0, 0, 0, 0.1)"
            height={3}
            className="mt-3"
            style={{ marginTop: '1rem' }}
          />
        </div>
      )}

      {error && (
        <div style={{ 
          marginBottom: '1rem', 
          padding: '0.75rem', 
          background: '#ffeaa7', 
          color: '#d63031',
          borderRadius: '6px',
          border: '1px solid #fdcb6e',
          fontSize: '0.8rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'start', gap: '0.5rem' }}>
            <div style={{ fontSize: '1rem', marginTop: '-2px' }}></div>
            <div>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>Report Generation Failed</div>
              <div>{error}</div>
              <button 
                onClick={() => setError(null)}
                style={{
                  marginTop: '0.5rem',
                  background: 'none',
                  border: 'none',
                  color: '#d63031',
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  fontSize: '0.75rem'
                }}
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {generatedReport && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ fontSize: '1rem', color: '#495057', marginBottom: '0.75rem' }}>
            Generated Report: {selectedReport}
          </h4>
          
          {/* Report Header */}
          <div style={{
            background: 'linear-gradient(165deg, #202020ff 0%, #191919ff 100%)',
            color: 'white',
            padding: '1rem',
            borderRadius: '6px 6px 0 0',
            marginBottom: '0',
            border: '1px solid #000000',
            borderBottom: 'none'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', color: '#ffffff' }}>{selectedReport}</h3>
                <p style={{ margin: 0, fontSize: '0.8rem', opacity: 0.9, color: '#ffffff' }}>
                  Report ID: {generatedReport.report_id || `RPT-${Date.now()}`}
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#ffffff' }}>
                  <div style={{ color: '#ffffff' }}>Generated: {new Date(generatedReport.generated_at || generatedReport.generation_timestamp || Date.now()).toLocaleString()}</div>
                  {generatedReport.processing_time && (
                    <div style={{ color: '#ffffff' }}>Processing Time: {generatedReport.processing_time}</div>
                  )}
                  {generatedReport.metadata?.generation_method && (
                    <div style={{ color: '#ffffff' }}>Method: {generatedReport.metadata.generation_method}</div>
                  )}
                </div>
                <button
                  onClick={() => handleDownloadPDF()}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: '#ffffff',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    borderRadius: '4px',
                    padding: '0.5rem 1rem',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.background = 'rgba(255, 255, 255, 0.2)';
                    e.target.style.borderColor = 'rgba(255, 255, 255, 0.5)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.background = 'rgba(255, 255, 255, 0.1)';
                    e.target.style.borderColor = 'rgba(255, 255, 255, 0.3)';
                  }}
                >
                  Download Report
                </button>
              </div>
            </div>
          </div>

          {/* Report Content */}
          <div style={{
            background: '#ffffff',
            padding: '0',
            borderRadius: '0 0 6px 6px',
            border: '1px solid #000000',
            borderTop: 'none',
            maxHeight: '600px',
            overflowY: 'auto',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <div 
              style={{
                padding: '1.5rem',
                fontSize: '0.85rem',
                lineHeight: '1.6',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
              }}
              dangerouslySetInnerHTML={{
                __html: formatReportContent(
                  generatedReport.report_content || 
                  generatedReport.executive_summary || 
                  generatedReport.detailed_analysis || 
                  JSON.stringify(generatedReport, null, 2)
                )
              }}
            />
          </div>

          {/* Report Metadata */}
          {generatedReport.metadata && (
            <div style={{
              marginTop: '1rem',
              padding: '0.75rem',
              background: '#f8f9fa',
              borderRadius: '6px',
              border: '1px solid #e9ecef'
            }}>
              <h5 style={{ fontSize: '0.8rem', margin: '0 0 0.5rem 0', color: '#495057' }}>
                Report Metadata
              </h5>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                gap: '0.5rem',
                fontSize: '0.7rem',
                color: '#6c757d'
              }}>
                {generatedReport.metadata.data_sources && (
                  <div><strong>Data Sources:</strong> {generatedReport.metadata.data_sources.join(', ')}</div>
                )}
                {generatedReport.metadata.context_items_used && (
                  <div><strong>Context Items:</strong> {generatedReport.metadata.context_items_used}</div>
                )}
                {generatedReport.metadata.processing_time_seconds && (
                  <div><strong>Processing Time:</strong> {generatedReport.metadata.processing_time_seconds.toFixed(2)}s</div>
                )}
                {generatedReport.metadata.optimization_applied && (
                  <div><strong>Optimization:</strong>  Applied</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <div>
        <h4 style={{ fontSize: '1rem', color: '#495057', marginBottom: '0.75rem' }}>
          Recent Reports
        </h4>
        
        {reportHistory.length > 0 ? (
          <div className="report-list">
            {reportHistory.map((report) => (
              <div 
                key={report.id} 
                className="report-item"
                onClick={() => handleViewReport(report)}
                style={{ cursor: 'pointer' }}
              >
                <h5>{report.title}</h5>
                <p>
                  <strong>ID:</strong> {report.id} | <strong>Date:</strong> {report.date}
                </p>
                <p>
                  <strong>Type:</strong> {report.type} | <strong>Status:</strong> {report.status}
                </p>
                <p style={{ color: '#6c757d', fontSize: '0.7rem', marginTop: '0.25rem' }}>
                  {report.description}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="placeholder-text">
            No reports generated yet. Generate your first AI-powered report above.
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportsView; 