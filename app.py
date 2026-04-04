import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import random
import pandas as pd
import re # 新增：用來過濾雜訊

# --- 1. 核心設定 ---
genai.configure(api_key="AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw")
model = genai.GenerativeModel('gemini-1.5-flash')

SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 雲端同步邏輯 ---
def load_data_from_sheets():
    try:
        df = pd.read_csv(CSV_URL)
        return df.to_dict('records')
    except:
        return []

if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data_from_sheets()
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = {}

# --- 側邊欄 ---
st.sidebar.title("🧑‍🏫 Gemini 雲端導覽")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

# --- 第一頁：拍照同步 (修復版) ---
if page == "📸 拍照同步題庫":
    st.title("📸 拍照建立雲端單字庫")
    uploaded_file = st.file_uploader("請上傳單字照片", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="待辨識照片", use_column_width=True)
        
        if st.button("🚀 開始辨識並同步到雲端"):
            with st.spinner('Gemini 老師正在拼命看照片中...'):
                try:
                    # 強制轉成 RGB 格式防止 PNG 報錯
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    prompt = "請精確讀取圖片中的英文單字與中文。只回傳 JSON 陣列格式，不要說任何廢話。格式：[{'word':'英文','definition':'中文','hint':'首字母'}]"
                    response = model.generate_content([prompt, img])
                    
                    # 強力解析邏輯：只抓取 [] 之間的內容
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        raw_json = match.group()
                        new_words = json.loads(raw_json)
                        st.session_state.word_bank = new_words
                        st.session_state.quiz_data = [] 
                        st.success(f"✅ 成功辨識 {len(new_words)} 個單字！")
                        st.balloons()
                    else:
                        st.error("AI 回傳格式不正確，請再試一次。")
                except Exception as e:
                    st.error(f"辨識出錯了：{str(e)}")

# --- Lv1 & Lv2 邏輯保持不變 (略，請參考前一份程式碼補齊，或直接覆蓋全部) ---
# ... (此處省略後續練習代碼以節省篇幅，請記得補上)
