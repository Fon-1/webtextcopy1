import streamlit as st
import json
import os
import uuid
import datetime
import logging
from pathlib import Path

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