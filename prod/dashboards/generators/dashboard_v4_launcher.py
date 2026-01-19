import streamlit as st
import json
import os
import streamlit.components.v1 as components

# Config
st.set_page_config(page_title="Sentiment Dashboard V4", layout="wide", initial_sidebar_state="collapsed")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "dashboard_v4_dynamic.html")
JSON_PATH = os.path.join(BASE_DIR, "consolidated_sentiment_data.json")

def load_dashboard():
    # 1. Read JSON Data
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            json_content = f.read()
    except FileNotFoundError:
        st.error(f"Data file not found: {JSON_PATH}")
        return

    # 2. Read HTML Template
    try:
        with open(HTML_PATH, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        st.error(f"HTML file not found: {HTML_PATH}")
        return

    # 3. Inject Data
    # We inject the data as a global variable window.INJECTED_DATA before the script runs
    injection_script = f"""
    <script>
        window.INJECTED_DATA = {json_content};
    </script>
    """
    
    # Insert injection script before the closing body tag or head
    # Or just prepend it to the HTML if it handles it (it's robust)
    # But cleaner to put it before the main script execution.
    # The HTML has <div id="root"></div> and then <script type="text/babel">
    # We can inject it in <head> or start of <body>.
    
    final_html = html_content.replace('<body>', f'<body>{injection_script}')

    # 4. Render with Streamlit Components
    # height=1200 to give enough space, scrolling=True to allow internal scroll
    components.html(final_html, height=1200, scrolling=True)

if __name__ == "__main__":
    load_dashboard()
