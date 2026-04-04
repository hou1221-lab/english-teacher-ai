import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import re
import random

# --- 1. 核心安全設定 (最穩定版本) ---
# 這是你的 API Key
API_KEY = "AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw"

# 強制指定穩定通訊協定，避開 v1beta 錯誤
genai.configure(api_key=API_KEY, transport='rest')

# 這裡不加 models/ 前綴，直接使用模型名稱，這是解決 404 的常見偏方
model = genai.GenerativeModel('gemini-1.5-flash')

# 你的 Google Sheet ID
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 資料處理 ---
def load_data():
    try:
        return pd.read_csv(CSV_URL).to_dict('records')
    except:
        return []

if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data()
if 'current_q' not in st.session_state:
    st.session_state.current_q = None

# --- 3. 側邊欄導覽 ---
st.sidebar.title("🧑‍🏫 雲端選單")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

if st.sidebar.button("🗑️ 清空暫存資料"):
    st.session_state.word_bank = []
    st.rerun()

# --- 4. 功能邏輯 ---

# 模式一：拍照辨識
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立雲端題庫")
    st.info(f"🤖 AI 狀態：{model.model_name} (穩定模式)")
    
    uploaded_file = st.file_uploader("請上傳單字照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        
        if st.button("🚀 開始辨識"):
            with st.spinner('正在強制連線 Google 穩定伺服器...'):
                try:
                    if img.mode != 'RGB': img = img.convert('RGB')
                    # 提示詞簡化，減少 AI 亂回傳的機率
                    prompt = "List English words and Chinese meanings from image as JSON: [{'word':'...', 'definition':'...', 'hint':'...'}]"
                    response = model.generate_content([prompt, img])
                    
                    # 使用正則抓取 JSON 陣列
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        st.session_state.word_bank = json.loads(match.group())
                        st.success(f"✅ 成功辨識 {len(st.session_state.word_bank)} 個單字！")
                        st.table(st.session_state.word_bank)
                        st.balloons()
                    else:
                        st.error("AI 辨識成功但回傳格式有誤，請再試一次。")
                except Exception as e:
                    st.error(f"連線失敗 (404/500)：{str(e)}")
                    st.warning("💡 如果持續失敗，請檢查 Google AI Studio 的 API Key 狀態。")

# 模式二：拼字挑戰
elif "✍️ Lv1. 拼字大挑戰" in page:
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("題庫空空的，請先去拍照喔！")
    else:
        if st.button("🎯 隨機抽題") or st.session_state.current_q is None:
            st.session_state.current_q = random.choice(st.session_state.word_bank)
        
        q = st.session_state.current_q
        st.subheader(f"中文意思：{q['definition']}")
        st.write(f"提示：首字母 **{q['hint']}**，長度 {len(q['word'])}")
        
        user_ans = st.text_input("請輸入單字：").strip()
        if st.button("檢查答案"):
            if user_ans.lower() == q['word'].lower():
                st.success("🎉 答對了！")
                st.balloons()
            else:
                st.error(f"再接再厲！答案是：{q['word']}")

# 模式三：情境測驗
elif "🧠 Lv2. 小六情境測驗" in page:
    st.title("🧠 情境測驗")
    st.write("已連動雲端單字庫。")
    if st.button("🎲 生成 AI 題目"):
        st.info("AI 正在根據你的單字編故事中...")
