"""
Special handler for truyensextv.com website.
This script uses multiple approaches to extract content from this problematic site.
"""

import requests
import time
import re
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib3
import socket
import ssl
import http.client
from fake_useragent import UserAgent
import os

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a custom SSL context that ignores certificate errors
custom_context = ssl.create_default_context()
custom_context.check_hostname = False
custom_context.verify_mode = ssl.CERT_NONE

def get_random_user_agent():
    """Generate a random user agent string"""
    try:
        ua = UserAgent()
        return ua.random
    except:
        # Fallback user agents if fake_useragent fails
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
        return random.choice(user_agents)

def extract_with_requests(url, debug_info=None):
    """Try to extract content using requests library with various settings"""
    if debug_info is None:
        debug_info = []
    
    debug_info.append("Attempt 1: Using requests with SSL verification disabled")
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://google.com/',
    }
    
    try:
        session = requests.Session()
        response = session.get(
            url, 
            headers=headers, 
            timeout=60,  # Extended timeout
            verify=False,
            stream=True
        )
        
        content_chunks = []
        for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
            if chunk:
                content_chunks.append(chunk)
        
        html = ''.join(content_chunks) if isinstance(content_chunks[0], str) else b''.join(content_chunks).decode('utf-8', errors='ignore')
        debug_info.append("Successfully retrieved content with requests")
        return html, debug_info
    except Exception as e:
        debug_info.append(f"Error in requests attempt: {str(e)}")
    
    return None, debug_info

def extract_with_urllib3(url, debug_info=None):
    """Try to extract content using urllib3 directly"""
    if debug_info is None:
        debug_info = []
    
    debug_info.append("Attempt 2: Using urllib3 directly")
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path or '/'
        
        http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=30, read=30),
            retries=urllib3.Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            ),
            ssl_context=custom_context
        )
        
        response = http.request(
            'GET',
            url,
            headers={
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            preload_content=False
        )
        
        content_chunks = []
        for chunk in response.stream(8192):
            if chunk:
                content_chunks.append(chunk)
        
        html = b''.join(content_chunks).decode('utf-8', errors='ignore')
        debug_info.append("Successfully retrieved content with urllib3")
        return html, debug_info
    except Exception as e:
        debug_info.append(f"Error in urllib3 attempt: {str(e)}")
    
    return None, debug_info

def extract_with_httplib(url, debug_info=None):
    """Try to extract content using http.client directly"""
    if debug_info is None:
        debug_info = []
    
    debug_info.append("Attempt 3: Using http.client directly")
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path or '/'
        
        # Create a custom HTTPSConnection with our SSL context
        connection = http.client.HTTPSConnection(
            domain, 
            timeout=60,
            context=custom_context
        )
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        connection.request('GET', path, headers=headers)
        response = connection.getresponse()
        
        html = response.read().decode('utf-8', errors='ignore')
        debug_info.append("Successfully retrieved content with http.client")
        return html, debug_info
    except Exception as e:
        debug_info.append(f"Error in http.client attempt: {str(e)}")
    
    return None, debug_info

def extract_using_curl(url, debug_info=None):
    """Try to extract content by executing curl command"""
    if debug_info is None:
        debug_info = []
    
    debug_info.append("Attempt 4: Using curl command")
    
    try:
        # Create a temporary file for the output
        temp_file = f"temp_content_{int(time.time())}.html"
        
        # Construct the curl command with all necessary options
        curl_command = f'curl -s -k -L -A "{get_random_user_agent()}" --connect-timeout 30 --max-time 60 "{url}" > {temp_file}'
        
        # Execute the curl command
        os.system(curl_command)
        
        # Read the content from the temporary file
        with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        
        # Remove the temporary file
        try:
            os.remove(temp_file)
        except:
            pass
        
        if html and len(html) > 100:  # Ensure we got meaningful content
            debug_info.append("Successfully retrieved content with curl")
            return html, debug_info
        else:
            debug_info.append("Curl retrieved empty or too short content")
    except Exception as e:
        debug_info.append(f"Error in curl attempt: {str(e)}")
    
    return None, debug_info

def parse_content(html, url, debug_info=None):
    """Parse the HTML content to extract the article"""
    if debug_info is None:
        debug_info = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_elem = soup.select_one('h1.txt-primary')
        if not title_elem:
            title_elem = soup.select_one('title')
        
        title = title_elem.get_text().strip() if title_elem else "Extracted Content"
        debug_info.append(f"Extracted title: {title}")
        
        # Extract content
        content_elem = soup.select_one('.chapter-c')
        if not content_elem:
            content_elem = soup.select_one('.chapter-content')
        if not content_elem:
            content_elem = soup.select_one('#chapter-content')
        if not content_elem:
            content_elem = soup.select_one('article')
        
        if content_elem:
            # Remove unwanted elements
            for unwanted in content_elem.select('script, style, .ads, .ad-container, .related, .comments'):
                unwanted.decompose()
            
            # Get the text
            paragraphs = content_elem.find_all(['p', 'div'], recursive=False)
            if not paragraphs:
                paragraphs = content_elem.find_all(['p', 'div'])
            
            content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # If still no content, get all text
            if not content:
                content = content_elem.get_text().strip()
            
            debug_info.append(f"Extracted content length: {len(content)} characters")
        else:
            # Fallback: get all text from body
            body = soup.select_one('body')
            content = body.get_text().strip() if body else ""
            debug_info.append(f"Fallback content extraction, length: {len(content)} characters")
        
        # Find navigation links
        next_link = None
        prev_link = None
        
        # Try to find navigation links
        for link in soup.find_all('a'):
            link_text = link.get_text().lower().strip()
            if any(term in link_text for term in ['chương sau', 'tiếp', 'tiếp theo', 'next']):
                next_link = link.get('href')
            elif any(term in link_text for term in ['chương trước', 'trước', 'previous', 'prev']):
                prev_link = link.get('href')
        
        debug_info.append(f"Navigation links - Next: {next_link}, Previous: {prev_link}")
        
        return title, content, prev_link, next_link, debug_info
    except Exception as e:
        debug_info.append(f"Error parsing content: {str(e)}")
        return "Error", f"Failed to parse content: {str(e)}", None, None, debug_info

def extract_from_truyensextv(url):
    """Main function to extract content from truyensextv.com"""
    start_time = time.time()
    debug_info = []
    debug_info.append(f"Starting extraction from: {url}")
    
    # Try multiple methods until one succeeds
    html = None
    
    # Method 1: Requests
    html, debug_info = extract_with_requests(url, debug_info)
    
    # Method 2: urllib3
    if not html:
        html, debug_info = extract_with_urllib3(url, debug_info)
    
    # Method 3: http.client
    if not html:
        html, debug_info = extract_with_httplib(url, debug_info)
    
    # Method 4: curl command
    if not html:
        html, debug_info = extract_using_curl(url, debug_info)
    
    if not html:
        debug_info.append("All extraction methods failed")
        return "Error", "Failed to extract content after multiple attempts", None, None, "\n".join(debug_info), time.time() - start_time
    
    # Parse the content
    title, content, prev_link, next_link, debug_info = parse_content(html, url, debug_info)
    
    execution_time = time.time() - start_time
    debug_info.append(f"Total execution time: {execution_time:.2f} seconds")
    
    return title, content, prev_link, next_link, "\n".join(debug_info), execution_time

if __name__ == "__main__":
    # Test the handler
    url = "https://truyensextv.com/chinh-phuc-gai-dep/3/"
    title, content, prev_link, next_link, debug_text, execution_time = extract_from_truyensextv(url)
    
    print(f"Title: {title}")
    print(f"Content length: {len(content)} characters")
    print(f"Previous link: {prev_link}")
    print(f"Next link: {next_link}")
    print(f"Execution time: {execution_time:.2f} seconds")
    print("\nDebug info:")
    print(debug_text) 