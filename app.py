import streamlit as st
import requests
import json
import base64
from PIL import Image
import io
import re

# --- 1. 核心安全設定 (從保險箱自動取件) ---
# 程式會自動去 Streamlit 或 GitHub 的 Secrets 找這組 Key
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ 找不到 API Key！請確保已在 Streamlit Secrets 設定中加入 GEMINI_API_KEY")
    st.stop()

# 官方正式版入口
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

st.set_page_config(page_title="AI 英文單字掃描器", layout="centered", page_icon="📸")

# --- 2. 圖片處理工具 ---
def img_to_base64(image):
    buffered = io.BytesIO()
    if image.mode != 'RGB': image = image.convert('RGB')
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- 3. 網頁介面 ---
st.title("📸 英文單字掃描器 (安全加密版)")
st.write("現在你的金鑰已受到保護，可以放心上傳單字照片了！")

uploaded_file = st.file_uploader("請選擇單字照片", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="已上傳的照片", use_container_width=True)
    
    if st.button("🚀 開始辨識"):
        with st.spinner('AI 正在透過安全通道讀取中...'):
            try:
                base64_img = img_to_base64(img)
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Read the image. Return ONLY a JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"},
                            {"inline_data": {"mime_type": "image/jpeg", "data": base64_img}}
                        ]
                    }]
                }
                
                response = requests.post(API_URL, json=payload, timeout=15)
                res_json = response.json()
                
                if 'candidates' in res_json:
                    ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
                    match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                    if match:
                        word_list = json.loads(match.group())
                        st.success(f"✅ 成功辨識出 {len(word_list)} 個單字！")
                        st.table(word_list)
                        st.balloons()
                    else:
                        st.error("AI 辨識成功但無法整理成表格。")
                else:
                    st.error(f"連線失敗：{res_json.get('error', {}).get('message', '未知錯誤')}")
            except Exception as e:
                st.error(f"錯誤：{str(e)}")
