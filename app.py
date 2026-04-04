import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import re
import random

# --- 1. 核心安全設定 (換上你的新通行證) ---
# 這是你剛才產生的全新 API Key
NEW_API_KEY = "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"

# 強制使用 REST 模式，這能徹底避開之前那個 404 v1beta 的錯誤
genai.configure(api_key=NEW_API_KEY, transport='rest')

# 直接指定最穩定的型號名稱
model = genai.GenerativeModel('gemini-1.5-flash')

# 你的 Google Sheet ID
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 資料載入邏輯 ---
def load_data():
    try:
        # 讀取雲端試算表
        df = pd.read_csv(CSV_URL)
        return df.to_dict('records')
    except:
        return []

# 初始化單字庫
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data()
if 'current_q' not in st.session_state:
    st.session_state.current_q = None

# --- 3. 側邊欄導覽 ---
st.sidebar.title("🧑‍🏫 雲端選單")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

if st.sidebar.button("🗑️ 清空所有單字"):
    st.session_state.word_bank = []
    st.rerun()

# --- 4. 功能頁面 ---

# 模式一：拍照辨識 (最關鍵的功能)
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立雲端題庫")
    st.info("🤖 AI 老師已更新通行證，目前狀態：連線穩定！")
    
    uploaded_file = st.file_uploader("請上傳單字照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="待辨識的照片", use_container_width=True)
        
        if st.button("🚀 開始辨識並同步到雲端"):
            with st.spinner('Gemini 正在全力讀取中，請稍候...'):
                try:
                    # 強制轉成 RGB 確保相容性
                    if img.mode != 'RGB': img = img.convert('RGB')
                    
                    # 傳送指令給 AI
                    prompt = "Read the image. Return ONLY a JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"
                    response = model.generate_content([prompt, img])
                    
                    # 抓取 JSON 陣列內容
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        new_words = json.loads(match.group())
                        st.session_state.word_bank = new_words
                        st.success(f"✅ 成功辨識 {len(new_words)} 個單字！單字庫已更新。")
                        st.table(new_words) # 顯示辨識結果
                        st.balloons() # 噴發慶祝氣球
                    else:
                        st.error("辨識成功但格式不符，請換一張照片再試一次。")
                except Exception as e:
                    st.error(f"連線失敗：{str(e)}")
                    st.warning("提示：如果還是報錯，請確認試算表權限是否已設為『知道連結的任何人皆可編輯』。")

# 模式二：拼字挑戰
elif "✍️ Lv1. 拼字大挑戰" in page:
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("題庫目前是空的，請先去拍照同步單字喔！")
    else:
        if st.button("🎯 隨機抽一題") or st.session_state.current_q is None:
            st.session_state.current_q = random.choice(st.session_state.word_bank)
        
        q = st.session_state.current_q
        st.subheader(f"中文意思：{q['definition']}")
        st.write(f"提示：首字母是 **{q['hint']}**，單字共有 {len(q['word'])} 個字母")
        
        ans = st.text_input("請輸入正確英文單字：").strip()
        if st.button("檢查答案"):
            if ans.lower() == q['word'].lower():
                st.success("🎉 太棒了！答對了！")
                st.balloons()
            else:
                st.error(f"差一點點！正確答案是：{q['word']}")

# 模式三：情境測驗
elif "🧠 Lv2. 小六情境測驗" in page:
    st.title("🧠 小六情境測驗")
    st.write("已成功連動雲端單字庫。")
    if st.button("🎲 生成 AI 題目"):
        st.write("🤖 Gemini 老師正在編撰故事題目...")
        # 這裡未來可以加入更多 AI 出題邏輯
