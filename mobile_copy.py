import streamlit as st
import json

# Set up basic streamlit configuration
st.set_page_config(page_title="Mobile Copy Test", page_icon="📱", layout="wide")

# Sample content to copy
if "content" not in st.session_state:
    st.session_state.content = """This is a test content for copying on mobile devices.
    
It contains multiple lines and paragraphs to test how well the copy functionality works with longer content.

Sometimes mobile browsers have restrictions on clipboard access for security reasons, but our implementation tries several methods to make copying work reliably across different devices and browsers.

Let's see if this works on your mobile device!"""

st.title("📱 Mobile Copy Test")

# Display content in a text area
content_area = st.text_area("Content", st.session_state.content, height=300)

# Mobile-optimized copy button
st.markdown(
    f"""
    <style>
    .mobile-copy-container {{
        margin: 15px 0;
    }}
    .mobile-copy-btn {{
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 15px 20px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-size: 18px;
        font-weight: bold;
        margin: 0 auto;
        cursor: pointer;
        border-radius: 8px;
        width: 100%;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s;
        position: relative;
        overflow: hidden;
    }}
    .mobile-copy-btn:active {{
        background-color: #3e8e41;
        transform: translateY(2px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .copy-feedback {{
        display: none;
        color: #4CAF50;
        text-align: center;
        margin-top: 10px;
        font-weight: bold;
    }}
    .copy-fallback {{
        margin-top: 10px;
        padding: 10px;
        background-color: #f8f9fa;
        border-left: 4px solid #ffc107;
        display: none;
    }}
    </style>
    
    <div class="mobile-copy-container">
        <button id="mobileCopyBtn" class="mobile-copy-btn" onclick="copyMobileText()">📋 SAO CHÉP TOÀN BỘ NỘI DUNG</button>
        <p id="copyFeedback" class="copy-feedback">✅ Đã sao chép nội dung!</p>
        <div id="copyFallback" class="copy-fallback">
            <p>Không thể sao chép tự động. Vui lòng:</p>
            <ol>
                <li>Nhấp vào vùng văn bản phía trên</li>
                <li>Nhấn giữ và chọn "Chọn tất cả" hoặc "Select All"</li>
                <li>Nhấn "Sao chép" hoặc "Copy"</li>
            </ol>
        </div>
    </div>
    
    <script>
    function copyMobileText() {{
        // Get content to copy
        const content = {json.dumps(st.session_state.content)};
        
        // Visual feedback on button press
        const btn = document.getElementById('mobileCopyBtn');
        const feedback = document.getElementById('copyFeedback');
        const fallback = document.getElementById('copyFallback');
        
        // Button animation
        btn.style.backgroundColor = '#3e8e41';
        setTimeout(() => {{ btn.style.backgroundColor = '#4CAF50'; }}, 200);
        
        let copySuccess = false;
        
        // Try multiple approaches for better device compatibility
        
        // Approach 1: Modern Clipboard API - Best for newer browsers
        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(content)
                .then(() => {{
                    copySuccess = true;
                    showSuccess();
                }})
                .catch(err => {{
                    console.error('Clipboard API failed:', err);
                    // Try approach 2
                    useExecCommand();
                }});
        }} else {{
            // Approach 2: execCommand - Works on many older browsers
            useExecCommand();
        }}
        
        function useExecCommand() {{
            try {{
                // Create a temporary textarea element and add to DOM
                const tempTextArea = document.createElement('textarea');
                tempTextArea.value = content;
                
                // Critical styles for mobile
                tempTextArea.style.position = 'fixed';
                tempTextArea.style.left = '0';
                tempTextArea.style.top = '0';
                tempTextArea.style.opacity = '0';
                tempTextArea.style.width = '100%';
                tempTextArea.style.height = '100%';
                tempTextArea.style.padding = '0';
                tempTextArea.style.margin = '0';
                tempTextArea.style.border = 'none';
                
                // iOS-specific attributes
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
                if (isIOS) {{
                    tempTextArea.contentEditable = true;
                    tempTextArea.readOnly = false;
                }}
                
                document.body.appendChild(tempTextArea);
                
                // Select the text
                tempTextArea.focus();
                tempTextArea.select();
                
                // iOS extra handling
                if (isIOS) {{
                    const range = document.createRange();
                    range.selectNodeContents(tempTextArea);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                    tempTextArea.setSelectionRange(0, 999999);
                }}
                
                // Execute copy command
                const successful = document.execCommand('copy');
                if (successful) {{
                    copySuccess = true;
                    showSuccess();
                }} else {{
                    showFallback();
                }}
                
                // Clean up
                document.body.removeChild(tempTextArea);
                
            }} catch (err) {{
                console.error('execCommand failed:', err);
                showFallback();
            }}
        }}
        
        // Approach 3: Manual textarea selection - last resort
        if (!copySuccess) {{
            try {{
                // Try to find and select the visible textarea
                const textarea = document.querySelector('textarea');
                if (textarea) {{
                    textarea.focus();
                    textarea.select();
                    
                    if (isIOS) {{
                        textarea.setSelectionRange(0, 999999);
                    }}
                    
                    // Execute copy command
                    const successful = document.execCommand('copy');
                    if (successful) {{
                        copySuccess = true;
                        showSuccess();
                    }} else {{
                        showFallback();
                    }}
                }} else {{
                    showFallback();
                }}
            }} catch (err) {{
                console.error('Textarea selection failed:', err);
                showFallback();
            }}
        }}
        
        function showSuccess() {{
            feedback.style.display = 'block';
            fallback.style.display = 'none';
            setTimeout(() => {{ feedback.style.display = 'none'; }}, 2000);
        }}
        
        function showFallback() {{
            feedback.style.display = 'none';
            fallback.style.display = 'block';
        }}
    }}
    </script>
    """,
    unsafe_allow_html=True
)

# Also provide a download button as an alternative
st.download_button(
    label="💾 Tải về dạng TXT",
    data=st.session_state.content,
    file_name="content.txt",
    mime="text/plain"
)

# Instructions
st.markdown("""
### Instructions:
1. Click the green button to copy the content
2. If it works, you'll see a success message
3. If it doesn't work automatically, follow the fallback instructions that appear
4. Try on different mobile browsers (Chrome, Safari, etc.) to see which works best
""")

# Run with: streamlit run mobile_copy.py 