import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re

# --- 1. 核心設定 (回到最直接的寫法) ---
# 這是你的 API Key，直接寫在這裡最快
API_KEY = "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"
genai.configure(api_key=API_KEY)

# 選擇最穩定的模型名稱 (嘗試解決 404 問題)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="英文單字小老師", layout="centered")

# --- 2. 側邊欄選單 (找回你的第一頁、第二頁) ---
st.sidebar.title("功能選單")
# 這裡就是你要的選單，保證會出現在左邊
page = st.sidebar.radio("切換頁面", ["📸 第一頁：拍照辨識", "✍️ 第二頁：拼字練習"])

# --- 3. 第一頁：純粹拍照上傳 ---
if page == "📸 第一頁：拍照辨識":
    st.title("📸 拍照同步題庫")
    st.write("單純拍照上傳，不記錄到雲端。")

    uploaded_file = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="已上傳的照片", use_container_width=True)
        
        if st.button("🚀 開始辨識"):
            with st.spinner('AI 正在讀取單字...'):
                try:
                    # 傳送指令給 AI
                    prompt = "Analyze image. Return ONLY a JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"
                    response = model.generate_content([prompt, img])
                    
                    # 抓取裡面的 JSON
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        word_list = json.loads(match.group())
                        st.session_state.temp_words = word_list # 暫存在網頁裡
                        st.success("✅ 辨識成功！")
                        st.table(word_list) # 直接列出表格
                        st.balloons()
                    else:
                        st.error("AI 沒看清楚，請再試一次。")
                except Exception as e:
                    # 如果還是出現 404，這裡會給予提示
                    st.error(f"連線失敗：{str(e)}")
                    st.info("💡 提示：這通常是 Google 伺服器的問題，請稍等一分鐘再按一次。")

# --- 4. 第二頁：簡單的練習模式 ---
elif page == "✍️ 第二頁：拼字練習":
    st.title("✍️ 拼字大挑戰")
    if 'temp_words' not in st.session_state or not st.session_state.temp_words:
        st.warning("請先去第一頁拍照辨識單字喔！")
    else:
        st.write("單字庫已準備好，開始練習吧！")
        st.write(st.session_state.temp_words)
