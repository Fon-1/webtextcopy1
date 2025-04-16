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

# Special function for metruyencv.com
def extract_metruyencv(url, html, soup, debug_info):
    """
    Special extraction method specifically for metruyencv.com
    """
    debug_info.append("Using specialized metruyencv.com extractor")
    title = ""
    content = ""
    
    # Get title
    title_elem = soup.select_one('h1.txt-primary')
    if title_elem:
        title = title_elem.get_text().strip()
        debug_info.append(f"Found title: {title}")
    else:
        # Try alternate title selector
        title_elem = soup.select_one('title')
        if title_elem:
            title = title_elem.get_text().split(' - ')[0].strip()
            debug_info.append(f"Found title from page title: {title}")
    
    # EXTREME FOCUS APPROACH: Identify and extract ONLY the story content
    
    # Get the article content area - add more robust selectors for Yugioh novel
    article = soup.select_one('#article.chapter-content')
    if not article:
        article = soup.select_one('.nh-read__content')
    if not article:
        article = soup.select_one('.chapter-c')  # Another common container
    if not article:
        article = soup.select_one('article.chapter')  # Another possible container
    
    # Special handling for Yugioh: Bệnh Nghiện Rồng novel
    if not article and "yugioh" in url.lower():
        debug_info.append("Trying specialized selectors for Yugioh novel")
        article = soup.select_one('main.container')
        
        # If we found the main container but need to narrow down to content
        if article:
            # Try to find the actual content container within the main container
            potential_content = article.select('.content, .chapter-content, .chapter, article')
            if potential_content:
                largest_text = ""
                largest_elem = None
                for elem in potential_content:
                    text = elem.get_text().strip()
                    if len(text) > len(largest_text):
                        largest_text = text
                        largest_elem = elem
                
                if largest_elem:
                    article = largest_elem
                    debug_info.append(f"Found content container for Yugioh novel with {len(largest_text)} characters")
    
    if not article:
        debug_info.append("Could not find content container")
        # More robust fallback - try to get content from main or article elements
        main_container = soup.select_one('main')
        if main_container:
            # Only proceed if we have a main container
            debug_info.append("Using main container as fallback")
            # Extract chapter content directly from text
            raw_text = main_container.get_text(separator='\n', strip=True)
            
            # Look for chapter title pattern
            chapter_title_match = re.search(r'(Chương|Chapter)\s+\d+.*?(?=\n|$)', raw_text)
            if chapter_title_match:
                chapter_title = chapter_title_match.group(0).strip()
                debug_info.append(f"Found chapter title: {chapter_title}")
                
                # Extract content after the chapter title
                content_start_idx = raw_text.find(chapter_title) + len(chapter_title)
                content_text = raw_text[content_start_idx:].strip()
                
                # Split into paragraphs
                paragraphs = []
                for line in content_text.split('\n'):
                    line = line.strip()
                    if line and len(line) > 20:  # Only meaningful paragraphs
                        paragraphs.append(line)
                
                if paragraphs:
                    final_content = chapter_title + "\n\n" + "\n\n".join(paragraphs)
                    debug_info.append(f"Extracted content with fallback method: {len(final_content)} characters")
                    return title, final_content
        
        return title, "Failed to extract content"
    
    # Step 1: Directly remove ALL UI elements from the HTML before extraction
    for ui_element in article.select('.chapter-nav, .chapter-header, .chapter-footer, .ads, .ad-container, .js-button, .button, .btn, .config-panel, .navigate, .nav, .setting, .rating, .comment, .comment-section, .lock-content, div[id^="ads-"], div[class*="rating"], div[class*="config"], div[class*="setting"], div[class*="navigate"], div[class*="header"], div[class*="footer"], div[class*="button"]'):
        ui_element.decompose()
    
    # Step 2: Get clean raw text from the remaining content
    raw_text = article.get_text(separator='\n', strip=True)
    
    # Step 3: ULTRA-DIRECT PATTERN MATCHING to find the actual chapter content
    # This targets the specific pattern of Yugioh novel chapters but works for other novels too
    
    # Look for chapter title pattern
    chapter_title_match = re.search(r'(Chương|Chapter)\s+\d+.*?(?=\n|$)', raw_text)
    
    if chapter_title_match:
        chapter_title = chapter_title_match.group(0).strip()
        debug_info.append(f"Found chapter title: {chapter_title}")
        
        # Find where the actual content starts (after the chapter title)
        content_start_idx = raw_text.find(chapter_title) + len(chapter_title)
        
        # Find where the chapter content ends (before lock message or navigation)
        end_markers = [
            "Vui lòng đăng nhập", 
            "Chương Bị Khóa",
            "Chương trước",
            "Chấm điểm",
            "Tặng quà", 
            "Báo cáo",
            "Đề cử",
            "Chương sau"
        ]
        
        content_end_idx = len(raw_text)
        for marker in end_markers:
            idx = raw_text.find(marker, content_start_idx)
            if idx > 0:
                content_end_idx = min(content_end_idx, idx)
        
        # Extract just the story content between chapter title and end marker
        raw_content = raw_text[content_start_idx:content_end_idx].strip()
        
        # Step 4: SUPER AGGRESSIVE FILTERING of extracted content
        
        # Direct string removal of problematic UI elements
        ui_strings = [
            "Cấu hình", "Mục lục", "Đánh dấu", "Cài đặt đọc truyện", "Close", 
            "Màu nền", "Màu chữ", "Font chữ", "Cỡ chữ", "Chiều cao dòng", "Canh chữ", 
            "Mặc định", "CấuhìnhMụclụcĐánhdấuCàiđặtđọctruyệnClose",
            "MàunềnMàuchữFontchữCỡchữChiềucaodòngCanhchữ",
            "chữđượctrìnhbàytrênmộtcột"
        ]
        
        # Exact matches of concatenated UI blocks
        exact_ui_blocks = [
            "Cấu hìnhMục lụcĐánh dấuCài đặt đọc truyệnClose",
            "CấuhìnhMụclụcĐánhdấuCàiđặtđọctruyệnClose",
            "Màu nền [ngày]#F8FAFC#f4f4f4#e9ebee#d5d8dc#f4f4e4#f5ebcd#eae4d3#f2f2f2#c2b49b#272729#232323#1e293b",
            "Màu chữ [ngày]Màu nền [đêm]#F8FAFC#f4f4f4#e9ebee#d5d8dc#f4f4e4#f5ebcd#eae4d3#f2f2f2#c2b49b#272729#232323#1e293bMàu chữ [đêm]",
            "Font chữAvenir NextBookerlySegoe UILiterataBaskervilleArialCourier NewTahomaPalatino LinotypeGeorgiaVerdanaTimes New RomanSource Sans Pro",
            "Cỡ chữChiều cao dòngCanh chữCanh tráiCanh đềuCanh giữaCanh phảiMặc định"
        ]
        
        # Step 5: Line-by-line cleaning
        clean_lines = []
        is_content_started = False
        
        for line in raw_content.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip any line containing UI elements (case-insensitive check)
            should_skip = False
            for ui_text in ui_strings:
                if ui_text.lower() in line.lower():
                    should_skip = True
                    break
            
            # Skip exact UI blocks
            for ui_block in exact_ui_blocks:
                if ui_block in line:
                    should_skip = True
                    break
            
            # Skip lines with hex colors or many special characters
            if re.search(r'#[A-Fa-f0-9]{3,6}', line) or len(re.findall(r'[#\[\]{}()<>/\\|@]', line)) > 5:
                should_skip = True
            
            # Skip lines that are just UI noise based on content patterns
            if len(line) < 10 and any(word in line.lower() for word in ["cấu", "hình", "màu", "font", "chữ", "nền", "đóng", "close"]):
                should_skip = True
            
            # Start content only when we find a line with actual content
            if not is_content_started and len(line) > 30 and not should_skip:
                is_content_started = True
            
            # Only keep lines after we've found actual content
            if is_content_started and not should_skip:
                clean_lines.append(line)
        
        # Step 6: Combine with proper chapter title
        if clean_lines:
            final_content = chapter_title + "\n\n" + "\n\n".join(clean_lines)
            return title, final_content
    
    # Fallback: If we couldn't find a chapter title, try extracting paragraphs directly
    paragraphs = []
    
    # Extract all paragraph elements
    for p in article.find_all('p'):
        text = p.get_text().strip()
        if text and len(text) > 20:  # Only meaningful paragraphs
            # Skip UI elements
            if not any(ui in text.lower() for ui in ["cấu hình", "mục lục", "đánh dấu", "cài đặt", "màu nền", "màu chữ"]):
                paragraphs.append(text)
    
    if paragraphs:
        content = "\n\n".join(paragraphs)
        return title, content
    
    # Final fallback: Just clean the raw text as much as possible
    raw_text = article.get_text()
    
    # Remove all known UI patterns
    for ui_pattern in [
        r'Cấu\s*hình.*?Mặc\s*định',
        r'Màu\s*nền.*?#[A-Fa-f0-9]{3,6}.*?#[A-Fa-f0-9]{3,6}',
        r'Font\s*chữ.*?Source\s*Sans\s*Pro',
        r'Vui\s*lòng\s*đăng\s*nhập.*?Chương\s*sau'
    ]:
        raw_text = re.sub(ui_pattern, '', raw_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Split into lines and clean
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    clean_lines = []
    
    for line in lines:
        # Skip short lines with UI indicators
        if len(line) < 20 and any(ui in line.lower() for ui in ["cấu", "hình", "màu", "font", "chữ"]):
            continue
        clean_lines.append(line)
    
    if clean_lines:
        content = "\n\n".join(clean_lines)
    
    return title, content

# Modify the deep_clean_content function to be less aggressive
def deep_clean_content(content, domain=None, is_novel=False, debug_info=None):
    """
    Performs cleaning of extracted content to remove noise while preserving actual content.
    
    Args:
        content: The text content to clean
        domain: The website domain (optional)
        is_novel: Whether the content is from a novel site
        debug_info: List to store debug information
    
    Returns:
        Cleaned content with noise removed
    """
    if not debug_info:
        debug_info = []
    
    if not content or len(content.strip()) < 100:
        return content
        
    debug_info.append("Performing deep content cleaning")
    start_length = len(content)
    
    # Check if the content has a chapter title pattern (common in novels)
    # If it does, we need to be more careful with cleaning
    has_chapter_pattern = re.search(r'(chương|chapter)\s+\d+', content.lower())
    
    # Split content into lines for processing
    lines = content.split('\n')
    clean_lines = []
    
    # Common noise patterns - reduced aggressiveness
    noise_patterns = [
        # Color codes
        r'#[A-Fa-f0-9]{3,6}',
        # Authentication
        r'^(đăng\s*nhập|đăng\s*ký|login|register|sign\s*in|sign\s*up)$'
    ]
    
    # UI elements to look for - but only delete if they occur on their own lines
    standalone_ui_patterns = [
        r'^cấu\s*hình$', 
        r'^mục\s*lục$', 
        r'^đánh\s*dấu$', 
        r'^cài\s*đặt\s*đọc\s*truyện$', 
        r'^close$',
        r'^màu\s*nền$', 
        r'^màu\s*chữ$', 
        r'^font\s*chữ$', 
        r'^cỡ\s*chữ$', 
        r'^chiều\s*cao\s*dòng$', 
        r'^canh\s*chữ$',
        r'^mặc\s*định$'
    ]
    
    # Process each line
    for i, line in enumerate(lines):
        original_line = line
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Keep chapter headings intact
        if re.search(r'(chương|chapter)\s+\d+', line.lower()):
            clean_lines.append(line)
            continue
        
        # Skip very short lines that don't make sense as content
        if len(line) < 5 and not re.match(r'^["\']+.*[!?.]["\']+$', line):
            continue
        
        # Check against standalone UI patterns - skip only if the entire line matches
        should_skip = False
        for pattern in standalone_ui_patterns:
            if re.match(pattern, line.lower()):
                should_skip = True
                break
                
        if should_skip:
            continue
        
        # Check against other noise patterns
        for pattern in noise_patterns:
            if re.search(pattern, line.lower()):
                should_skip = True
                break
        
        if should_skip:
            continue
            
        # Check for high symbol density - but only for short lines
        if len(line) < 30:
            symbol_count = len(re.findall(r'[#\[\]{}()<>/\\|@$%^&*+=]', line))
            if symbol_count > len(line) * 0.15:  # Reduced from 0.1 to 0.15
                continue
        
        # This line passed all filters - add it to clean content
        clean_lines.append(line)
    
    # Special handling for novels - keep more content
    if is_novel or has_chapter_pattern:
        # If we have a chapter pattern and very few lines, the cleaning was probably too aggressive
        if has_chapter_pattern and len(clean_lines) < 3 and len(lines) > 10:
            debug_info.append("Cleaning was too aggressive, reverting to less aggressive filtering")
            # Try again with minimal filtering
            clean_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Only remove exact matches of UI elements
                if line in ["Cấu hình", "Mục lục", "Đánh dấu", "Cài đặt đọc truyện", "Close", 
                           "Màu nền", "Màu chữ", "Font chữ", "Cỡ chữ", "Chiều cao dòng", "Canh chữ"]:
                    continue
                    
                # Only remove lines with hexadecimal color codes
                if re.search(r'#[A-Fa-f0-9]{3,6}', line):
                    continue
                    
                clean_lines.append(line)
    # Reconstruct the content
    final_content = '\n\n'.join(clean_lines)
    
    # Final cleanup operations
    # Remove excessive whitespace
    final_content = re.sub(r'\n{3,}', '\n\n', final_content)
    final_content = re.sub(r' {2,}', ' ', final_content)
    
    # Trim final content
    final_content = final_content.strip()
    
    # Safeguard - if cleaned content is much shorter than original, it might have been too aggressive
    if len(final_content) < min(300, start_length * 0.3) and start_length > 1000:
        debug_info.append("Cleaned content too short, reverting to original content")
        # The cleaning was too aggressive, revert to original but remove only definite UI elements
        lines = content.split('\n')
        minimal_clean_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Only remove the most obvious UI elements
            if any(ui in line for ui in ["#F8FAFC", "Màu nền [ngày]", "Màu chữ [ngày]", "Font chữAvenir Next"]):
                continue
                
            minimal_clean_lines.append(line)
            
        final_content = '\n\n'.join(minimal_clean_lines)
    
    end_length = len(final_content)
    reduction = start_length - end_length
    debug_info.append(f"Deep cleaning removed {reduction} characters ({reduction/max(1, start_length)*100:.1f}% reduction)")
    
    return final_content

# Also modify the clean_vietnamese_novel function to be less aggressive
def clean_vietnamese_novel(content, debug_info=None):
    """
    Specialized cleaning for Vietnamese novel content with a more balanced approach.
    
    Args:
        content: The text content to clean
        debug_info: List to store debug information
    
    Returns:
        Cleaned content with Vietnamese-specific noise removed
    """
    if not debug_info:
        debug_info = []
    
    if not content or len(content.strip()) < 100:
        return content
    
    debug_info.append("Applying specialized Vietnamese novel cleaning")
    start_length = len(content)
    
    # Check if we already have a good chapter
    has_chapter_title = re.search(r'(Chương|Chapter)\s+\d+', content, re.IGNORECASE)
    has_paragraphs = content.count('\n\n') > 3  # Multiple paragraphs indicates probably good content
    
    # If the content already looks good, do minimal cleaning
    if has_chapter_title and has_paragraphs and len(content) > 500:
        debug_info.append("Content already well-structured, applying minimal cleaning")
        # Only remove exact matches of UI blocks
        ui_blocks = [
            "Cấu hình", "Mục lục", "Đánh dấu", "Cài đặt đọc truyện", "Close",
            "Màu nền", "Màu chữ", "Font chữ", "Cỡ chữ", "Chiều cao dòng",
            "Canh chữ", "Mặc định", "CấuhìnhMụclụcĐánhdấuCàiđặtđọctruyệnClose",
            "MàunềnMàuchữFontchữCỡchữChiềucaodòngCanhchữ"
        ]
        
        # Split by paragraphs to preserve structure
        paragraphs = content.split('\n\n')
        clean_paragraphs = []
        
        for paragraph in paragraphs:
            # Skip if it's an exact UI block
            if paragraph.strip() in ui_blocks:
                continue
                
            # Skip if it has hex color codes
            if re.search(r'#[A-Fa-f0-9]{3,6}', paragraph):
                continue
                
            clean_paragraphs.append(paragraph)
            
        cleaned_content = '\n\n'.join(clean_paragraphs)
        
        end_length = len(cleaned_content)
        reduction = start_length - end_length
        if reduction > 0:
            debug_info.append(f"Minimal Vietnamese cleaning removed {reduction} characters ({reduction/max(1, start_length)*100:.1f}% reduction)")
        
        return cleaned_content
    
    # Vietnamese-specific patterns to remove - reduced aggressiveness
    vn_noise_patterns = [
        # Concatenated UI elements (no spaces) - only match exact patterns
        r'^(cấuhình|mụclục|đánhdấu|càiđặt|đọctruyện|màunền|màuchữ|fontchữ|cỡchữ)$',
        # Mix of Vietnamese and English UI terms - only match exact patterns
        r'^(darkmode|lightmode|fontsize|lineheight|textalign)$',
        # Color codes
        r'#[A-Fa-f0-9]{3,6}'
    ]
    
    # Common text segments that appear at start/end of chapters
    vn_chapter_noise = [
        "Cấu hình", "Mục lục", "Đánh dấu", "Cài đặt đọc truyện", 
        "Màu nền", "Màu chữ", "Font chữ", "Cỡ chữ", "Chiều cao dòng", 
        "Canh chữ", "Canh trái", "Canh giữa", "Canh phải", "Canh đều",
        "Chương trước", "Chương sau", "Chấm điểm", "Đề cử", "Tặng quà", "Báo cáo",
        "Close", "Mặc định"
    ]
    
    # Process line by line with more specific Vietnamese context
    lines = content.split('\n')
    clean_lines = []
    
    # First pass: Remove exact noise segments
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Skip exact matches of known noise
        should_skip = False
        for noise in vn_chapter_noise:
            if line == noise:  # Only exact matches, not substring matches
                should_skip = True
                break
        
        if should_skip:
            continue
            
        # Check against Vietnamese-specific patterns - only for exact matches or short lines
        if len(line) < 30:  # Only apply to short lines to avoid filtering real content
            for pattern in vn_noise_patterns:
                if re.search(pattern, line.lower().replace(" ", "")):
                    should_skip = True
                    break
        
        if should_skip:
            continue
        
        # Keep this line
        clean_lines.append(line)
    
    # Second pass: Structure detection - group lines into paragraphs
    paragraphs = []
    current_paragraph = []
    
    # Try to detect chapter structure
    chapter_title_pattern = r'(chương|chapter)\s+\d+'
    has_chapter_structure = any(re.search(chapter_title_pattern, line.lower()) for line in clean_lines)
    
    # Process cleaned lines for paragraph structure
    for i, line in enumerate(clean_lines):
        # Chapter titles are always separate paragraphs
        if re.search(chapter_title_pattern, line.lower()):
            if current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
            paragraphs.append(line)
            continue
            
        # Group shorter lines that don't end with punctuation
        if len(line) < 100 and not line.rstrip().endswith(('.', '!', '?', ':', '…', '"', '"', '"')):
            current_paragraph.append(line)
        else:
            # This line ends a paragraph
            current_paragraph.append(line)
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
    
    # Add any remaining paragraph
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    # Join paragraphs with double newlines
    cleaned_content = '\n\n'.join(paragraphs)
    
    # Final formatting cleanup
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)  # Normalize newlines
    cleaned_content = re.sub(r' {2,}', ' ', cleaned_content)      # Remove extra spaces
    
    # Safeguard - if cleaned content is much shorter than original, it might have been too aggressive
    if len(cleaned_content) < min(300, start_length * 0.3) and start_length > 1000:
        debug_info.append("Vietnamese cleaning was too aggressive, reverting to minimal cleaning")
        # Try again with minimal filtering
        minimal_clean_content = content
        
        # Only remove exact UI blocks
        for ui_block in vn_chapter_noise:
            minimal_clean_content = minimal_clean_content.replace(ui_block, '')
            
        # Remove color codes
        minimal_clean_content = re.sub(r'#[A-Fa-f0-9]{3,6}', '', minimal_clean_content)
        
        # Clean up formatting
        minimal_clean_content = re.sub(r'\n{3,}', '\n\n', minimal_clean_content)
        minimal_clean_content = re.sub(r' {2,}', ' ', minimal_clean_content)
        minimal_clean_content = minimal_clean_content.strip()
        
        cleaned_content = minimal_clean_content
    
    end_length = len(cleaned_content)
    reduction = start_length - end_length
    if reduction > 0:
        debug_info.append(f"Vietnamese novel cleaning removed {reduction} characters ({reduction/max(1, start_length)*100:.1f}% reduction)")
    
    return cleaned_content

# Enhanced Universal Content Extractor - Works on any website
def extract_content(url):
    start_time = time.time()
    debug_info = []
    next_chapter_url = None
    prev_chapter_url = None
    
    try:
        # Create session with cookies
        session = requests.Session()
        
        # Generic browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        debug_info.append(f"Fetching URL: {url}")
        
        # Get the page with reasonable timeout
        timeout_value = st.session_state.get('timeout_setting', 30)  # Default to 30 seconds
        
        # Parse URL to get domain first
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        debug_info.append(f"Domain: {domain}")
        
        # Store domain in session state for future navigation
        if 'current_domain' not in st.session_state:
            st.session_state.current_domain = domain
        else:
            st.session_state.current_domain = domain
        
        # Double-check that a proper timeout value is set, especially for problematic domains
        if "truyensextv" in domain or "metruyencv" in domain:
            if timeout_value < 45:
                timeout_value = 45  # Force minimum 45 seconds for these problematic domains
                debug_info.append(f"Forced minimum timeout value of 45s for problematic domain: {domain}")
        
        debug_info.append(f"Using timeout: {timeout_value}s")
        
        # Special handling for problematic domains with SSL issues
        ssl_verification = True
        if "truyensextv" in domain:
            # Disable SSL verification for problematic sites
            ssl_verification = False
            # Import urllib3 here to suppress warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            debug_info.append("SSL verification disabled for known problematic site")
            
            # Store SSL settings in session state for future navigation
            st.session_state.ssl_verification = False
        else:
            # Update session state with current SSL settings
            st.session_state.ssl_verification = True
        
        # Performance optimization - set a longer connect timeout but shorter read timeout
        # This helps with slow initial connections but prevents hanging on data transfer
        timeouts = (timeout_value, min(timeout_value, 30))  # (connect_timeout, read_timeout)
        debug_info.append(f"Using connect/read timeouts: {timeouts}")
        
        # Attempt the request with appropriate settings
        try:
            response = session.get(
                url, 
                headers=headers, 
                timeout=timeouts,
                verify=ssl_verification,
                stream=True  # Use streaming for better performance
            )
            # Read in chunks for better memory usage
            content_chunks = []
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                if chunk:
                    content_chunks.append(chunk)
            html = ''.join(content_chunks) if isinstance(content_chunks[0], str) else b''.join(content_chunks).decode('utf-8', errors='ignore')
            
        except requests.exceptions.SSLError:
            # If we get an SSL error, retry without verification
            debug_info.append("SSL Error occurred. Retrying without SSL verification.")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = session.get(
                url,
                headers=headers,
                timeout=timeouts,
                verify=False,
                stream=True  # Use streaming for better performance
            )
            # Read in chunks for better memory usage
            content_chunks = []
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                if chunk:
                    content_chunks.append(chunk)
            html = ''.join(content_chunks) if isinstance(content_chunks[0], str) else b''.join(content_chunks).decode('utf-8', errors='ignore')
            
            debug_info.append("Successfully retrieved content with SSL verification disabled")
        
        # Set base URL for building links
        base_url = f"{parsed_url.scheme}://{domain}"
        
        # Extract title for reference
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        title = title_match.group(1).split(' - ')[0].strip() if title_match else "Extracted Content"
        debug_info.append(f"Title: {title}")
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract navigation links (next/previous chapter)
        # This needs to happen before we remove elements from the soup
        debug_info.append("Looking for chapter navigation links")
        
        # Special handling for metruyencv.com - they have specific navigation patterns
        if 'metruyencv.com' in domain:
            debug_info.append("Using metruyencv.com specialized navigation detection")
            
            # For metruyencv we need a different approach - they use specific classes and patterns
            # First try the chapter-nav links
            nav_links = soup.select('.chapter-nav a, .chapter-header a, .chapter-actions a, .btn-chap a')
            
            for link in nav_links:
                try:
                    # Get the text and href
                    link_text = link.get_text().lower().strip()
                    link_href = link.get('href', '')
                    
                    # Check text content for navigation clues
                    if any(term in link_text for term in ['chương sau', 'tiếp', 'tiếp theo', 'next']):
                        if link_href:
                            next_chapter_url = link_href if link_href.startswith('http') else f"{base_url}{link_href}"
                            debug_info.append(f"Found next chapter URL (metruyencv): {next_chapter_url}")
                    elif any(term in link_text for term in ['chương trước', 'trước', 'previous', 'prev']):
                        if link_href:
                            prev_chapter_url = link_href if link_href.startswith('http') else f"{base_url}{link_href}"
                            debug_info.append(f"Found previous chapter URL (metruyencv): {prev_chapter_url}")
                except Exception as e:
                    debug_info.append(f"Error processing navigation link: {str(e)}")
            # If we didn't find navigation using the above approach, try secondary approach
            if not next_chapter_url or not prev_chapter_url:
                # Look for links with icon classes typically used for navigation
                icon_links = soup.select('a.fa-arrow-left, a.fa-arrow-right, a.fa-angle-left, a.fa-angle-right, a.prev-chap, a.next-chap')
                
                for link in icon_links:
                    try:
                        link_href = link.get('href', '')
                        if not link_href:
                            continue
                            
                        link_class = link.get('class', [])
                        if isinstance(link_class, str):
                            link_class = link_class.split()
                            
                        if any(cls in ['fa-arrow-right', 'fa-angle-right', 'next-chap'] for cls in link_class):
                            next_chapter_url = link_href if link_href.startswith('http') else f"{base_url}{link_href}"
                            debug_info.append(f"Found next chapter URL from icon (metruyencv): {next_chapter_url}")
                        elif any(cls in ['fa-arrow-left', 'fa-angle-left', 'prev-chap'] for cls in link_class):
                            prev_chapter_url = link_href if link_href.startswith('http') else f"{base_url}{link_href}"
                            debug_info.append(f"Found previous chapter URL from icon (metruyencv): {prev_chapter_url}")
                    except Exception as e:
                        debug_info.append(f"Error processing icon link: {str(e)}")
            
            # Third approach: Look directly at the HTML for navigation patterns
            if not next_chapter_url or not prev_chapter_url:
                # Try to find links by looking at text that contains navigation terms
                all_links = soup.find_all('a')
                
                for link in all_links:
                    try:
                        link_text = link.get_text().lower().strip()
                        link_href = link.get('href', '')
                        
                        if not link_href:
                            continue
                            
                        # Match on Vietnamese navigation terms
                        if not next_chapter_url and any(nav_term in link_text for nav_term in ['chương sau', 'chương tiếp', 'tiếp theo']):
                            next_chapter_url = link_href if link_href.startswith('http') else f"{base_url}{link_href}"
                            debug_info.append(f"Found next chapter URL from text (metruyencv): {next_chapter_url}")
                        
                        if not prev_chapter_url and any(nav_term in link_text for nav_term in ['chương trước', 'quay lại']):
                            prev_chapter_url = link_href if link_href.startswith('http') else f"{base_url}{link_href}"
                            debug_info.append(f"Found previous chapter URL from text (metruyencv): {prev_chapter_url}")
                    except Exception as e:
                        continue  # Skip this link if there's an error
            
            # Fourth approach: Try to infer navigation from the current chapter number in the URL
            if (not next_chapter_url or not prev_chapter_url) and 'chuong-' in url:
                try:
                    # Extract the current chapter number from the URL
                    chapter_match = re.search(r'chuong-(\d+)', url)
                    if chapter_match:
                        current_chapter = int(chapter_match.group(1))
                        debug_info.append(f"Current chapter number: {current_chapter}")
                        
                        # Construct URLs for adjacent chapters
                        base_path = url[:url.find(f"chuong-{current_chapter}")]
                        
                        if not prev_chapter_url and current_chapter > 1:
                            prev_chapter_url = f"{base_path}chuong-{current_chapter - 1}"
                            debug_info.append(f"Inferred previous chapter URL: {prev_chapter_url}")
                        
                        if not next_chapter_url:
                            next_chapter_url = f"{base_path}chuong-{current_chapter + 1}"
                            debug_info.append(f"Inferred next chapter URL: {next_chapter_url}")
                except Exception as e:
                    debug_info.append(f"Error inferring chapter URLs: {str(e)}")
        
        # Common patterns for next/prev chapter links - using BeautifulSoup's :-soup-contains instead of :contains
        if not next_chapter_url:
            # Try to find navigation links using common patterns
            for selector in [
                'a.next-chap, a.next_chapter, a.next, a.next-chapter, a[rel="next"]',
                '.next-chap a, .next_chapter a, .next a, .next-chapter a',
                '#next_chap, #next_chapter, #next'
            ]:
                next_links = soup.select(selector)
                if next_links:
                    next_href = next_links[0].get('href')
                    if next_href:
                        # Handle relative URLs
                        if next_href.startswith('/'):
                            next_chapter_url = f"{base_url}{next_href}"
                        elif not (next_href.startswith('http://') or next_href.startswith('https://')):
                            next_chapter_url = f"{base_url}/{next_href}"
                        else:
                            next_chapter_url = next_href
                        debug_info.append(f"Found next chapter URL: {next_chapter_url}")
                        break
            
            # Try to find by text content
            if not next_chapter_url:
                for a in soup.find_all('a'):
                    link_text = a.get_text().lower().strip()
                    if any(term in link_text for term in ['next chapter', 'chương sau', 'chap sau', 'tiếp', 'next']):
                        next_href = a.get('href')
                        if next_href:
                            # Handle relative URLs
                            if next_href.startswith('/'):
                                next_chapter_url = f"{base_url}{next_href}"
                            elif not (next_href.startswith('http://') or next_href.startswith('https://')):
                                next_chapter_url = f"{base_url}/{next_href}"
                            else:
                                next_chapter_url = next_href
                            debug_info.append(f"Found next chapter URL by text: {next_chapter_url}")
                            break
        
        if not prev_chapter_url:
            # Try to find navigation links using common patterns
            for selector in [
                'a.prev-chap, a.prev_chapter, a.prev, a.previous-chapter, a[rel="prev"]',
                '.prev-chap a, .prev_chapter a, .prev a, .previous-chapter a',
                '#prev_chap, #prev_chapter, #previous'
            ]:
                prev_links = soup.select(selector)
                if prev_links:
                    prev_href = prev_links[0].get('href')
                    if prev_href:
                        # Handle relative URLs
                        if prev_href.startswith('/'):
                            prev_chapter_url = f"{base_url}{prev_href}"
                        elif not (prev_href.startswith('http://') or prev_href.startswith('https://')):
                            prev_chapter_url = f"{base_url}/{prev_href}"
                        else:
                            prev_chapter_url = prev_href
                        debug_info.append(f"Found previous chapter URL: {prev_chapter_url}")
                        break
            
            # Try to find by text content
            if not prev_chapter_url:
                for a in soup.find_all('a'):
                    link_text = a.get_text().lower().strip()
                    if any(term in link_text for term in ['previous chapter', 'chương trước', 'chap trước', 'trước', 'previous', 'prev']):
                        prev_href = a.get('href')
                        if prev_href:
                            # Handle relative URLs
                            if prev_href.startswith('/'):
                                prev_chapter_url = f"{base_url}{prev_href}"
                            elif not (prev_href.startswith('http://') or prev_href.startswith('https://')):
                                prev_chapter_url = f"{base_url}/{prev_href}"
                            else:
                                prev_chapter_url = prev_href
                            debug_info.append(f"Found previous chapter URL by text: {prev_chapter_url}")
                            break
        
        # Check for specialized extractors
        if 'metruyencv.com' in domain:
            title, content = extract_metruyencv(url, html, soup, debug_info)
            if content and len(content) > 100:
                # Apply deep cleaning to the content
                content = deep_clean_content(content, domain, True, debug_info)
                # Apply Vietnamese-specific novel cleaning
                content = clean_vietnamese_novel(content, debug_info)
                
                execution_time = time.time() - start_time
                debug_info.append(f"Extraction completed in {execution_time:.2f} seconds")
                debug_text = '\n'.join(debug_info)
                return title, content, execution_time, debug_text, prev_chapter_url, next_chapter_url

        # Remove elements that are definitely not content
        for element in soup.select('script, style, noscript, meta, link, head, iframe, svg, path, [role="banner"], [role="navigation"], [role="complementary"], [role="search"], [role="form"], [role="region"], [role="alert"], .ads, .ad-container, .advertisement, .sidebar, .comments, .comment-section'):
            element.decompose()
        
        # Try to detect and remove navigation, header, and footer
        for element in soup.find_all(['nav', 'header', 'footer']):
            element.decompose()
            
        # Remove comment elements
        for element in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
            element.extract()
        
        # STEP 1: SPECIALIZED HANDLING FOR COMMON SITES
        
        # Check if we're dealing with a novel site or blog - with error handling
        is_novel_site = False
        is_blog = False
        is_news_site = False
        
        # Safely check for novel site
        try:
            novel_domains = ['wuxiaworld.com', 'royalroad.com', 'novelupdates.com', 'webnovel.com', 'metruyencv.com', 'truyenfull.vn']
            is_novel_site = any(nd in domain for nd in novel_domains)
        except Exception as e:
            debug_info.append(f"Error during novel site check: {str(e)}")
        
        # Safely check for blog
        try:
            article_elements = soup.find_all('article')
            # Make sure article_elements is iterable before using it
            is_blog = article_elements is not None and len(article_elements) > 0
        except Exception as e:
            debug_info.append(f"Error during blog check: {str(e)}")
        
        # Safely check for news site
        try:
            news_domains = ['news.', 'cnn.', 'bbc.', 'nytimes.', 'theguardian.', 'reuters.']
            is_news_site = any(nd in domain for nd in news_domains)
        except Exception as e:
            debug_info.append(f"Error during news site check: {str(e)}")
        
        # Special case for metruyencv.com
        if 'metruyencv.com' in domain:
            is_novel_site = True
            debug_info.append("Detected metruyencv.com - using specialized novel extraction")
            
        debug_info.append(f"Site type: {'Novel' if is_novel_site else 'Blog' if is_blog else 'News' if is_news_site else 'General'}")
        
        # Store all potential content blocks
        content_blocks = []
        
        # Method 1: Look for common content containers
        selectors = []
        
        # Add specialized selectors based on site type
        if is_novel_site:
            selectors.extend(['.chapter-content', '.chapter-inner', '.chapter', '#chapter', '.chapter-text', '.reading-content', '#novel-content', '.novel-content'])
        
        if is_blog or is_news_site:
            selectors.extend(['.post-content', '.entry-content', '.article-content', '.article__content', '.article-body', '.story-body', '.story-content'])
        
        # Always include these generic selectors
        selectors.extend(['article', 'main', '[role="main"]', '.content', '#content', '.post', '.article', '.entry', '.page-content', '.post-content', '.story'])
        
        # Check if specific domain patterns are present
        if 'metruyencv.com' in domain or 'truyenfull.vn' in domain:
            # Add specific selectors for Vietnamese novel sites
            selectors.insert(0, '#article.chapter-content')
            selectors.insert(0, '.nh-read__content')
        
        debug_info.append(f"Trying selectors: {selectors[:5]}...")
        
        # Find elements matching our selectors
        for selector in selectors:
            try:
                elements = soup.select(selector)
                debug_info.append(f"Selector {selector}: found {len(elements)} elements")
                
                for element in elements:
                    # Skip if too small or empty
                    if len(element.get_text().strip()) < 200:
                        continue
                    
                    # Calculate text-to-HTML ratio (higher = more likely to be content)
                    html_length = len(str(element))
                    text_length = len(element.get_text())
                    if html_length == 0:
                        ratio = 0
                    else:
                        ratio = text_length / html_length
                    
                    # Check the density of paragraph tags
                    p_count = len(element.find_all('p'))
                    p_density = p_count / max(1, text_length / 500)  # number of <p> tags per 500 chars
                    
                    # Higher score for elements with good paragraph structure
                    p_score = min(2.0, p_density * 0.5)  # Cap at doubling the score
                    
                    # Calculate final score, weighting for different site types
                    if is_novel_site:
                        # Novel sites often have less HTML structure but more plain text
                        final_score = text_length * ratio * 1.5
                    else:
                        # Regular sites should have good paragraph structure
                        final_score = text_length * ratio * (1.0 + p_score)
                    
                    content_blocks.append({
                        'element': element,
                        'text': element.get_text(),
                        'length': text_length,
                        'ratio': ratio,
                        'score': final_score,
                        'selector': selector
                    })
            except Exception as e:
                debug_info.append(f"Error processing selector {selector}: {str(e)}")
        
        # Method 2: Find divs with substantial text
        if not content_blocks:
            debug_info.append("No content from selectors, searching divs with substantial text")
            try:
                for div in soup.find_all(['div', 'section']):
                    try:
                        text = div.get_text().strip()
                        if len(text) > 300:  # Only consider substantial text blocks
                            # Calculate text density
                            html_length = len(str(div))
                            text_length = len(text)
                            ratio = text_length / html_length if html_length > 0 else 0
                            
                            # Check for paragraph density
                            p_count = len(div.find_all('p'))
                            p_density = p_count / max(1, text_length / 500)
                            p_score = min(2.0, p_density * 0.5)
                            
                            # Calculate score
                            if is_novel_site:
                                final_score = text_length * ratio * 1.5
                            else:
                                final_score = text_length * ratio * (1.0 + p_score)
                            
                            content_blocks.append({
                                'element': div,
                                'text': text,
                                'length': text_length,
                                'ratio': ratio,
                                'score': final_score,
                                'selector': 'div-text'
                            })
                    except Exception as e:
                        continue  # Skip this div on error
            except Exception as e:
                debug_info.append(f"Error during div search: {str(e)}")
        
        # Method 3: Find element with most paragraph tags
        if not content_blocks:
            try:
                debug_info.append("Searching for element with most paragraph tags")
                max_paragraphs = 0
                best_element = None
                
                for element in soup.find_all(['div', 'article', 'section']):
                    try:
                        paragraphs = element.find_all('p')
                        if len(paragraphs) > max_paragraphs:
                            # Check if paragraphs contain meaningful text
                            total_text = ' '.join(p.get_text().strip() for p in paragraphs)
                            if len(total_text) > 200:
                                max_paragraphs = len(paragraphs)
                                best_element = element
                    except Exception:
                        continue  # Skip this element on error
                
                if best_element:
                    # Calculate metrics
                    text = best_element.get_text().strip()
                    html_length = len(str(best_element))
                    text_length = len(text)
                    ratio = text_length / html_length if html_length > 0 else 0
                    
                    content_blocks.append({
                        'element': best_element,
                        'text': text,
                        'length': text_length,
                        'ratio': ratio,
                        'score': text_length * ratio,
                        'selector': 'max-paragraphs'
                    })
            except Exception as e:
                debug_info.append(f"Error during paragraph search: {str(e)}")
        
        # Method 4: Last resort - look for largest text block
        if not content_blocks:
            try:
                debug_info.append("Looking for largest text block as last resort")
                all_elements = soup.find_all(['div', 'article', 'section', 'main'])
                if all_elements:
                    largest_text = ""
                    largest_element = None
                    for element in all_elements:
                        try:
                            text = element.get_text().strip()
                            if len(text) > len(largest_text):
                                largest_text = text
                                largest_element = element
                        except Exception:
                            continue  # Skip this element on error
                    
                    if largest_element and len(largest_text) > 200:
                        # Calculate metrics
                        html_length = len(str(largest_element))
                        text_length = len(largest_text)
                        ratio = text_length / html_length if html_length > 0 else 0
                        
                        content_blocks.append({
                            'element': largest_element,
                            'text': largest_text,
                            'length': text_length,
                            'ratio': ratio,
                            'score': text_length * ratio,
                            'selector': 'largest-text'
                        })
            except Exception as e:
                debug_info.append(f"Error during largest text search: {str(e)}")
        
        # STEP 2: SELECT BEST CONTENT BLOCK
        
        content_text = ""
        if content_blocks:
            # Sort by score
            content_blocks.sort(key=lambda x: x['score'], reverse=True)
            
            # Get top 3 blocks for debugging
            top_blocks = content_blocks[:min(3, len(content_blocks))]
            debug_info.append(f"Top content blocks:")
            for i, block in enumerate(top_blocks):
                debug_info.append(f"{i+1}. Score: {block['score']:.2f}, Length: {block['length']}, Ratio: {block['ratio']:.2f}, Selector: {block['selector']}")
            
            # Get the highest scoring content
            content_text = content_blocks[0]['text']
            debug_info.append(f"Selected content with score {content_blocks[0]['score']:.2f} and length {len(content_text)}")
        else:
            # As a last resort, get the whole body text
            try:
                body = soup.find('body')
                if body:
                    content_text = body.get_text()
                    debug_info.append("No content blocks found, using body text")
            except Exception as e:
                debug_info.append(f"Error getting body text: {str(e)}")
                content_text = ""
        
        # STEP 3: ENHANCED CONTENT CLEANING
        
        # Split into lines for cleaning
        lines = content_text.split('\n')
        clean_lines = []
        
        # Content analysis metrics
        if not lines or not any(line.strip() for line in lines):
            avg_line_length = 0
            max_line_length = 0
        else:
            try:
                avg_line_length = sum(len(line.strip()) for line in lines if line.strip()) / max(1, len([line for line in lines if line.strip()]))
                max_line_length = max((len(line.strip()) for line in lines if line.strip()), default=0)
            except Exception as e:
                debug_info.append(f"Error calculating line metrics: {str(e)}")
                avg_line_length = 0
                max_line_length = 0
        
        debug_info.append(f"Average line length: {avg_line_length:.2f}, Max line length: {max_line_length}")
        
        # Count lines before cleaning
        original_line_count = len([line for line in lines if line.strip()])
        debug_info.append(f"Original line count: {original_line_count}")
        
        # Detect common chapter patterns for novel sites
        chapter_pattern = None
        if is_novel_site:
            try:
                # Look for chapter title patterns
                chapter_matches = []
                for line in lines:
                    if line.strip():
                        match1 = re.search(r'chapter\s+\d+', line.lower())
                        if match1:
                            chapter_matches.append(match1)
                        match2 = re.search(r'chương\s+\d+', line.lower())
                        if match2:
                            chapter_matches.append(match2)
                
                if chapter_matches:
                    debug_info.append(f"Detected novel chapter format")
                    # Format might be novel chapters
                    chapter_pattern = r'(chapter|chương)\s+\d+'
            except Exception as e:
                debug_info.append(f"Error detecting chapter pattern: {str(e)}")
        
        # Process each line with error handling
        for i, line in enumerate(lines):
            try:
                line = line.strip()
                if not line:
                    continue
                
                # Keep chapter headings in novels
                if chapter_pattern and re.search(chapter_pattern, line.lower()):
                    clean_lines.append(line)
                    continue
                
                # Skip very short lines that look like UI elements
                if len(line) < 5 and not re.match(r'^[A-Z]+!$|^[!?\.]+$', line):
                    continue
                
                # Additional checks for novel sites - preserve short sound effects
                if is_novel_site and re.match(r'^["\']*[A-Z][a-z]*[!\?\.]+["\']*$', line):
                    clean_lines.append(line)
                    continue
                    
                # Skip lines with high special character density
                special_char_ratio = len(re.findall(r'[#\[\]{}()<>/\\|@]', line)) / (len(line) + 0.1)
                if special_char_ratio > 0.1:  # More than 10% special chars
                    continue
                
                # Skip lines with many non-word characters (likely UI)
                word_char_ratio = len(re.findall(r'\w', line)) / (len(line) + 0.1)
                if word_char_ratio < 0.5 and len(line) < 20:  # Less than 50% word chars and short
                    continue
                    
                # Skip lines that look like navigation/UI
                if re.match(r'^([<>«»]|next|prev|previous|forward|back|home|menu|login|search|sign in)$', line.lower()):
                    continue
                    
                # Calculate how much this line differs from average length
                if avg_line_length > 0:
                    length_difference = abs(len(line) - avg_line_length) / max(1, avg_line_length)
                    
                    # Short lines surrounded by much longer lines might be headings or UI elements
                    if i > 0 and i < len(lines) - 1 and len(line) < 20 and length_difference > 0.7:
                        # Check if next and previous lines are much longer (suggesting this is a heading)
                        prev_line = lines[i-1].strip() if i > 0 else ""
                        next_line = lines[i+1].strip() if i < len(lines) - 1 else ""
                        
                        if len(prev_line) > 50 and len(next_line) > 50:
                            # This could be a heading - we'll keep it
                            clean_lines.append(line)
                            continue
                            
                        # Otherwise it might be UI - but only skip if it's very short
                        if len(line) < 10:
                            continue
                
                # This line passed all filters - add it to clean content
                clean_lines.append(line)
            except Exception as e:
                debug_info.append(f"Error processing line: {str(e)}")
                # Add the line anyway if we encounter an error
                if line and len(line.strip()) > 20:
                    clean_lines.append(line.strip())
        
        # Count lines after cleaning
        clean_line_count = len(clean_lines)
        debug_info.append(f"Clean line count: {clean_line_count}")
        debug_info.append(f"Removed {original_line_count - clean_line_count} lines")
        
        # If no clean lines, use a simple approach
        if not clean_lines:
            debug_info.append("No lines passed filtering, using simple extraction")
            clean_lines = [line.strip() for line in content_text.split('\n') if len(line.strip()) > 20]
        
        # STEP 4: IMPROVED PARAGRAPH FORMATION
        
        paragraphs = []
        current_paragraph = []
        
        # Detect if content has a lot of dialogue (affects paragraph formation)
        dialogue_pattern = r'"[^"]+"|\'[^\']+\''
        dialogue_count = 0
        
        try:
            dialogue_matches = []
            for line in clean_lines:
                match = re.search(dialogue_pattern, line)
                if match:
                    dialogue_matches.append(match)
            dialogue_count = len(dialogue_matches)
            is_dialogue_heavy = dialogue_count > len(clean_lines) * 0.3
        except Exception as e:
            debug_info.append(f"Error during dialogue detection: {str(e)}")
            is_dialogue_heavy = False
        
        debug_info.append(f"Dialogue heavy: {is_dialogue_heavy} ({dialogue_count}/{len(clean_lines)} lines with dialogue)")
        
        # Special handling for novels
        if is_novel_site:
            # Novel formatting often uses shorter paragraphs
            paragraph_threshold = 15
        else:
            # Regular content can have longer paragraphs
            paragraph_threshold = 25
        
        # If we have very few lines, don't try to form paragraphs
        if len(clean_lines) <= 3:
            paragraphs = clean_lines
        else:
            try:
                for line in clean_lines:
                    # Skip empty lines
                    if not line.strip():
                        continue
                        
                    # Chapter headings are always standalone
                    if chapter_pattern and re.search(chapter_pattern, line.lower()):
                        if current_paragraph:
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                        paragraphs.append(line)
                        continue
                        
                    # Very short lines are likely standalone elements (headings, exclamations, etc.)
                    if len(line) < paragraph_threshold:
                        if current_paragraph:
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                        paragraphs.append(line)
                        continue
                    
                    # Lines with dialogue in dialogue-heavy content might be standalone
                    if is_dialogue_heavy and re.search(dialogue_pattern, line) and len(line) < 100:
                        if current_paragraph:
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                        paragraphs.append(line)
                        continue
                        
                    # Lines ending with sentence-ending punctuation might end paragraphs
                    if line.endswith(('.', '!', '?')):
                        current_paragraph.append(line)
                        paragraphs.append(' '.join(current_paragraph))
                        current_paragraph = []
                    else:
                        # Otherwise, add to current paragraph
                        current_paragraph.append(line)
            except Exception as e:
                debug_info.append(f"Error during paragraph formation: {str(e)}")
                # If paragraph formation fails, just use the clean lines as paragraphs
                paragraphs = clean_lines
        
        # Add any remaining paragraph
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Join paragraphs with double newlines
        content = '\n\n'.join(paragraphs)
        
        # FINAL CLEANUP
        
        # Remove extra spaces
        content = re.sub(r' +', ' ', content)
        
        # Fix excessive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Final whitespace trim
        content = content.strip()
        
        # Check if extracted content is too short - might be error
        if len(content) < 300 and original_line_count > 50:
            debug_info.append("WARNING: Extracted content is very short compared to original")
            
            # As a fallback, try a simpler approach with less aggressive filtering
            try:
                simple_lines = []
                for line in content_text.split('\n'):
                    line = line.strip()
                    if len(line) > 10:  # Keep any line with reasonable length
                        simple_lines.append(line)
                
                # Only use this fallback if it gives substantially more content
                if len(simple_lines) > 2 * len(paragraphs):
                    debug_info.append("Using simple fallback extraction")
                    content = '\n\n'.join(simple_lines)
            except Exception as e:
                debug_info.append(f"Error during fallback extraction: {str(e)}")
        
        # Final check - if content is still empty, try direct HTML extraction
        if not content or len(content.strip()) < 100:
            try:
                debug_info.append("Content too short, trying direct HTML extraction")
                # For metruyencv.com, try to find the article content directly
                if 'metruyencv.com' in domain:
                    article_text = ""
                    article = soup.select_one('#article')
                    if article:
                        article_text = article.get_text()
                    
                    if len(article_text) > 100:
                        content = article_text
                        debug_info.append("Extracted content directly from #article")
            except Exception as e:
                debug_info.append(f"Error during direct HTML extraction: {str(e)}")
        
        # Final deep cleaning to remove any remaining noise
        content = deep_clean_content(content, domain, is_novel_site, debug_info)
        
        # Apply Vietnamese novel cleaning for Vietnamese domains
        vietnamese_domains = ['metruyencv.com', 'truyenfull.vn', 'truyenyy.com', 'truyencv.com', 'truyenki.com']
        if any(vn_domain in domain for vn_domain in vietnamese_domains):
            content = clean_vietnamese_novel(content, debug_info)
        
        execution_time = time.time() - start_time
        debug_info.append(f"Extraction completed in {execution_time:.2f} seconds")
        
        # Compile debug information
        debug_text = '\n'.join(debug_info)
        
        # Empty content check
        if not content or len(content.strip()) < 100:
            return "No content found", "No content could be extracted from this URL.", execution_time, debug_text, None, None
            
        return title, content, execution_time, debug_text, prev_chapter_url, next_chapter_url

    except Exception as e:
        execution_time = time.time() - start_time
        debug_info.append(f"ERROR: {str(e)}")
        debug_text = '\n'.join(debug_info)
        return f"Error: {str(e)}", "", execution_time, debug_text, None, None

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
        # Check if the previous URL is from the same problematic domain to preserve settings
        prev_url_domain = urlparse(st.session_state.prev_chapter_url).netloc
        if prev_url_domain == st.session_state.current_domain:
            debug_info = []
            debug_info.append(f"Navigating to previous chapter: {st.session_state.prev_chapter_url}")
            debug_info.append(f"Preserving domain settings for: {prev_url_domain}")
            
            # Store navigation debug info
            if 'navigation_debug' not in st.session_state:
                st.session_state.navigation_debug = []
            st.session_state.navigation_debug = debug_info
        
        # Set the current URL to the previous chapter URL
        st.session_state.current_url = st.session_state.prev_chapter_url
        st.session_state.needs_extraction = True

def navigate_next():
    if st.session_state.next_chapter_url:
        # Check if the next URL is from the same problematic domain to preserve settings
        next_url_domain = urlparse(st.session_state.next_chapter_url).netloc
        if next_url_domain == st.session_state.current_domain:
            debug_info = []
            debug_info.append(f"Navigating to next chapter: {st.session_state.next_chapter_url}")
            debug_info.append(f"Preserving domain settings for: {next_url_domain}")
            
            # Store navigation debug info
            if 'navigation_debug' not in st.session_state:
                st.session_state.navigation_debug = []
            st.session_state.navigation_debug = debug_info
        
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

# Process extraction when needed
if extract_clicked or st.session_state.needs_extraction:
    if not url:
        st.warning("⚠️ Vui lòng nhập URL")
    else:
        # Update current URL in session state
        st.session_state.current_url = url
        st.session_state.needs_extraction = False
        
        # Check if we already have SSL settings for this domain
        parsed_url = urlparse(url)
        current_domain = parsed_url.netloc
        
        # Create navigation debug info
        if 'navigation_debug' not in st.session_state:
            st.session_state.navigation_debug = []
        
        # Update navigation debug info
        if hasattr(st.session_state, 'current_domain') and st.session_state.current_domain == current_domain:
            st.session_state.navigation_debug.append(f"Reusing settings for domain: {current_domain}")
            if "truyensextv" in current_domain:
                st.session_state.navigation_debug.append("This is a domain with known SSL issues")
        
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

# Function to handle text selection for annotations
def on_text_select():
    # This is a placeholder for client-side text selection
    # In Streamlit, we'll need to use a workaround with text interaction
    pass

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
    # Replace pyperclip.copy with Streamlit button
    st.success(f"✅ Đã trích xuất trong {st.session_state.execution_time:.2f} giây")
    
    # Add copy button
    if st.button("📋 Sao chép vào clipboard", key="copy_btn"):
        st.code(st.session_state.content, language=None)
        st.toast("✅ Đã sao chép! Bạn có thể dán nội dung ở nơi khác.")
    
    # Show the content
    with st.expander(f"📖 {st.session_state.title}", expanded=True):
        # Get current annotations for this URL
        annotations = get_annotations(st.session_state.current_url)
        
        # Create a key for tracking content changes for scroll position
        content_key = f"content_{hash(st.session_state.content)}"
        
        # Display the content in a text area - height based on preferences
        content_text_area = st.text_area(
            label="Nội dung",
            value=st.session_state.content,
            height=int(st.session_state.preferences.get("font_size", "16px").replace("px", "")) * 25,
            label_visibility="collapsed",
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
                    
            # Display domain and SSL verification settings
            st.text("\nCurrent Settings:")
            st.text(f"Current domain: {st.session_state.get('current_domain', 'Not set')}")
            st.text(f"SSL verification: {'Disabled' if not st.session_state.get('ssl_verification', True) else 'Enabled'}")
elif url and extract_clicked:
    st.error(f"❌ {st.session_state.title if st.session_state.title else 'Error'}")
    st.info("Không thể trích xuất. Hãy thử URL khác.")
    
    # Always show debug on error
    with st.expander("🔍 Debug Information", expanded=True):
        st.text(st.session_state.debug_text)

# Check if we need to navigate to a stored URL
if st.session_state.current_url and st.session_state.current_url != url and (st.session_state.prev_chapter_url or st.session_state.next_chapter_url):
    # Auto-fill the URL input
    url = st.session_state.current_url
    # Simulate clicking the extract button
    st.experimental_rerun()

# Add a JavaScript injection for advanced UI features
st.markdown("""
<script>
// Script to enable better text selection
document.addEventListener('DOMContentLoaded', function() {
    // Wait for Streamlit to fully load
    setTimeout(() => {
        // Find the text area element
        const textArea = document.querySelector('textarea[aria-label="Nội dung"]');
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
