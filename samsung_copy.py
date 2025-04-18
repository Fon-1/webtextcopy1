import streamlit as st

# Set page config
st.set_page_config(
    page_title="Samsung S21 Copy Test",
    page_icon="📱",
    layout="wide"
)

# Sample content to copy
content = """Chương 111: ( Blue-Eyes Alternative White Dragon ) Burst Stream!

Chương 111: ( Blue-Eyes Alternative White Dragon ) Burst Stream!

Nhìn qua Deep-Eyes White Dragon dáng người, Camula sắc mặt có chút âm tình bất định.

Yuga sử dụng ( Blue-Eyes ) bộ bài, cùng nàng trong tưởng tượng hoàn toàn khác biệt, lại ẩn chứa nàng chưa bao giờ nghe monster.

Nó công thủ trị số cùng hiệu quả, đều là thượng thừa nhất, so với nàng ( Vampire Genesis ) càng thêm cường đại!"""

# Main app
st.title("📱 Samsung S21 Copy Test")

# Display content in a text area - this is the simplest method
st.subheader("Cách 1: Chọn và sao chép từ vùng văn bản")
st.text_area("Nội dung văn bản", content, height=300, key="content_area")

st.info("""
👆 Hướng dẫn:
1. Nhấn và giữ vào vùng văn bản ở trên
2. Chọn "Chọn tất cả" hoặc "Select all" 
3. Nhấn "Sao chép" hoặc "Copy"
""")

# Provide direct download as most reliable option
st.subheader("Cách 2: Tải về thành tệp văn bản")
st.download_button(
    label="💾 TẢI VỀ DẠNG TXT",
    data=content,
    file_name="content.txt",
    mime="text/plain",
    use_container_width=True
)

# Add a separate copy method using components
st.subheader("Cách 3: Sử dụng nút sao chép (thử nghiệm)")

# Convert newlines to HTML breaks and escape quotes
html_content = content.replace("\n", "<br>").replace('"', "&quot;")

# Create HTML with pure string concatenation (no f-strings)
html = """
<style>
.copy-button {
    background-color: #4CAF50;
    color: white;
    padding: 15px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 10px 0;
    cursor: pointer;
    border-radius: 4px;
    border: none;
    width: 100%;
    font-weight: bold;
}
.content-display {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 15px;
    margin: 10px 0;
    background-color: #f9f9fa;
}
</style>

<div class="content-display">
""" + html_content + """
</div>

<button class="copy-button" onclick="copyToClipboard()">📋 NHẤN ĐỂ SAO CHÉP</button>
<div id="copy-message" style="display:none; color:green; text-align:center; margin:10px 0;">✅ Đã sao chép thành công!</div>

<script>
function copyToClipboard() {
    // Create a temporary textarea
    var tempInput = document.createElement("textarea");
    tempInput.value = document.querySelector('.content-display').innerText;
    document.body.appendChild(tempInput);
    
    // Select the text
    tempInput.select();
    tempInput.setSelectionRange(0, 99999);
    
    // Try to copy
    var success = false;
    try {
        success = document.execCommand('copy');
    } catch (err) {
        console.error('Không thể sao chép: ', err);
    }
    
    // Remove the temporary element
    document.body.removeChild(tempInput);
    
    // Show success message
    if (success) {
        var message = document.getElementById('copy-message');
        message.style.display = 'block';
        setTimeout(function() {
            message.style.display = 'none';
        }, 2000);
    }
}
</script>
"""

st.markdown(html, unsafe_allow_html=True)

# Add an extremely simple static version
st.subheader("Cách 4: Chọn văn bản bằng ngón tay")

static_html = """
<style>
.static-text-box {
    border: 2px solid #007bff;
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    background-color: white;
}
</style>

<div class="static-text-box">
"""

# Add each line separately to avoid any f-string issues
for line in content.split("\n"):
    static_html += line + "<br>"

static_html += """
</div>
<p style="color: #6c757d; font-style: italic; margin-top: 10px;">Nhấn giữ vào văn bản trên, chọn tất cả và nhấn sao chép</p>
"""

st.markdown(static_html, unsafe_allow_html=True)

st.markdown("""
---
### Mẹo:
- Thử từng cách một cho đến khi tìm được cách hiệu quả nhất trên thiết bị của bạn
- Cách 1 và 4 thường hoạt động tốt nhất trên Samsung S21
- Cách 2 luôn luôn hoạt động nhưng cần tải file về
""") 