"""
Emoji Cleaner Utility for PharmaCopilot Reports
Removes all emojis from report content and replaces them with text equivalents
"""

import re

def clean_emojis_from_text(text):
    """
    Remove emojis from text and replace with text equivalents
    """
    if not text:
        return text
    
    # Define emoji replacements
    emoji_replacements = {
        # Status indicators
        '🔴': '[HIGH RISK]',
        '🟡': '[MEDIUM RISK]', 
        '🟢': '[LOW RISK]',
        '✅': '[OK]',
        '❌': '[FAIL]',
        '⚠️': '[WARNING]',
        '🚨': '[ALERT]',
        
        # Trends and analysis
        '📈': '[INCREASING]',
        '📉': '[DECREASING]',
        '📊': '[DATA]',
        '📋': '[REPORT]',
        '📄': '[DOCUMENT]',
        
        # Actions and maintenance
        '🔧': '[MAINTENANCE]',
        '⚙️': '[SETTINGS]',
        '💡': '[TIP]',
        '🎯': '[TARGET]',
        
        # Factory and production
        '🏭': '[FACTORY]',
        '⏰': '[TIME]',
        '🔄': '[PROCESS]',
        '📦': '[PACKAGE]',
        
        # General symbols
        '⭐': '[STAR]',
        '💯': '[100%]',
        '🎉': '[SUCCESS]',
        '🔍': '[SEARCH]',
    }
    
    # Apply replacements
    cleaned_text = text
    for emoji, replacement in emoji_replacements.items():
        cleaned_text = cleaned_text.replace(emoji, replacement)
    
    # Remove any remaining emojis using regex
    # This regex matches most emoji characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+", 
        flags=re.UNICODE
    )
    
    cleaned_text = emoji_pattern.sub('', cleaned_text)
    
    return cleaned_text

def clean_report_content(report_data):
    """
    Clean emojis from a complete report data structure
    """
    if isinstance(report_data, dict):
        cleaned_data = {}
        for key, value in report_data.items():
            if isinstance(value, str):
                cleaned_data[key] = clean_emojis_from_text(value)
            elif isinstance(value, (dict, list)):
                cleaned_data[key] = clean_report_content(value)
            else:
                cleaned_data[key] = value
        return cleaned_data
    
    elif isinstance(report_data, list):
        return [clean_report_content(item) for item in report_data]
    
    elif isinstance(report_data, str):
        return clean_emojis_from_text(report_data)
    
    else:
        return report_data

if __name__ == "__main__":
    # Test the cleaner
    test_text = """
    # 📊 Quality Control Report
    
    ## Status: ✅ Healthy
    - Risk Level: 🔴 High
    - Trend: 📈 Increasing
    - Alert: 🚨 Critical
    """
    
    print("Original:")
    print(test_text)
    print("\nCleaned:")
    print(clean_emojis_from_text(test_text))
