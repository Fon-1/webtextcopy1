"""
Fixed request handler for the text summarization application.
This file contains a function to fix the timeout handling in the a.py file.
"""

import re
import os
import sys

def fix_timeout_in_file():
    """
    Fix the timeout handling in the a.py file.
    Creates a backup of the original file and writes the fixed version.
    """
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Current directory: {current_dir}")

        # Path to the original file
        original_file = os.path.join(current_dir, "a.py")
        # Path to the backup file
        backup_file = os.path.join(current_dir, "a.py.bak")
        # Path to the fixed file
        fixed_file = os.path.join(current_dir, "a_fixed.py")

        print(f"Reading from: {original_file}")
        print(f"Backup to: {backup_file}")
        print(f"Writing to: {fixed_file}")

        # Check if the original file exists
        if not os.path.exists(original_file):
            print(f"Error: Original file not found at {original_file}")
            return False

        # Create a backup of the original file
        try:
            with open(original_file, 'rb') as src:
                with open(backup_file, 'wb') as dst:
                    dst.write(src.read())
            print(f"Backup created at {backup_file}")
        except Exception as e:
            print(f"Warning: Failed to create backup: {str(e)}")

        # Read the original file
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix approach 1: Find the line with timeout_value assignment and fix the whole block
        # This approach specifically targets the known problematic format with \n characters in the string
        line_to_search = 'timeout_value = st.session_state.get(\'timeout_setting\', 10)'
        if line_to_search in content:
            print(f"Found line with timeout_value assignment: {line_to_search}")
            
            # Find position of the line
            pos = content.find(line_to_search)
            if pos != -1:
                # Find the next line that contains "domain ="
                domain_line_pos = content.find("domain = ", pos)
                
                if domain_line_pos != -1:
                    # Extract everything between these positions
                    old_code = content[pos:domain_line_pos].rstrip()
                    print(f"Found code block to replace:\n{old_code}")
                    
                    # Create the new code to insert
                    new_code = """        # Get the page with reasonable timeout
        timeout_value = st.session_state.get('timeout_setting', 30)  # Default to 30 seconds
        
        # Get website domain for context and specialized handling
        domain = urlparse(url).netloc
        
        # Double-check that a proper timeout value is set, especially for problematic domains
        if "truyensextv" in domain or "metruyencv" in domain:
            if timeout_value < 45:
                timeout_value = 45  # Force minimum 45 seconds for these problematic domains
                debug_info.append(f"Forced minimum timeout value of 45s for problematic domain: {domain}")
        
        debug_info.append(f"Using timeout: {timeout_value}s")
        response = session.get(url, headers=headers, timeout=timeout_value)
        html = response.text
        
        # Set base URL for building links
        base_url = f"{urlparse(url).scheme}://{domain}"""
                    
                    # Replace old code with new code
                    fixed_content = content[:pos] + new_code + content[domain_line_pos + len("domain = "):]
                    
                    # Write the fixed content to the new file
                    with open(fixed_file, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    print(f"Fixed file written to {fixed_file}")
                    print("After verifying the changes, you can replace the original file with the fixed one.")
                    print("Example command: copy /Y a_fixed.py a.py")
                    return True
                else:
                    print("Could not locate the domain line that follows the timeout assignment.")
            else:
                print("Found the line in string comparison but not using .find() - this is strange.")
        else:
            print("Could not find the timeout_value assignment line.")
        
        # Fix approach 2: Try a regex-based approach as a fallback
        print("Trying fallback regex approach...")
        patterns_to_try = [
            r"timeout_value\s*=\s*st\.session_state\.get\('timeout_setting',\s*\d+\).*?response\s*=\s*session\.get\(url,\s*headers=headers,\s*timeout=timeout_value\)",
            r"timeout_value\s*=\s*st\.session_state\.get\('timeout_setting',\s*\d+\).*?\\n\s*response\s*=\s*session\.get",
            r"timeout_value\s*=\s*st\.session_state\.get\('timeout_setting',\s*\d+\)"
        ]
        
        replacement_made = False
        for i, pattern in enumerate(patterns_to_try):
            print(f"Trying pattern {i+1}...")
            if re.search(pattern, content, re.DOTALL):
                print(f"Pattern {i+1} matched!")
                
                # Direct string replacement for the known problematic line
                if i == 2:  # Last pattern (just the timeout_value line)
                    # Get full line
                    lines = content.split('\n')
                    for line_idx, line in enumerate(lines):
                        if line_to_search in line:
                            # Replace all lines from this one until we find the response line
                            response_idx = None
                            for j in range(line_idx, min(line_idx + 10, len(lines))):
                                if "response = session.get" in lines[j]:
                                    response_idx = j
                                    break
                            
                            if response_idx is not None:
                                # Create the new code
                                new_code_lines = [
                                    "        # Get the page with reasonable timeout",
                                    "        timeout_value = st.session_state.get('timeout_setting', 30)  # Default to 30 seconds",
                                    "",
                                    "        # Double-check that a proper timeout value is set, especially for problematic domains",
                                    "        if \"truyensextv\" in domain or \"metruyencv\" in domain:",
                                    "            if timeout_value < 45:",
                                    "                timeout_value = 45  # Force minimum 45 seconds for these problematic domains",
                                    "                debug_info.append(f\"Forced minimum timeout value of 45s for problematic domain: {domain}\")",
                                    "",
                                    "        debug_info.append(f\"Using timeout: {timeout_value}s\")",
                                    "        response = session.get(url, headers=headers, timeout=timeout_value)"
                                ]
                                
                                # Replace the problematic lines
                                lines[line_idx:response_idx+1] = new_code_lines
                                fixed_content = '\n'.join(lines)
                                replacement_made = True
                                break
                else:
                    # For the more complex patterns, attempt a full regex replacement
                    new_timeout_code = """        # Get the page with reasonable timeout
        timeout_value = st.session_state.get('timeout_setting', 30)  # Default to 30 seconds
        
        # Double-check that a proper timeout value is set, especially for problematic domains
        if "truyensextv" in domain or "metruyencv" in domain:
            if timeout_value < 45:
                timeout_value = 45  # Force minimum 45 seconds for these problematic domains
                debug_info.append(f"Forced minimum timeout value of 45s for problematic domain: {domain}")
        
        debug_info.append(f"Using timeout: {timeout_value}s")
        response = session.get(url, headers=headers, timeout=timeout_value)"""
                    
                    fixed_content = re.sub(pattern, new_timeout_code, content, flags=re.DOTALL)
                    if fixed_content != content:
                        replacement_made = True
                        break
            
            if replacement_made:
                break
        
        if replacement_made:
            # Write the fixed content to the new file
            with open(fixed_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"Fixed file written to {fixed_file}")
            print("After verifying the changes, you can replace the original file with the fixed one.")
            print("Example command: copy /Y a_fixed.py a.py")
            return True
        else:
            # Last resort: manual replacement of the specific line with newlines
            problem_line = r"timeout_value = st.session_state.get('timeout_setting', 10)  # Default to 10 seconds if not set\n        debug_info.append(f\"Using timeout: {timeout_value}s\")\n        response = session.get(url, headers=headers, timeout=timeout_value)"
            if problem_line in content:
                print("Found the exact problematic line with newline characters.")
                fixed_content = content.replace(problem_line, """        # Get the page with reasonable timeout
        timeout_value = st.session_state.get('timeout_setting', 30)  # Default to 30 seconds
        
        # Double-check that a proper timeout value is set, especially for problematic domains
        if "truyensextv" in domain or "metruyencv" in domain:
            if timeout_value < 45:
                timeout_value = 45  # Force minimum 45 seconds for these problematic domains
                debug_info.append(f"Forced minimum timeout value of 45s for problematic domain: {domain}")
        
        debug_info.append(f"Using timeout: {timeout_value}s")
        response = session.get(url, headers=headers, timeout=timeout_value)""")
                
                # Write the fixed content to the new file
                with open(fixed_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                print(f"Fixed file written to {fixed_file}")
                print("After verifying the changes, you can replace the original file with the fixed one.")
                print("Example command: copy /Y a_fixed.py a.py")
                return True
            else:
                print("No changes were made to the file. Could not find the timeout pattern.")
                return False

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_timeout_in_file()
    sys.exit(0 if success else 1)
