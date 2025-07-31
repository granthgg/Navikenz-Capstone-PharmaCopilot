"""
Prompt templates for different report types in PharmaCopilot
"""

class PromptTemplates:
    """
    Collection of prompt templates for different pharmaceutical manufacturing reports
    """
    
    @staticmethod
    def get_quality_control_prompt() -> str:
        """Prompt template for quality control reports"""
        return """
        Generate a comprehensive pharmaceutical quality control report focusing on:
        - Current defect probability analysis
        - Quality classification assessment
        - Risk level evaluation
        - Process parameter analysis
        - Regulatory compliance status
        - Actionable recommendations
        
        Ensure the report is professional, factual, and compliant with pharmaceutical standards.
        """
    
    @staticmethod
    def get_batch_record_prompt() -> str:
        """Prompt template for batch record analysis"""
        return """
        Generate a detailed batch record analysis report covering:
        - Batch performance metrics
        - Process parameter compliance
        - Yield analysis
        - Quality indicators
        - Deviation analysis
        - Batch disposition recommendations
        
        Focus on regulatory compliance and manufacturing excellence.
        """
    
    @staticmethod
    def get_deviation_prompt() -> str:
        """Prompt template for deviation investigation"""
        return """
        Generate a thorough deviation investigation report including:
        - Root cause analysis
        - Impact assessment
        - Corrective actions
        - Preventive measures
        - Regulatory implications
        - Timeline for resolution
        
        Ensure comprehensive documentation for regulatory compliance.
        """
    
    @staticmethod
    def get_system_prompt() -> str:
        """Base system prompt for all pharmaceutical reports"""
        return """
        You are an expert pharmaceutical manufacturing analyst with deep knowledge of:
        - FDA regulations (21 CFR Part 11, 21 CFR Part 210/211)
        - Good Manufacturing Practices (GMP)
        - Quality assurance and control
        - Process optimization
        - Risk management
        - Regulatory compliance
        
        Generate professional, accurate, and actionable reports that meet pharmaceutical industry standards.
        All reports must be free of emojis and decorative elements.
        """
