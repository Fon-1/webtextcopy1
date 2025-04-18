import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import datetime
import urllib3
import time
import pyperclip  # Import pyperclip for copy functionality

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set page config
st.set_page_config(
    page_title="Trích xuất nội dung",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "content" not in st.session_state:
    st.session_state.content = ""
if "title" not in st.session_state:
    st.session_state.title = ""
if "current_url" not in st.session_state:
    st.session_state.current_url = ""
if "prev_chapter_url" not in st.session_state:
    st.session_state.prev_chapter_url = None
if "next_chapter_url" not in st.session_state:
    st.session_state.next_chapter_url = None
if "ssl_verification" not in st.session_state:
    st.session_state.ssl_verification = True
if "current_domain" not in st.session_state:
    st.session_state.current_domain = None
if "debug_text" not in st.session_state:
    st.session_state.debug_text = ""
if "scroll_position" not in st.session_state:
    st.session_state.scroll_position = 0
if "current_annotation" not in st.session_state:
    st.session_state.current_annotation = ""
if "annotation_text" not in st.session_state:
    st.session_state.annotation_text = ""

# Function stubs (simplified for brevity)
def extract_content(url):
    # Simplified extraction function
    return f"Content extracted from {url}", f"Title for {url}", None, None

# Main app
st.title("📚 Text Extractor Tool")

# URL input
url = st.text_input("URL", st.session_state.current_url)
extract_clicked = st.button("⚡ Extract Content", key="extract_button")

# Process extraction
if url and extract_clicked:
    with st.spinner("Đang trích xuất..."):
        start_time = time.time()
        st.session_state.content, st.session_state.title, st.session_state.prev_chapter_url, st.session_state.next_chapter_url = extract_content(url)
        st.session_state.current_url = url
        extraction_time = time.time() - start_time
        
    st.success(f"✅ Extracted in {extraction_time:.2f} seconds")
    st.session_state.scroll_position = 0

# Display content if available
if st.session_state.content:
    st.header(f"📖 {st.session_state.title}")
    
    # Display the content in a text area
    content_text_area = st.text_area(
        "Content",
        value=st.session_state.content,
        height=400,
        key="content_area"
    )
    
    # Add a copy button with pyperclip
    if st.button("📋 COPY CONTENT", key="copy_button"):
        try:
            pyperclip.copy(st.session_state.content)
            st.success("✅ Content copied successfully!")
        except Exception as e:
            st.error(f"Error copying: {str(e)}")
            st.info("Try selecting the text manually and using Ctrl+C/Cmd+C to copy.")
    
    # Add a download button
    st.download_button(
        label="💾 Download as TXT",
        data=st.session_state.content,
        file_name=f"{st.session_state.title}.txt",
        mime="text/plain"
    )
    
    # Navigation
    st.markdown("### Navigation")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.prev_chapter_url:
            if st.button("⬅️ Previous Chapter", use_container_width=True):
                url = st.session_state.prev_chapter_url
                st.experimental_rerun()
        else:
            st.button("⬅️ Previous Chapter", disabled=True, use_container_width=True)
    
    with col3:
        if st.session_state.next_chapter_url:
            if st.button("➡️ Next Chapter", use_container_width=True):
                url = st.session_state.next_chapter_url
                st.experimental_rerun()
        else:
            st.button("➡️ Next Chapter", disabled=True, use_container_width=True)

# Run the app with: streamlit run a_fixed.py 