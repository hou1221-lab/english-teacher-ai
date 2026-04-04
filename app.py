import streamlit as st
import random
import pandas as pd
import re
from pypdf import PdfReader

# =========================================
# 1. 基本設定
# =========================================
st.set_page_config(
    page_title="孩子英文學習機",
    layout="centered",
    page_icon="📝"
)

st.markdown("""
<style>
/* 整體字體 */
html, body, [class*="css"]  {
    font-size: 22px !important;
}

/* 標題 */
h1 {
    font-size: 46px !important;
    font-weight: 900 !important;
}
h2 {
    font-size: 38px !important;
    font-weight: 800 !important;
}
h3 {
    font-size: 30px !important;
    font-weight: 800 !important;
}

/* 題目字體 */
.big-font {
    font-size: 40px !important;
    font-weight: 900 !important;
    line-height: 1.7 !important;
    margin-bottom: 12px !important;
}

/* 一般說明文字 */
.normal-font {
    font-size: 24px !important;
    line-height: 1.6 !important;
}

/* 輸入框 */
.stTextInput input {
    font-size: 30px !important;
    height: 68px !important;
    font-weight: bold !important;
}

/* TextArea */
textarea {
    font-size: 22px !important;
}

/* Radio 選項 */
div[data-baseweb="radio"] label {
    font-size: 28px !important;
    font-weight: bold !important;
    line-height: 1.8 !important;
}

/* 按鈕 */
.stButton button {
    font-size: 24px !important;
    font-weight: bold !important;
    padding: 12px 20px !important;
    border-radius: 12px !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-size: 22px !important;
    font-weight: bold !important;
}

/* Sidebar */
section[data-testid="stSidebar"] * {
    font-size: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================
# 2. Session State 初始化
# =========================================
if "word_bank" not in st.session_state:
    st.session_state.word_bank = []

if "challenge_order" not in st.session_state:
    st.session_state.challenge_order = []

if "challenge_index" not in st.session_state:
    st.session_state.challenge_index = 0

if "challenge_score" not in st.session_state:
    st.session_state.challenge_score = 0

if "challenge_wrong" not in st.session_state:
    st.session_state.challenge_wrong = []

if "challenge_answered" not in st.session_state:
    st.session_state.challenge_answered = False

if "challenge_selected" not in st.session_state:
    st.session_state.challenge_selected = None

if "challenge_result" not in st.session_state:
    st.session_state.challenge_result = None

# =========================================
# 3. 工具函式
# =========================================
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip())

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
    支援：
    apple 蘋果
    banana 香蕉

    或：
    apple,蘋果
    banana,香蕉

    或：
    apple\t蘋果
    """
    results = []
    lines = text.split("\n")

    for line in lines:
        line = clean_text(line)
        if not line:
            continue

        parts = None

        if "," in line:
            parts = [x.strip() for x in line.split(",", 1)]
        elif "\t" in line:
            parts = [x.strip() for x in line.split("\t", 1)]
        else:
            parts = line.split(" ", 1)

        if len(parts) == 2:
            eng = clean_text(parts[0]).lower()
            chi = clean_text(parts[1])

            # 英文只保留合理格式
            if re.fullmatch(r"[A-Za-z][A-Za-z\-\s']*", eng):
                results.append({"word": eng, "definition": chi})

    return deduplicate_words(results)

def get_hint(word):
    word = word.strip()
    if len(word) <= 1:
        return word
    return f"{word[0]} " + " ".join(["_"] * (len(word) - 1))

def make_choice_list(correct_value, pool, key_name):
    others = [item[key_name] for item in pool if item[key_name] != correct_value]
    distractors = random.sample(others, min(3, len(others)))
    choices = distractors + [correct_value]
    random.shuffle(choices)
    return choices

def import_words(new_words):
    st.session_state.word_bank.extend(new_words)
    st.session_state.word_bank = deduplicate_words(st.session_state.word_bank)

def load_words_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def reset_challenge():
    st.session_state.challenge_order = list(range(len(st.session_state.word_bank)))
    random.shuffle(st.session_state.challenge_order)
    st.session_state.challenge_index = 0
    st.session_state.challenge_score = 0
    st.session_state.challenge_wrong = []
    st.session_state.challenge_answered = False
    st.session_state.challenge_selected = None
    st.session_state.challenge_result = None

# =========================================
# 4. 側邊欄
# =========================================
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio(
    "切換頁面",
    [
        "📝 家長建立題庫",
        "✍️ 第一頁：中文提示拼英文",
        "🎯 第二頁：英文選中文",
        "🧠 第三頁：闖關總複習",
        "📚 錯題本"
    ]
)

if st.sidebar.button("🗑️ 重設全部題庫"):
    st.session_state.word_bank = []
    reset_challenge()
    st.rerun()

# =========================================
# 5. 家長建立題庫
# =========================================
if page == "📝 家長建立題庫":
    st.title("📝 家長建立題庫")
    st.markdown("<p class='normal-font'>可以單筆輸入、整批貼上，或直接上傳 PDF 單字表。</p>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["單筆輸入", "整批貼上", "PDF 匯入"])

    with tab1:
        with st.form("single_add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                eng = st.text_input("英文單字")
            with col2:
                chi = st.text_input("中文意思")

            submitted = st.form_submit_button("➕ 加入題庫")
            if submitted:
                eng = clean_text(eng).lower()
                chi = clean_text(chi)

                if eng and chi:
                    import_words([{"word": eng, "definition": chi}])
                    st.success(f"已加入：{eng} / {chi}")
                else:
                    st.error("英文和中文都不能空白。")

    with tab2:
        st.markdown("<p class='normal-font'>請一行一筆，例如：</p>", unsafe_allow_html=True)
        st.code("apple 蘋果\nbanana 香蕉\norange 橘子\naccount 帳目")
        st.markdown("<p class='normal-font'>也支援逗號格式：</p>", unsafe_allow_html=True)
        st.code("apple,蘋果\nbanana,香蕉")

        bulk_text = st.text_area("請貼上單字表", height=240)

        if st.button("📥 匯入整批單字"):
            parsed = parse_bulk_text(bulk_text)
            if parsed:
                import_words(parsed)
                st.success(f"成功匯入 {len(parsed)} 筆單字。")
            else:
                st.error("格式不正確，請用「英文 空格 中文」或「英文,中文」。")

    with tab3:
        st.markdown("<p class='normal-font'>上傳 PDF 後，系統會先把文字抓出來，再轉成題庫。</p>", unsafe_allow_html=True)
        st.markdown("<p class='normal-font'>PDF 內容最好是這種格式：</p>", unsafe_allow_html=True)
        st.code("apple 蘋果\nbanana 香蕉\naccord 一致、符合\nacceptable 可接受的，合意的")

        pdf_file = st.file_uploader("上傳 PDF 單字表", type=["pdf"], key="pdf_uploader")

        if pdf_file:
            try:
                extracted_text = load_words_from_pdf(pdf_file)
                st.text_area("📖 PDF 解析內容（可先檢查）", extracted_text, height=260, key="pdf_text_preview")

                if st.button("📥 將 PDF 內容轉成題庫"):
                    parsed = parse_bulk_text(extracted_text)
                    if parsed:
                        import_words(parsed)
                        st.success(f"成功匯入 {len(parsed)} 筆單字。")
                    else:
                        st.error("無法解析成題庫，請確認 PDF 每行是『英文 中文』或『英文,中文』。")
            except Exception as e:
                st.error(f"PDF 讀取失敗：{e}")

    st.subheader("📋 目前題庫清單")
    if st.session_state.word_bank:
        df = pd.DataFrame(st.session_state.word_bank)
        st.dataframe(df, use_container_width=True)

        csv_data = pd.DataFrame(st.session_state.word_bank).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ 下載題庫 CSV",
            data=csv_data,
            file_name="word_bank.csv",
            mime="text/csv"
        )
    else:
        st.info("目前還沒有單字。")

# =========================================
# 6. 第一頁：中文提示拼英文
# =========================================
elif page == "✍️ 第一頁：中文提示拼英文":
    st.title("✍️ 中文提示拼英文")

    if not st.session_state.word_bank:
        st.warning("⚠️ 題庫空空的，請先到家長建立題庫。")
    else:
        st.markdown("<p class='normal-font'>看到中文後，自己拼出英文單字。</p>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>",
                unsafe_allow_html=True
            )

            hint = get_hint(item["word"])
            ans = st.text_input(f"提示：{hint}", key=f"spell_{i}").strip().lower()

            if ans:
                if ans == item["word"]:
                    st.success("✅ 正確！")
                else:
                    st.error(f"❌ 再試一次。提示：{hint}")

# =========================================
# 7. 第二頁：英文選中文
# =========================================
elif page == "🎯 第二頁：英文選中文":
    st.title("🎯 英文選中文")

    if len(st.session_state.word_bank) < 2:
        st.warning("⚠️ 至少要 2 個單字才能做選擇題。")
    else:
        st.markdown("<p class='normal-font'>看到英文，選出正確中文。</p>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['word']}</p>",
                unsafe_allow_html=True
            )

            correct = item["definition"]
            options = make_choice_list(correct, st.session_state.word_bank, "definition")

            user_choice = st.radio("請選擇：", options, key=f"q2_{i}")
            if st.button("檢查答案", key=f"btn2_{i}"):
                if user_choice == correct:
                    st.success("🎉 太棒了！")
                else:
                    st.error(f"❌ 正確答案是：{correct}")

# =========================================
# 8. 第三頁：闖關總複習
# =========================================
elif page == "🧠 第三頁：闖關總複習":
    st.title("🧠 題庫總複習")

    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 至少要 4 個單字才能做四選一闖關。")
    else:
        if not st.session_state.challenge_order or len(st.session_state.challenge_order) != len(st.session_state.word_bank):
            reset_challenge()

        total = len(st.session_state.challenge_order)
        current_idx = st.session_state.challenge_index

        if current_idx >= total:
            st.success(f"🎉 闖關完成！總分：{st.session_state.challenge_score} / {total}")

            if st.session_state.challenge_score == total:
                st.balloons()
                st.success("太厲害了，全對！")

            if st.session_state.challenge_wrong:
                st.subheader("❌ 本次錯題")
                wrong_df = pd.DataFrame(st.session_state.challenge_wrong)
                st.dataframe(wrong_df, use_container_width=True)
            else:
                st.success("本次沒有錯題！")

            if st.button("🔁 再玩一次"):
                reset_challenge()
                st.rerun()

        else:
            q_number = current_idx + 1
            item_index = st.session_state.challenge_order[current_idx]
            item = st.session_state.word_bank[item_index]

            st.markdown(
                f"<p class='normal-font'>目前進度：第 {q_number} 題 / 共 {total} 題</p>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<p class='normal-font'>目前分數：{st.session_state.challenge_score}</p>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<p class='big-font'>第 {q_number} 題：「{item['definition']}」是哪個英文單字？</p>",
                unsafe_allow_html=True
            )

            correct = item["word"]
            options = make_choice_list(correct, st.session_state.word_bank, "word")

            selected = st.radio(
                "請選擇：",
                options,
                key=f"challenge_radio_{current_idx}"
            )

            if not st.session_state.challenge_answered:
                if st.button("✅ 送出答案"):
                    st.session_state.challenge_selected = selected
                    if selected == correct:
                        st.session_state.challenge_score += 1
                        st.session_state.challenge_result = True
                    else:
                        st.session_state.challenge_result = False
                        st.session_state.challenge_wrong.append({
                            "題號": q_number,
                            "中文": item["definition"],
                            "你的答案": selected,
                            "正確答案": correct
                        })

                    st.session_state.challenge_answered = True
                    st.rerun()

            else:
                if st.session_state.challenge_result:
                    st.success("🎉 答對了！")
                else:
                    st.error(f"❌ 答錯了！正確答案是：{correct}")

                if st.button("➡️ 下一題"):
                    st.session_state.challenge_index += 1
                    st.session_state.challenge_answered = False
                    st.session_state.challenge_selected = None
                    st.session_state.challenge_result = None
                    st.rerun()

# =========================================
# 9. 錯題本
# =========================================
elif page == "📚 錯題本":
    st.title("📚 錯題本")

    if st.session_state.challenge_wrong:
        st.markdown("<p class='normal-font'>這裡會顯示最近一次闖關答錯的題目。</p>", unsafe_allow_html=True)
        wrong_df = pd.DataFrame(st.session_state.challenge_wrong)
        st.dataframe(wrong_df, use_container_width=True)

        csv_data = wrong_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ 下載錯題本 CSV",
            data=csv_data,
            file_name="wrong_answers.csv",
            mime="text/csv"
        )
    else:
        st.info("目前還沒有錯題紀錄。先去『闖關總複習』玩一輪吧。")
