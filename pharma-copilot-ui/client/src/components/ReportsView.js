import React, { useState } from 'react';

const ReportsView = () => {
  const [selectedReport, setSelectedReport] = useState(null);

  // Mock report data structure for demonstration
  const mockReports = [
    {
      id: 'RPT-001',
      title: 'Batch Quality Analysis',
      date: '2025-01-16',
      status: 'Generated',
      type: '21 CFR 11 Compliant',
      description: 'Comprehensive quality analysis for Batch #PH-2025-001'
    },
    {
      id: 'RPT-002', 
      title: 'Process Deviation Report',
      date: '2025-01-15',
      status: 'Generated',
      type: '21 CFR 11 Compliant',
      description: 'Analysis of temperature deviation incident on Line 2'
    },
    {
      id: 'RPT-003',
      title: 'OEE Performance Summary',
      date: '2025-01-14',
      status: 'Generated',
      type: 'Operational',
      description: 'Weekly OEE performance metrics and trends analysis'
    }
  ];

  const reportTypes = [
    'Quality Control Report',
    'Batch Record Analysis',
    'Process Deviation Investigation',
    'OEE Performance Summary',
    'Regulatory Compliance Review',
    'Manufacturing Excellence Report'
  ];

  const handleGenerateReport = (reportType) => {
    // In real implementation, this would trigger GenAI report generation
    alert(`Report generation request initiated for: ${reportType}\n\nThis feature will integrate with your GenAI systems to automatically generate comprehensive, 21 CFR 11 compliant reports based on current manufacturing data and historical analysis.`);
  };

  const handleViewReport = (report) => {
    setSelectedReport(report);
    // In real implementation, this would open the full report view
    alert(`Opening report: ${report.title}\n\nThis would display the full AI-generated report with narrative analysis, data citations, and regulatory compliance documentation.`);
  };

  return (
    <div className="panel reports-panel">
      <div className="status-indicator status-warning">
        Integration Pending - GenAI Systems
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ fontSize: '1rem', color: '#495057', marginBottom: '0.75rem' }}>
          Generate New Report
        </h4>
        <div style={{ display: 'grid', gap: '0.5rem' }}>
          {reportTypes.map((type, index) => (
            <button
              key={index}
              className="btn btn-secondary"
              onClick={() => handleGenerateReport(type)}
              style={{ 
                textAlign: 'left', 
                padding: '0.5rem 0.75rem',
                fontSize: '0.8rem',
                background: '#f8f9fa',
                color: '#495057',
                border: '1px solid #dee2e6'
              }}
            >
              Generate {type}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h4 style={{ fontSize: '1rem', color: '#495057', marginBottom: '0.75rem' }}>
          Recent Reports
        </h4>
        
        {mockReports.length > 0 ? (
          <div className="report-list">
            {mockReports.map((report) => (
              <div 
                key={report.id} 
                className="report-item"
                onClick={() => handleViewReport(report)}
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
            No reports available. Generate your first AI-powered report above.
          </div>
        )}
      </div>

      <div style={{ 
        marginTop: '1.5rem', 
        padding: '1rem', 
        background: '#f8f9fa', 
        borderRadius: '6px',
        border: '1px dashed #dee2e6'
      }}>
        <h5 style={{ fontSize: '0.875rem', color: '#495057', marginBottom: '0.5rem' }}>
          Upcoming Features
        </h5>
        <ul style={{ fontSize: '0.75rem', color: '#6c757d', paddingLeft: '1rem', margin: 0 }}>
          <li>AI-Generated Narrative Reports</li>
          <li>21 CFR 11 Compliance Documentation</li>
          <li>Real-time Data Citations</li>
          <li>Regulatory Submission Ready Formats</li>
          <li>Multi-language Report Generation</li>
          <li>Automated Report Scheduling</li>
          <li>Integration with RAG Knowledge Base</li>
        </ul>
      </div>

      <div style={{ 
        fontSize: '0.75rem', 
        color: '#6c757d', 
        marginTop: '1rem', 
        textAlign: 'center',
        fontStyle: 'italic'
      }}>
        This module will integrate with your GenAI systems for automated report generation
      </div>
    </div>
  );
};

export default ReportsView; 