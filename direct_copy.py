import streamlit as st

# Set page config
st.set_page_config(
    page_title="Samsung Mobile Copy Test",
    page_icon="📱",
    layout="wide"
)

# Sample content to copy
content = """This is a test content for copying on Samsung mobile devices.

Testing the copy functionality with multiple lines.
Let's see if this works properly on your Samsung device!
"""

# Main app
st.title("📱 Samsung Mobile Copy Test")

# Display content in simple text area
st.text_area("Content", content, height=200)

# SOLUTION 1: Direct visible text area with clear instructions
st.markdown("""
<style>
.big-copy-area {
    width: 100%;
    height: 200px;
    font-size: 16px;
    padding: 10px;
    border: 2px solid #4CAF50;
    margin-bottom: 10px;
    background-color: #f9f9f9;
}
.copy-instructions {
    background-color: #fffacd;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
    border-left: 5px solid #ffeb3b;
}
</style>

<div class="copy-instructions">
    <h3>How to copy content on Samsung devices:</h3>
    <ol>
        <li>Tap and hold on the text area below</li>
        <li>Select "Select all" from the popup menu</li>
        <li>Tap "Copy" from the popup menu</li>
    </ol>
</div>

<textarea class="big-copy-area" readonly>""" + content + """</textarea>
""", unsafe_allow_html=True)

# SOLUTION 2: Simple Button that uses SelectionRange approach
st.markdown("""
<style>
.simple-copy-btn {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 15px;
    text-align: center;
    display: block;
    font-size: 18px;
    margin: 10px 0;
    cursor: pointer;
    border-radius: 5px;
    width: 100%;
}
.simple-copy-msg {
    color: #4CAF50;
    display: none;
    text-align: center;
    margin-top: 10px;
    font-weight: bold;
}
</style>

<button id="simpleCopyBtn" class="simple-copy-btn">📋 COPY WITH SELECTION RANGE</button>
<div id="simpleCopyMsg" class="simple-copy-msg">✅ Content copied!</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('simpleCopyBtn');
    const msg = document.getElementById('simpleCopyMsg');
    const content = `""" + content.replace('"', '\\"').replace('\n', '\\n') + """`;
    
    if (btn) {
        btn.addEventListener('click', function() {
            // Create visible textarea
            const textarea = document.createElement('textarea');
            textarea.value = content;
            
            // Make it clearly visible
            textarea.style.position = 'fixed';
            textarea.style.top = '50%';
            textarea.style.left = '50%';
            textarea.style.transform = 'translate(-50%, -50%)';
            textarea.style.width = '90%';
            textarea.style.height = '200px';
            textarea.style.zIndex = '9999';
            textarea.style.backgroundColor = 'white';
            textarea.style.border = '2px solid #4CAF50';
            textarea.style.padding = '10px';
            
            document.body.appendChild(textarea);
            
            // Select the text
            textarea.focus();
            textarea.select();
            
            // For Samsung/mobile
            if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
                textarea.setSelectionRange(0, 999999);
                alert("Please use the 'Select All' option that appears, then tap 'Copy'");
            }
            
            // Let the user copy manually
            setTimeout(function() {
                document.body.removeChild(textarea);
                msg.style.display = 'block';
                setTimeout(() => { msg.style.display = 'none'; }, 2000);
            }, 10000);
        });
    }
});
</script>
""", unsafe_allow_html=True)

# SOLUTION 3: Copy button for iOS (may work on some Samsung devices)
st.markdown("""
<style>
.ios-copy-btn {
    background-color: #007AFF;
    color: white;
    border: none;
    padding: 15px;
    text-align: center;
    display: block;
    font-size: 18px;
    margin: 10px 0;
    cursor: pointer;
    border-radius: 5px;
    width: 100%;
}
.ios-copy-msg {
    color: #007AFF;
    display: none;
    text-align: center;
    margin-top: 10px;
    font-weight: bold;
}
</style>

<button id="iosCopyBtn" class="ios-copy-btn">📱 iOS/ALTERNATIVE METHOD</button>
<div id="iosCopyMsg" class="ios-copy-msg">✅ Content copied!</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('iosCopyBtn');
    const msg = document.getElementById('iosCopyMsg');
    const content = `""" + content.replace('"', '\\"').replace('\n', '\\n') + """`;
    
    if (btn) {
        btn.addEventListener('click', function() {
            // Try navigator clipboard
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(content)
                    .then(function() {
                        msg.style.display = 'block';
                        setTimeout(() => { msg.style.display = 'none'; }, 2000);
                    })
                    .catch(function() {
                        // Create invisible textarea
                        const textarea = document.createElement('textarea');
                        textarea.value = content;
                        textarea.style.position = 'absolute';
                        textarea.style.left = '-9999px';
                        document.body.appendChild(textarea);
                        
                        // Try select and execute command
                        textarea.select();
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textarea);
                        
                        if (successful) {
                            msg.style.display = 'block';
                            setTimeout(() => { msg.style.display = 'none'; }, 2000);
                        } else {
                            alert("Automatic copy failed. Please use the first method.");
                        }
                    });
            }
        });
    }
});
</script>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### Instructions")
st.markdown("""
1. **First option**: Use the text area at the top. Tap and hold, then select all and copy.
2. **Second option**: Press the green button, which will show a temporary text area for 10 seconds. Select all text and copy it.
3. **Third option**: Try the blue button, which attempts to use the system clipboard directly.
""") 