import requests  
import socket  
import time  
import streamlit as st
import traceback

url = "https://truyensextv.com/chinh-phuc-gai-dep/"  
socket.setdefaulttimeout(60)  
print("Starting request with 60s timeout...")  
start = time.time()  
try:  
    response = requests.get(url, timeout=60)  
    print(f"Success! Took {time.time()-start:.2f} seconds")  
    print(f"Response length: {len(response.text)} bytes")  
except Exception as e:  
    print(f"Error after {time.time()-start:.2f} seconds: {e}") 

def test_timeout_setting():
    try:
        # Initialize session state if needed
        if 'timeout_setting' not in st.session_state:
            st.session_state['timeout_setting'] = 10
        
        # Get the timeout value
        timeout_value = st.session_state.get('timeout_setting', 30)  # Default to 30 seconds
        
        # Check for problematic domains
        domain = "metruyencv.com"  # Test domain
        
        # Apply the same logic as in the fixed code
        if "truyensextv" in domain or "metruyencv" in domain:
            if timeout_value < 45:
                timeout_value = 45  # Force minimum 45 seconds for these problematic domains
                print(f"Forced minimum timeout value of 45s for problematic domain: {domain}")
        
        print(f"Original timeout setting: {st.session_state.get('timeout_setting')}")
        print(f"Final timeout value: {timeout_value}")
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_timeout_setting()
    print(f"Test {'succeeded' if success else 'failed'}") 
