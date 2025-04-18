import streamlit as st

# Set page config
st.set_page_config(
    page_title="Mobile Copy Button",
    page_icon="📱",
    layout="wide"
)

# Sample content to copy - this would be your extracted content
content = """Chương 111: ( Blue-Eyes Alternative White Dragon ) Burst Stream!

Chương 111: ( Blue-Eyes Alternative White Dragon ) Burst Stream!

Nhìn qua Deep-Eyes White Dragon dáng người, Camula sắc mặt có chút âm tình bất định.

Yuga sử dụng ( Blue-Eyes ) bộ bài, cùng nàng trong tưởng tượng hoàn toàn khác biệt, lại ẩn chứa nàng chưa bao giờ nghe monster.

Nó công thủ trị số cùng hiệu quả, đều là thượng thừa nhất, so với nàng ( Vampire Genesis ) càng thêm cường đại!"""

# Main app - keep it simple
st.title("📋 Sao chép bài viết")

# Create content area first - this is the key part
content_placeholder = st.empty()

# Define the HTML for our simple button
button_html = """
<style>
.mobile-copy-btn {
    background-color: #4CAF50;
    color: white;
    padding: 16px;
    font-size: 18px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    width: 100%;
    margin: 10px 0;
    font-weight: bold;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>

<button id="copyBtn" class="mobile-copy-btn">📋 NHẤN ĐỂ SAO CHÉP</button>
<div id="copySuccess" style="display:none; color:#4CAF50; text-align:center; margin:10px 0; font-weight:bold;">
    ✅ Đã sao chép thành công!
</div>
"""

# Button first
st.markdown(button_html, unsafe_allow_html=True)

# JavaScript with direct assignment of text value (no complex operations)
js = """
<script>
document.getElementById('copyBtn').addEventListener('click', function() {
    // This text value is the exact text to be copied
    var textToCopy = """ + '"' + content.replace('\n', '\\n').replace('"', '\\"') + '"' + """;
    
    // First try: Modern clipboard API (most modern browsers)
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(textToCopy)
            .then(function() {
                showSuccess();
            })
            .catch(function() {
                // If fails, try alternate approaches
                alternateMethod(textToCopy);
            });
    } else {
        // Fallback for older browsers
        alternateMethod(textToCopy);
    }
    
    function alternateMethod(text) {
        // Create visible textarea
        var textarea = document.createElement('textarea');
        textarea.value = text;
        
        // Make it clearly visible on mobile
        textarea.style.position = 'fixed';
        textarea.style.left = '0';
        textarea.style.top = '20%';
        textarea.style.width = '100%';
        textarea.style.height = '100px';
        textarea.style.padding = '10px';
        textarea.style.zIndex = '9999';
        textarea.style.backgroundColor = 'white';
        textarea.style.color = 'black';
        
        document.body.appendChild(textarea);
        
        // Show instructions
        var instructions = document.createElement('div');
        instructions.innerHTML = '<strong>Chọn văn bản và nhấn "Sao chép"</strong>';
        instructions.style.position = 'fixed';
        instructions.style.left = '0';
        instructions.style.top = '10%';
        instructions.style.width = '100%';
        instructions.style.padding = '10px';
        instructions.style.backgroundColor = '#fff3cd';
        instructions.style.color = '#856404';
        instructions.style.textAlign = 'center';
        instructions.style.zIndex = '10000';
        
        document.body.appendChild(instructions);
        
        // Select the text
        textarea.focus();
        textarea.select();
        
        // Add close button
        var closeBtn = document.createElement('button');
        closeBtn.innerText = 'ĐÓNG';
        closeBtn.style.position = 'fixed';
        closeBtn.style.left = '10px';
        closeBtn.style.top = 'calc(20% + 110px)';
        closeBtn.style.padding = '8px 15px';
        closeBtn.style.backgroundColor = '#dc3545';
        closeBtn.style.color = 'white';
        closeBtn.style.border = 'none';
        closeBtn.style.borderRadius = '4px';
        closeBtn.style.zIndex = '10000';
        
        closeBtn.addEventListener('click', function() {
            document.body.removeChild(textarea);
            document.body.removeChild(instructions);
            document.body.removeChild(closeBtn);
            showSuccess();
        });
        
        document.body.appendChild(closeBtn);
    }
    
    function showSuccess() {
        var message = document.getElementById('copySuccess');
        message.style.display = 'block';
        setTimeout(function() {
            message.style.display = 'none';
        }, 2000);
    }
});
</script>
"""

# Add JavaScript
st.markdown(js, unsafe_allow_html=True)

# Display content in a text area for direct selection too
content_placeholder.text_area("Nội dung", value=content, height=300)

# Simple instruction
st.info("Nhấn nút xanh phía trên để sao chép nội dung")

# Option to download as failsafe
st.download_button(
    label="💾 TẢI VỀ DẠNG TXT (nếu không sao chép được)",
    data=content,
    file_name="content.txt",
    mime="text/plain"
) 