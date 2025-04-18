import streamlit as st
import pyperclip

# Simple app to test copy functionality
st.title("Test Copy Functionality")

# Some test content
test_content = """This is a test of the copy functionality.
It should work with multiple lines of text.
Let's see if it works properly!"""

# Display in a text area
st.text_area("Content", test_content, height=200)

# Copy button using pyperclip
if st.button("📋 Copy Content"):
    try:
        pyperclip.copy(test_content)
        st.success("✅ Content copied successfully!")
    except Exception as e:
        st.error(f"Error copying: {str(e)}")
        st.info("Try selecting the text manually and using Ctrl+C/Cmd+C to copy.") 