import streamlit as st
import requests
import json
import base64
from PIL import Image
import io
import re

# --- 1. 核心安全設定 ---
# 這是你的 API Key
API_KEY = "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"

# 直接使用官方正式版入口，避開 404 錯誤
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

st.set_page_config(page_title="AI 英文單字掃描器", layout="centered", page_icon="📸")

# --- 2. 圖片處理工具 ---
def img_to_base64(image):
    buffered = io.BytesIO()
    if image.mode != 'RGB': image = image.convert('RGB')
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- 3. 網頁介面 ---
st.title("📸 英文單字即時掃描器")
st.write("上傳課本、講義照片，AI 會立刻幫你翻譯並整理成表格。")

# 側邊欄：簡單的說明
with st.sidebar:
    st.header("使用說明")
    st.write("1. 上傳含英文單字的照片")
    st.write("2. 點擊開始辨識")
    st.write("3. 直接查看整理結果")
    if st.button("🗑️ 重新開始"):
        st.rerun()

# 模式：拍照辨識
uploaded_file = st.file_uploader("請選擇單字照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # 顯示上傳的照片
    img = Image.open(uploaded_file)
    st.image(img, caption="已上傳的照片", use_container_width=True)
    
    if st.button("🚀 讓 AI 開始辨識"):
        with st.spinner('AI 老師正在讀取中...'):
            try:
                # 準備傳送給 Google 的資料
                base64_img = img_to_base64(img)
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Read the English words and Chinese meanings from the image. Return ONLY a plain JSON list like this: [{'word':'英文單字','definition':'中文意思','hint':'首字母'}]"},
                            {"inline_data": {"mime_type": "image/jpeg", "data": base64_img}}
                        ]
                    }]
                }
                
                # 直接向 Google 請求
                response = requests.post(API_URL, json=payload, timeout=15)
                res_json = response.json()
                
                # 解析 AI 回傳的文字
                if 'candidates' in res_json:
                    ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # 抓取其中的 JSON 陣列
                    match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                    if match:
                        word_list = json.loads(match.group())
                        
                        st.success(f"✅ 成功辨識出 {len(word_list)} 個單字！")
                        # 直接把結果顯示成表格
                        st.table(word_list)
                        st.balloons()
                    else:
                        st.error("AI 讀取到了文字，但無法整理成表格，請換一張更清晰的照片。")
                else:
                    # 如果 Google 報錯，顯示詳細訊息
                    error_msg = res_json.get('error', {}).get('message', '未知連線錯誤')
                    st.error(f"連線失敗：{error_msg}")
                    st.info("💡 建議：點擊左側的『重新開始』並再次嘗試。")
                    
            except Exception as e:
                st.error(f"程式發生錯誤：{str(e)}")
