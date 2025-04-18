import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import logging
import json
from pathlib import Path
import uuid
import datetime
import urllib3
import html

# Import helper functions
try:
    from helper_functions import (
        load_preferences, save_preferences, generate_custom_css,
        get_annotations, add_annotation, delete_annotation, 
        update_reading_progress
    )
except ImportError:
    # Define fallback functions if helper_functions.py is not found
    def load_preferences():
        """Load user preferences from a JSON file."""
        try:
            prefs_path = Path("preferences.json")
            if prefs_path.exists():
                with open(prefs_path, "r") as f:
                    return json.load(f)
            else:
                # Default preferences
                return {
                    "font_size": "16px",
                    "line_height": "1.6",
                    "font_family": "Arial, sans-serif",
                    "theme": "light",
                    "reading_history": {},
                    "annotations": {}
                }
        except Exception as e:
            logging.error(f"Error loading preferences: {str(e)}")
            # Return default preferences if there's an error
            return {
                "font_size": "16px",
                "line_height": "1.6",
                "font_family": "Arial, sans-serif",
                "theme": "light",
                "reading_history": {},
                "annotations": {}
            }
    
    def save_preferences(prefs):
        """Save user preferences to a JSON file."""
        try:
            prefs_path = Path("preferences.json")
            with open(prefs_path, "w") as f:
                json.dump(prefs, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving preferences: {str(e)}")
            return False
    
    def generate_custom_css(prefs):
        """Generate custom CSS based on user preferences."""
        theme = prefs.get("theme", "light")
        font_size = prefs.get("font_size", "16px")
        line_height = prefs.get("line_height", "1.6")
        font_family = prefs.get("font_family", "Arial, sans-serif")
        
        css = f"""
        <style>
        /* Custom CSS for user preferences */
        .stApp {{
            font-family: {font_family};
            font-size: {font_size};
            line-height: {line_height};
        }}
        
        /* Dark mode if selected */
        .stApp {{ {'background-color: #1E1E1E; color: #E0E0E0;' if theme == 'dark' else ''} }}
        
        /* Style for the content area */
        .stTextArea textarea {{
            font-family: {font_family} !important;
            font-size: {font_size} !important;
            line-height: {line_height} !important;
        }}
        </style>
        """
        return css
    
    def get_annotations(url):
        """Get annotations for a specific URL."""
        try:
            if "preferences" in st.session_state and "annotations" in st.session_state.preferences:
                annotations = st.session_state.preferences.get("annotations", {})
                return annotations.get(url, [])
        except Exception as e:
            logging.error(f"Error getting annotations: {str(e)}")
        return []
    
    def add_annotation(url, text, annotation_text, position):
        """Add an annotation for a specific URL."""
        try:
            if "preferences" not in st.session_state:
                st.session_state.preferences = load_preferences()
                
            if "annotations" not in st.session_state.preferences:
                st.session_state.preferences["annotations"] = {}
                
            if url not in st.session_state.preferences["annotations"]:
                st.session_state.preferences["annotations"][url] = []
                
            # Create annotation with unique ID
            annotation = {
                "id": str(uuid.uuid4()),
                "text": text,
                "annotation": annotation_text,
                "position": position,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            st.session_state.preferences["annotations"][url].append(annotation)
            save_preferences(st.session_state.preferences)
            return True
        except Exception as e:
            logging.error(f"Error adding annotation: {str(e)}")
            return False
    
    def delete_annotation(url, annotation_id):
        """Delete an annotation for a specific URL."""
        try:
            if "preferences" in st.session_state and "annotations" in st.session_state.preferences:
                if url in st.session_state.preferences["annotations"]:
                    annotations = st.session_state.preferences["annotations"][url]
                    st.session_state.preferences["annotations"][url] = [
                        a for a in annotations if a.get("id") != annotation_id
                    ]
                    save_preferences(st.session_state.preferences)
                    return True
        except Exception as e:
            logging.error(f"Error deleting annotation: {str(e)}")
        return False
    
    def update_reading_progress(url, title, position=0, total_length=0):
        """Update reading progress for a specific URL."""
        try:
            if "preferences" not in st.session_state:
                st.session_state.preferences = load_preferences()
                
            if "reading_history" not in st.session_state.preferences:
                st.session_state.preferences["reading_history"] = {}
                
            # Update or create reading history entry
            st.session_state.preferences["reading_history"][url] = {
                "title": title,
                "last_position": position,
                "total_length": total_length,
                "last_read": datetime.datetime.now().isoformat()
            }
            
            save_preferences(st.session_state.preferences)
            return True
        except Exception as e:
            logging.error(f"Error updating reading progress: {str(e)}")
            return False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("content_extractor")

# STREAMLIT UI - UNIVERSAL EXTRACTOR
st.set_page_config(
    page_title="Universal Content Extractor", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load user preferences on startup
if 'preferences' not in st.session_state:
    st.session_state.preferences = load_preferences()

# Apply custom CSS based on preferences
custom_css = generate_custom_css(st.session_state.preferences)
st.markdown(custom_css, unsafe_allow_html=True)

# Initialize session state for annotations
if 'current_annotation' not in st.session_state:
    st.session_state.current_annotation = None
if 'annotation_text' not in st.session_state:
    st.session_state.annotation_text = ""

# Initialize session state for navigation
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""
if 'prev_chapter_url' not in st.session_state:
    st.session_state.prev_chapter_url = None
if 'next_chapter_url' not in st.session_state:
    st.session_state.next_chapter_url = None
if 'content' not in st.session_state:
    st.session_state.content = ""
if 'title' not in st.session_state:
    st.session_state.title = ""
if 'debug_text' not in st.session_state:
    st.session_state.debug_text = ""
if 'execution_time' not in st.session_state:
    st.session_state.execution_time = 0
if 'selected_text_start' not in st.session_state:
    st.session_state.selected_text_start = 0
if 'selected_text_end' not in st.session_state:
    st.session_state.selected_text_end = 0
if 'scroll_position' not in st.session_state:
    st.session_state.scroll_position = 0

# Create navigation callback functions
def navigate_previous():
    if st.session_state.prev_chapter_url:
        # Set the current URL to the previous chapter URL
        st.session_state.current_url = st.session_state.prev_chapter_url
        st.session_state.needs_extraction = True

def navigate_next():
    if st.session_state.next_chapter_url:
        # Set the current URL to the next chapter URL
        st.session_state.current_url = st.session_state.next_chapter_url
        st.session_state.needs_extraction = True

# Flag to track if we need to extract content
if 'needs_extraction' not in st.session_state:
    st.session_state.needs_extraction = False

# Sidebar for settings and reading history
with st.sidebar:
    st.title("Cài đặt")
    
    # Reading preferences section
    st.header("Tùy chỉnh hiển thị")
    
    # Theme selector
    theme_options = {"light": "Sáng", "dark": "Tối"}
    selected_theme = st.selectbox(
        "Chế độ hiển thị",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(st.session_state.preferences.get("theme", "light"))
    )
    
    # Font size selector
    font_size_options = {"14px": "Nhỏ", "16px": "Vừa", "18px": "Lớn", "20px": "Rất lớn"}
    selected_font_size = st.selectbox(
        "Cỡ chữ",
        options=list(font_size_options.keys()),
        format_func=lambda x: font_size_options[x],
        index=list(font_size_options.keys()).index(st.session_state.preferences.get("font_size", "16px"))
    )
    
    # Line height selector
    line_height_options = {"1.4": "Hẹp", "1.6": "Vừa", "1.8": "Rộng", "2.0": "Rất rộng"}
    selected_line_height = st.selectbox(
        "Khoảng cách dòng",
        options=list(line_height_options.keys()),
        format_func=lambda x: line_height_options[x],
        index=list(line_height_options.keys()).index(st.session_state.preferences.get("line_height", "1.6"))
    )
    
    # Font family selector
    font_family_options = {
        "Arial, sans-serif": "Arial", 
        "Times New Roman, serif": "Times New Roman",
        "Georgia, serif": "Georgia",
        "Verdana, sans-serif": "Verdana",
        "Courier New, monospace": "Courier New"
    }
    selected_font_family = st.selectbox(
        "Phông chữ",
        options=list(font_family_options.keys()),
        format_func=lambda x: font_family_options[x],
        index=list(font_family_options.keys()).index(st.session_state.preferences.get("font_family", "Arial, sans-serif"))
    )
    
    # Update preferences if changed
    if (selected_theme != st.session_state.preferences.get("theme", "light") or
        selected_font_size != st.session_state.preferences.get("font_size", "16px") or
        selected_line_height != st.session_state.preferences.get("line_height", "1.6") or
        selected_font_family != st.session_state.preferences.get("font_family", "Arial, sans-serif")):
        
        st.session_state.preferences["theme"] = selected_theme
        st.session_state.preferences["font_size"] = selected_font_size
        st.session_state.preferences["line_height"] = selected_line_height
        st.session_state.preferences["font_family"] = selected_font_family
        
        save_preferences(st.session_state.preferences)
        st.markdown(generate_custom_css(st.session_state.preferences), unsafe_allow_html=True)
        st.rerun()  # Rerun to apply changes
    
    # Reading history section
    st.header("Lịch sử đọc")
    
    reading_history = st.session_state.preferences.get("reading_history", {})
    if reading_history:
        # Sort by last read time (most recent first)
        sorted_history = sorted(
            reading_history.items(), 
            key=lambda x: x[1].get("last_read", ""), 
            reverse=True
        )
        
        for url, data in sorted_history[:10]:  # Show only the 10 most recent
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📚 {data.get('title', 'Nội dung không tiêu đề')}", key=f"history_{url}"):
                    st.session_state.current_url = url
                    st.session_state.needs_extraction = True
                    st.rerun()
            with col2:
                # Show progress as percentage
                if data.get("total_length", 0) > 0:
                    progress = min(100, int((data.get("last_position", 0) / data.get("total_length", 1)) * 100))
                    st.text(f"{progress}%")
                else:
                    st.text("--")

# Main content area
st.markdown("## ⚡ Trích xuất nội dung từ web")

# URL input with current URL from session state
url = st.text_input(
    label="URL", 
    placeholder="Nhập URL trang web cần trích xuất nội dung...",
    value=st.session_state.current_url
)

# Show debug info toggle
show_debug = st.checkbox("Hiển thị thông tin debug", value=False)

# Extract button
extract_clicked = st.button("🚀 Trích xuất", use_container_width=True)

# Placeholder for extract_content function (simplified for this demo)
def extract_content(url):
    # Simplified extraction just for testing UI
    time.sleep(1)  # Simulating network delay
    return "Sample Title", "This is sample content to demonstrate the UI function.", 1.0, "Debug info would go here", None, None

# Process extraction when needed
if extract_clicked or st.session_state.needs_extraction:
    if not url:
        st.warning("⚠️ Vui lòng nhập URL")
    else:
        # Update current URL in session state
        st.session_state.current_url = url
        st.session_state.needs_extraction = False
        
        try:
            with st.spinner("⏳ Đang trích xuất..."):
                title, content, execution_time, debug_text, prev_chapter_url, next_chapter_url = extract_content(url)
                
                # Store all results in session state
                st.session_state.title = title
                st.session_state.content = content
                st.session_state.execution_time = execution_time
                st.session_state.debug_text = debug_text
                st.session_state.prev_chapter_url = prev_chapter_url
                st.session_state.next_chapter_url = next_chapter_url
                
                # Reset scroll position for new content
                st.session_state.scroll_position = 0
                
                # Update reading progress (0 position for new content)
                if content and len(content) > 100:
                    update_reading_progress(url, title, 0, len(content))
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")

# Function to handle annotation submission
def submit_annotation():
    if st.session_state.annotation_text and st.session_state.current_annotation:
        add_annotation(
            st.session_state.current_url,
            st.session_state.current_annotation,
            st.session_state.annotation_text,
            st.session_state.selected_text_start
        )
        st.session_state.annotation_text = ""
        st.session_state.current_annotation = None
        st.session_state.update_annotations = True

# Display content and navigation if available
if st.session_state.content and len(st.session_state.content) > 100:
    # Success message
    st.success(f"✅ Đã trích xuất trong {st.session_state.execution_time:.2f} giây")
    
    # Show the content
    with st.expander(f"📖 {st.session_state.title}", expanded=True):
        # Get current annotations for this URL
        annotations = get_annotations(st.session_state.current_url)
        
        # Create a key for tracking content changes for scroll position
        content_key = f"content_{hash(st.session_state.content)}"
        
        # ===== MOBILE-OPTIMIZED COPY SOLUTION =====
        # Create an even simpler copy solution
        current_text = st.session_state.content
        
        # Tạo container cho chức năng sao chép
        st.markdown("""
        <style>
        .simple-copy-container {
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            background-color: #f8fff8;
        }
        .simple-copy-title {
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
            color: #2E7D32;
        }
        .simple-copy-area {
            width: 100%;
            min-height: 150px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: white;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .simple-copy-button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            text-align: center;
            display: block;
            width: 100%;
            font-size: 16px;
            margin: 10px 0;
            cursor: pointer;
            border-radius: 5px;
        }
        .simple-instructions {
            background-color: #e8f5e9;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Tạo textarea cho việc copy
        st.text_area("Vùng sao chép nội dung", value=current_text, height=250, key="copy_area")
        
        # Hướng dẫn sao chép
        st.info("""
        **Cách sao chép nội dung:**
        1. Nhấp vào vùng văn bản phía trên
        2. Nhấn Ctrl+A (hoặc Command+A trên Mac) để chọn tất cả
        3. Nhấn Ctrl+C (hoặc Command+C trên Mac) để sao chép
        4. Đối với thiết bị di động: Chạm và giữ trên vùng văn bản, chọn "Chọn tất cả" và sau đó "Sao chép"
        """)
        
        # Nút trợ giúp sao chép
        helper_col1, helper_col2 = st.columns(2)
        with helper_col1:
            if st.button("📋 Trợ giúp sao chép", use_container_width=True):
                st.markdown("""
                <script>
                    try {
                        var copyArea = document.querySelector('textarea[aria-label="Vùng sao chép nội dung"]');
                        if (copyArea) {
                            copyArea.select();
                            document.execCommand('copy');
                            // Thông báo
                            alert("✓ Đã chọn vùng văn bản! Hãy nhấn Ctrl+C (hoặc Command+C) để sao chép.");
                        }
                    } catch (e) {
                        alert("Không thể tự động chọn văn bản. Vui lòng chọn thủ công.");
                    }
                </script>
                """, unsafe_allow_html=True)
        
        with helper_col2:
            # Nút tải về dưới dạng văn bản
            st.download_button(
                label="📥 Tải về dưới dạng văn bản",
                data=st.session_state.content,
                file_name=f"{st.session_state.title}.txt",
                mime="text/plain",
                help="Tải nội dung về thiết bị của bạn dưới dạng tệp văn bản",
                use_container_width=True
            )
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Display the content in a text area - height based on preferences
        col1, col2 = st.columns([4, 1])
        
        with col1:
            content_text_area = st.text_area(
                label="Nội dung chính",
                value=st.session_state.content,
                height=int(st.session_state.preferences.get("font_size", "16px").replace("px", "")) * 25,
                key=content_key
            )
            
            # Update reading progress when text area is interacted with
            if content_text_area != st.session_state.content:
                # Assume this is a scroll or selection interaction
                cursor_pos = len(content_text_area.split('\n', 1)[0])  # Simplistic approach, gets position of first line
                if cursor_pos > 0:
                    # Update reading progress
                    update_reading_progress(
                        st.session_state.current_url,
                        st.session_state.title,
                        cursor_pos,
                        len(st.session_state.content)
                    )
                    st.session_state.scroll_position = cursor_pos
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            # Nút sao chép đơn giản
            if st.button("📋 Sao chép", use_container_width=True):
                st.info("Hãy chọn toàn bộ nội dung ở phần sao chép phía trên.")
                
                # Tự động cuộn lên khu vực sao chép
                js = """
                <script>
                    // Cuộn lên khu vực sao chép
                    window.scrollTo(0, 0);
                </script>
                """
                st.components.v1.html(js, height=0)
        
        # Annotation section
        st.markdown("### 🖍️ Ghi chú & đánh dấu")
        
        # Text selection for annotation
        annotation_col1, annotation_col2 = st.columns([3, 1])
        with annotation_col1:
            selected_text = st.text_input("Đoạn văn bản để đánh dấu", key="selected_text")
            if selected_text != st.session_state.current_annotation:
                st.session_state.current_annotation = selected_text
        
        with annotation_col2:
            if st.button("Đánh dấu", key="annotate_button", disabled=not selected_text):
                st.session_state.annotation_active = True
        
        # If annotation is active, show the annotation input
        if st.session_state.get("annotation_active", False) and st.session_state.current_annotation:
            annotation_text = st.text_area("Ghi chú của bạn", key="annotation_input")
            st.session_state.annotation_text = annotation_text
            
            if st.button("Lưu ghi chú", key="save_annotation"):
                submit_annotation()
                st.session_state.annotation_active = False
                st.rerun()
        
        # Display existing annotations
        if annotations:
            st.markdown("### Các ghi chú đã lưu")
            for i, annotation in enumerate(annotations):
                with st.expander(f"{annotation.get('text', '')[:50]}...", expanded=False):
                    st.markdown(annotation.get("annotation", ""))
                    created_at = datetime.datetime.fromisoformat(annotation.get("created_at", datetime.datetime.now().isoformat()))
                    st.caption(f"Đã tạo: {created_at.strftime('%d/%m/%Y %H:%M')}")
                    if st.button("Xóa", key=f"delete_annotation_{i}"):
                        delete_annotation(st.session_state.current_url, annotation.get("id"))
                        st.rerun()
    
    # Navigation and Controls section
    st.markdown("### Điều hướng")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.prev_chapter_url:
            st.button("⬅️ Chương trước", on_click=navigate_previous, use_container_width=True)
        else:
            st.button("⬅️ Chương trước", disabled=True, use_container_width=True)
    
    with col2:
        # Download button
        st.download_button("💾 Tải về", st.session_state.content, file_name=f"{st.session_state.title}.txt", use_container_width=True)
    
    with col3:
        if st.session_state.next_chapter_url:
            st.button("➡️ Chương sau", on_click=navigate_next, use_container_width=True)
        else:
            st.button("➡️ Chương sau", disabled=True, use_container_width=True)
    
    # Display URL info
    with st.expander("🔗 Thông tin liên kết"):
        if st.session_state.prev_chapter_url:
            st.markdown(f"**Chương trước:** {st.session_state.prev_chapter_url}")
        else:
            st.markdown("**Chương trước:** Không tìm thấy")
            
        st.markdown(f"**Chương hiện tại:** {st.session_state.current_url}")
        
        if st.session_state.next_chapter_url:
            st.markdown(f"**Chương sau:** {st.session_state.next_chapter_url}")
        else:
            st.markdown("**Chương sau:** Không tìm thấy")
    
    # Show debug info if requested
    if show_debug:
        with st.expander("🔍 Debug Information", expanded=False):
            # Display original debugging information
            st.text(f"Fetching URL: {st.session_state.current_url}")
            if hasattr(st.session_state, 'debug_text'):
                st.text(st.session_state.debug_text)
                
            # Display navigation debug info if available
            if hasattr(st.session_state, 'navigation_debug') and st.session_state.navigation_debug:
                st.text("\nNavigation Information:")
                for line in st.session_state.navigation_debug:
                    st.text(line)
elif url and extract_clicked:
    st.error(f"❌ {st.session_state.title if st.session_state.title else 'Error'}")
    st.info("Không thể trích xuất. Hãy thử URL khác.")
    
    # Always show debug on error
    with st.expander("🔍 Debug Information", expanded=True):
        st.text(st.session_state.debug_text)

# Add a JavaScript injection for advanced UI features
st.markdown("""
<script>
// Script to enable better text selection
document.addEventListener('DOMContentLoaded', function() {
    // Wait for Streamlit to fully load
    setTimeout(() => {
        // Find the text area element
        const textArea = document.querySelector('textarea[aria-label="Nội dung chính"]');
        if (textArea) {
            // Add selection event listener
            textArea.addEventListener('mouseup', function() {
                const selection = window.getSelection();
                const selectedText = selection.toString();
                
                if (selectedText) {
                    // Find the input field for selection and update it
                    const selectionInput = document.querySelector('input[aria-label="Đoạn văn bản để đánh dấu"]');
                    if (selectionInput) {
                        selectionInput.value = selectedText;
                        // Trigger change event to update Streamlit
                        const event = new Event('input', { bubbles: true });
                        selectionInput.dispatchEvent(event);
                    }
                }
            });
        }
    }, 1000);
});
</script>
""", unsafe_allow_html=True)

# Custom footer
st.markdown("""
<style>
footer {visibility: hidden;}
.custom-footer {
    text-align: center;
    padding: 20px;
    font-size: 12px;
    color: #666;
    margin-top: 50px;
}
</style>
<div class="custom-footer">
    Universal Content Extractor | 📚 Được tạo ra để đọc và lưu trữ nội dung trực tuyến | Phiên bản: 2.0
</div>
""", unsafe_allow_html=True) 