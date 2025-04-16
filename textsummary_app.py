import streamlit as st
import requests
from bs4 import BeautifulSoup
import ollama

# Constants
MODEL = "llama2-uncensored"  # Đổi sang model llama3.2

# Lớp để trích xuất nội dung từ website
class Website:
    def __init__(self, url):
        """Tải nội dung từ URL và trích xuất văn bản cần thiết"""
        self.url = url
        try:
            response = requests.get(url, timeout=1)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.text = f"Lỗi khi tải trang web: {e}"
            self.title = "Lỗi"
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "Không tìm thấy tiêu đề"

        # Loại bỏ các phần không cần thiết
        for tag in soup(["script", "style", "img", "input", "iframe", "nav", "footer"]):
            tag.decompose()

        # Trích xuất nội dung từ thẻ <p> và <article>
        paragraphs = soup.find_all(['p', 'article'])
        self.text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

# Prompt hệ thống - Không yêu cầu tóm tắt
system_prompt = (
    "Bạn là một AI chuyên trích xuất nội dung từ một trang web. "
    "Trả về toàn bộ nội dung một cách trung thực mà không thực hiện bất kỳ chỉnh sửa hay tóm tắt nào. "
    "Không thêm nhận xét, không diễn giải, chỉ hiển thị nội dung gốc như đã có trên trang web."
)

# Hàm tạo prompt người dùng
def user_prompt_for(website):
    return (
        f"Dưới đây là nội dung từ trang web '{website.title}'. "
        "Hãy trả về toàn bộ nội dung này một cách nguyên bản, không chỉnh sửa:\n\n"
        + website.text
    )

# Hàm xử lý Ollama
def extract_content(url):
    try:
        website = Website(url)
        if "Lỗi khi tải trang web" in website.text:
            return website.text  # Trả về lỗi nếu có
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for(website)}
        ]
        response = ollama.chat(model=MODEL, messages=messages)
        return response['message']['content']
    except Exception as e:
        return f"Lỗi xử lý: {e}"

# Giao diện Streamlit
st.set_page_config(page_title="Trích Xuất Nội Dung Trang Web", layout="wide")
st.title("Trích Xuất Nội Dung Website (Không Tóm Tắt)")

st.markdown("Nhập URL để lấy toàn bộ nội dung có thể đọc được của trang web.")

url = st.text_input("Nhập URL:", "")

if st.button("Trích xuất nội dung"):
    if url:
        with st.spinner("Đang trích xuất nội dung..."):
            content = extract_content(url)
        st.markdown(content)
    else:
        st.warning("Vui lòng nhập một URL hợp lệ.")
