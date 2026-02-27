PRIMARY_COLOR = "#556B2F"          # Olive green
BACKGROUND_COLOR = "#F4F6F0"       # Light cream
SECONDARY_BG = "#E3E8DA"           # Light sage
TEXT_COLOR = "#3B2F2F"             # Dark brown
ACCENT_COLOR_1 = "#6B7460"         # Sage green
ACCENT_COLOR_2 = "#4F5743"         # Dark olive
ACCENT_COLOR_3 = "#483C32"         # Dark brown

def load_css():
    return f"""
    <style>
        .stApp {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
        }}
        
        .main-header {{
            font-size: 2.8rem;
            font-weight: 700;
            color: {PRIMARY_COLOR};
            ... (ALL your same CSS)
        }}

                /* Subject input boxes styling - stacked vertically */
                /* Subject input boxes styling - stacked vertically */
        .subject-input-container {
            "display: flex;"
            "flex-direction: column;"
            "gap: 16px;"
            "margin-top: 10px;"
            "margin-bottom: 5px;"
            "width: 100%;"
        }
        
        .subject-item {
            "display: flex;"
            "flex-direction: column;"
            "width: 100%;"
        }
        
        .subject-item label {
            "font-size: 0.9rem;"
            "font-weight: 600;"
            "color: #3B2F2F;"
            "margin-bottom: 6px;"
            "margin-left: 4px;"
            "font-family: 'Segoe UI', sans-serif;"
        }
        
        /* Target Streamlit number input container */
        .subject-item div[data-testid="stNumberInput"] {
            "width: 100%;"
        }
        
        /* Style the input box */
        .subject-item div[data-testid="stNumberInput"] > div {
            "border: 2px solid #556B2F !important;"
            "border-radius: 14px !important;"
            "background-color: white !important;"
            "box-shadow: 0 2px 6px rgba(85, 107, 47, 0.1) !important;"
            "transition: all 0.2s ease !important;"
            "overflow: hidden !important;"
        }
        
        /* Style the input field itself */
        .subject-item div[data-testid="stNumberInput"] input {
            "border-radius: 12px !important;"
            "padding: 8px 14px !important;"
            "font-size: 1rem !important;"
            "font-weight: 500 !important;"
            "border: none !important;"
            "background-color: white !important;"
        }
        
        /* Focus state - darker border */
        .subject-item div[data-testid="stNumberInput"] > div:focus-within {
            "border: 2px solid #4F5743 !important;"
            "box-shadow: 0 0 0 3px rgba(85, 107, 47, 0.2) !important;"
        }
        
        /* Hover state */
        .subject-item div[data-testid="stNumberInput"] > div:hover {
            "border: 2px solid #6B7460 !important;"
        }
        
        /* Style the step buttons (up/down arrows) */
        .subject-item div[data-testid="stNumberInput"] button {
            "background-color: #F4F6F0 !important;"
            "border-left: 1px solid #556B2F !important;"
            "color: #556B2F !important;"
        }
        
        .subject-item div[data-testid="stNumberInput"] button:hover {
            "background-color: #556B2F !important;"
            "color: white !important;"
        }
    </style>
    """
def get_colors():
    return {
        'primary': PRIMARY_COLOR,
        'background': BACKGROUND_COLOR,
        'secondary_bg': SECONDARY_BG,
        'text': TEXT_COLOR,
        'accent1': ACCENT_COLOR_1,
        'accent2': ACCENT_COLOR_2,
        'accent3': ACCENT_COLOR_3
    }