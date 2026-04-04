import streamlit as st
import random
import pandas as pd
import re

# =========================================
# 1. 基本設定
# =========================================
st.set_page_config(page_title="孩子英文學習機", layout="centered", page_icon="📝")

st.markdown("""
    <style>
    .stTextInput input {
        font-size: 30px !important;
        height: 60px !important;
        font-weight: bold !important;
    }
    .big-font {
        font-size: 32px !important;
        font-weight: bold !important;
        line-height: 1.5;
    }
    div[data-baseweb="radio"] label {
        font-size: 24px !important;
        font-weight: bold !important;
    }
    textarea {
        font-size: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================
# 2. 初始化題庫
# =========================================
if "word_bank" not in st.session_state:
    st.session_state.word_bank = []

# =========================================
# 3. 工具函式
# =========================================
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())

def deduplicate_words(word_list):
    seen = set()
    result = []
    for item in word_list:
        word = clean_text(item.get("word", "")).lower()
        definition = clean_text(item.get("definition", ""))
        if word and definition:
            key = (word, definition)
            if key not in seen:
                seen.add(key)
                result.append({"word": word, "definition": definition})
    return result

def parse_bulk_text(text):
    """
    支援格式：
    apple 蘋果
    banana 香蕉
    orange 橘子

    或
    apple,蘋果
    banana,香蕉
    """
    results = []
    lines = text.split("\n")

    for line in lines:
        line = clean_text(line)
        if not line:
            continue

        # 優先支援逗號分隔
        if "," in line:
            parts = [x.strip() for x in line.split(",", 1)]
        else:
            parts = line.split(" ", 1)

        if len(parts) == 2:
            eng = clean_text(parts[0]).lower()
            chi = clean_text(parts[1])

            if eng and chi:
                results.append({"word": eng, "definition": chi})

    return deduplicate_words(results)

def get_hint(word):
    if len(word) <= 1:
        return word
    return f"{word[0]} " + " ".join(["_"] * (len(word) - 1))

def make_choice_list(correct_value, pool, key_name):
    others = [item[key_name] for item in pool if item[key_name] != correct_value]
    distractors = random.sample(others, min(3, len(others)))
    choices = distractors + [correct_value]
    random.shuffle(choices)
    return choices

# =========================================
# 4. 側邊欄
# =========================================
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio("切換頁面", [
    "📝 家長建立題庫",
    "✍️ 第一頁：中文提示拼英文",
    "🎯 第二頁：英文選中文",
    "🧠 第三頁：題庫總複習"
])

if st.sidebar.button("🗑️ 重設全部題庫"):
    st.session_state.word_bank = []
    st.rerun()

# =========================================
# 5. 家長建立題庫
# =========================================
if page == "📝 家長建立題庫":
    st.title("📝 家長建立題庫")
    st.write("這一版不使用 AI 辨識。請直接手動輸入，或一次貼上整批單字。")

    tab1, tab2 = st.tabs(["單筆輸入", "整批貼上"])

    with tab1:
        with st.form("single_add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                eng = st.text_input("英文單字")
            with c2:
                chi = st.text_input("中文意思")

            submitted = st.form_submit_button("➕ 加入題庫")
            if submitted:
                eng = clean_text(eng).lower()
                chi = clean_text(chi)

                if eng and chi:
                    st.session_state.word_bank.append({
                        "word": eng,
                        "definition": chi
                    })
                    st.session_state.word_bank = deduplicate_words(st.session_state.word_bank)
                    st.success(f"已加入：{eng} / {chi}")
                else:
                    st.error("英文和中文都不能空白。")

    with tab2:
        st.write("請一行一筆，例如：")
        st.code("apple 蘋果\nbanana 香蕉\norange 橘子")
        st.write("也支援逗號格式：")
        st.code("apple,蘋果\nbanana,香蕉")

        bulk_text = st.text_area("請貼上單字表", height=220, placeholder="apple 蘋果\nbanana 香蕉")
        if st.button("📥 匯入整批單字"):
            parsed = parse_bulk_text(bulk_text)
            if parsed:
                st.session_state.word_bank.extend(parsed)
                st.session_state.word_bank = deduplicate_words(st.session_state.word_bank)
                st.success(f"成功匯入 {len(parsed)} 筆單字。")
            else:
                st.error("格式不正確，請用「英文 空格 中文」或「英文,中文」。")

    st.subheader("📋 目前題庫清單")
    if st.session_state.word_bank:
        df = pd.DataFrame(st.session_state.word_bank)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前還沒有單字。")

# =========================================
# 6. 第一頁：中文提示拼英文
#    例：蘋果 -> a _ _ _ _
# =========================================
elif page == "✍️ 第一頁：中文提示拼英文":
    st.title("✍️ 中文提示拼英文")

    if not st.session_state.word_bank:
        st.warning("⚠️ 題庫空空的，請家長先建立題庫。")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>",
                unsafe_allow_html=True
            )

            hint = get_hint(item["word"])
            ans = st.text_input(f"提示：{hint}", key=f"spell_{i}").strip().lower()

            if ans:
                if ans == item["word"]:
                    st.success("✨ 正確！")
                else:
                    st.error("再試一次喔！")

# =========================================
# 7. 第二頁：英文選中文
#    例：apple -> 選 蘋果
# =========================================
elif page == "🎯 第二頁：英文選中文":
    st.title("🎯 英文選中文")

    if len(st.session_state.word_bank) < 2:
        st.warning("⚠️ 至少要 2 個單字才能做選擇題。")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['word']}</p>",
                unsafe_allow_html=True
            )

            correct = item["definition"]
            options = make_choice_list(correct, st.session_state.word_bank, "definition")

            user_choice = st.radio("請選出正確中文：", options, key=f"q2_{i}")
            if st.button("檢查答案", key=f"btn2_{i}"):
                if user_choice == correct:
                    st.success("🎉 太棒了！")
                else:
                    st.error(f"不對喔，正確答案是：{correct}")

# =========================================
# 8. 第三頁：題庫總複習
#    給中文 -> 選正確英文
# =========================================
elif page == "🧠 第三頁：題庫總複習":
    st.title("🧠 題庫總複習")

    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 至少要 4 個單字才能做四選一總複習。")
    else:
        score = 0

        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：「{item['definition']}」是哪個英文單字？</p>",
                unsafe_allow_html=True
            )

            correct = item["word"]
            options = make_choice_list(correct, st.session_state.word_bank, "word")

            user_choice = st.radio("請選擇：", options, key=f"q3_{i}")
            if user_choice == correct:
                score += 1

        if st.button("📊 送出結算分數"):
            st.success(f"總分：{score} / {len(st.session_state.word_bank)}")
            if score == len(st.session_state.word_bank):
                st.balloons()
