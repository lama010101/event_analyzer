#!/usr/bin/env python3
"""
Streamlit app entry point for Vercel deployment
"""
import streamlit as st
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main app function
try:
    from app import main
    
    # Set up Streamlit configuration for Vercel
    st.set_page_config(
        page_title="Historical Image Analysis",
        page_icon="📸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Run the main app
    if __name__ == "__main__":
        main()
        
except Exception as e:
    st.error(f"Error loading application: {str(e)}")
    st.stop()