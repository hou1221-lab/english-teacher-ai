import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import re
import random

# --- 1. 核心設定：解決 404 的關鍵 ---
# 加上 transport="rest" 強制走穩定通道
genai.configure(api_key="AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw", transport="rest")

# 自動偵測模型邏輯
@st.cache_resource
def get_working_model():
    # 按照穩定度測試模型名稱
    models_to_try = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-1.5-pro']
    for m in models_to_try:
        try:
            return genai.GenerativeModel(m)
        except:
            continue
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# Google Sheet 資訊
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 資料處理函數 ---
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        return df.to_dict('records')
    except:
        return []

# 初始化 Session State
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data()
if 'current_q' not in st.session_state:
    st.session_state.current_q = None

# --- 3. 側邊欄導覽 ---
st.sidebar.title("🧑‍🏫 雲端選單")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

if st.sidebar.button("🗑️ 清空暫存單字"):
    st.session_state.word_bank = []
    st.rerun()

# --- 4. 模式切換邏輯 ---

# 模式一：拍照同步
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立雲端題庫")
    st.info(f"🤖 目前使用的 AI 大腦：{model.model_name}")
    
    uploaded_file = st.file_uploader("請上傳單字照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="待辨識照片", use_container_width=True)
        
        if st.button("🚀 開始辨識並同步"):
            with st.spinner('Gemini 老師正在努力看照片...'):
                try:
                    if img.mode != 'RGB': img = img.convert('RGB')
                    prompt = "Analyze image. Return ONLY a JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"
                    response = model.generate_content([prompt, img])
                    
                    # 使用正則表達式抓取 JSON
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        new_words = json.loads(match.group())
                        st.session_state.word_bank = new_words
                        st.success(f"✅ 成功辨識 {len(new_words)} 個單字！")
                        st.table(new_words)
                        st.balloons()
                    else:
                        st.error("AI 回傳格式有誤，請再試一次。")
                except Exception as e:
                    st.error(f"連線失敗：{str(e)}")

# 模式二：拼字挑戰
elif "✍️ Lv1. 拼字大挑戰" in page:
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("題庫空空的，請先去拍照喔！")
    else:
        if st.button("🎯 隨機抽一題") or st.session_state.current_q is None:
            st.session_state.current_q = random.choice(st.session_state.word_bank)
        
        q = st.session_state.current_q
        st.subheader(f"中文意思：{q['definition']}")
        st.write(f"提示：首字母是 **{q['hint']}**，單字長度為 {len(q['word'])} 個字母")
        
        ans = st.text_input("請輸入英文單字：", key="ans_input").strip()
        if st.button("檢查答案"):
            if ans.lower() == q['word'].lower():
                st.success("🎉 太棒了！答對了！")
                st.balloons()
            else:
                st.error(f"差一點點！正確答案是：{q['word']}")

# 模式三：情境測驗
elif "🧠 Lv2. 小六情境測驗" in page:
    st.title("🧠 小六情境測驗")
    if not st.session_state.word_bank:
        st.warning("請先去拍照同步單字。")
    else:
        st.write("🤖 Gemini 老師正在根據你的單字出題...")
        if st.button("🎲 生成情境題目"):
            with st.spinner('出題中...'):
                words_str = ", ".join([w['word'] for w in st.session_state.word_bank[:5]])
                prompt = f"使用這幾個單字：{words_str}，寫一個適合小六學生的英文填空題故事，並提供選項。"
                try:
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error(f"生成失敗：{e}")
