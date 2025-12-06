import streamlit as st
import requests
import json
import re # 用於計算字數

# ==========================================
# 👇👇👇 專題設定區 (已填入你的 API Key) 👇👇👇
# 這裡有填字，網頁就會自動登入，輸入框會消失
PROJECT_API_KEY = "AIzaSyB__HHKjyIX0gB3avw5j_acBDy3fh_wblQ"
# ==========================================

# 頁面設定 (加入 initial_sidebar_state="expanded" 讓側邊欄預設展開)
st.set_page_config(
    page_title="英級棒!! 學測英文作文AI批改APP", 
    page_icon="💯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS 讓介面更漂亮
st.markdown("""
<style>
    .stTextArea textarea {
        font-size: 16px !important;
        line-height: 1.5 !important;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄設計 ---
with st.sidebar:
    st.title("⚙️ 設定與評分標準")
    
    # 判斷是否有內建 Key
    if PROJECT_API_KEY:
        api_key = PROJECT_API_KEY
        st.success("✅ 已啟用專題展示模式")
    else:
        api_key_input = st.text_input("請輸入 Google API Key", type="password")
        api_key = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    
    # API 健檢 (使用 expander 收納，讓介面更乾淨)
    with st.expander("🔍 API 連線狀態檢測"):
        if st.button("檢測 API Key"):
            if not api_key:
                st.error("❌ 未偵測到 API Key")
            else:
                try:
                    check_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                    resp = requests.get(check_url)
                    if resp.status_code == 200:
                        st.success("✅ 連線成功！")
                    else:
                        st.error(f"❌ 連線失敗: {resp.status_code}")
                except Exception as e:
                    st.error(f"錯誤: {e}")

    # 模型選擇
    user_available_models = [
        'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 
        'gemini-1.5-flash', 'gemini-1.5-pro'
    ]
    model_option = st.selectbox("🤖 選擇 AI 模型", user_available_models, index=0)
    
    st.markdown("---")
    
    # 將評分標準放入側邊欄，隨時可參考
    with st.expander("📚 大考中心評分標準 (點擊展開)"):
        st.markdown("""
        **1. 內容 (Content)**
        - 切題度、細節支持。
        
        **2. 組織 (Organization)**
        - 結構完整、轉折語使用。
        
        **3. 文法句構 (Grammar)**
        - 正確性、句型變化。
        
        **4. 字彙拼字 (Vocabulary)**
        - 用字精準、搭配詞。
        """)

st.title("💯 英級棒!! 學測英文作文 AI 批改 APP")
st.caption("專為台灣高中生打造，依照大考中心標準提供三階段深度批改。")

# 初始化 Session State
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""
if 'essay_content' not in st.session_state:
    st.session_state.essay_content = ""

# --- 核心功能：萬能連線函數 ---
def call_gemini_api(prompt, key, model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "⚠️ AI 回傳格式錯誤，請重試。"
        else:
            return f"⚠️ 連線錯誤: {response.text}"
    except Exception as e:
        return f"⚠️ 系統錯誤: {str(e)}"

# 分頁設計
tab1, tab2 = st.tabs(["🎲 題目設定", "✍️ 作文批改區"])

# --- Tab 1: 題目設定 ---
with tab1:
    st.subheader("📍 設定題目")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        topic_source = st.radio("題目來源：", ["AI 自動出題 (食衣住行育樂)", "自行輸入"])
    
    current_topic = ""
    
    if topic_source == "AI 自動出題 (食衣住行育樂)":
        if st.button("✨ 生成模擬試題", type="primary"):
            if not api_key:
                st.error("❌ 請先設定 API Key")
            else:
                with st.spinner("AI 正在出題中..."):
                    prompt_gen = "你現在是台灣高中英文學測的出題老師。請從「食、衣、住、行、育、樂」中隨機選一個主題，設計一個符合學測格式的英文作文題目。..."
                    result = call_gemini_api(prompt_gen, api_key, model_option)
                    st.session_state.generated_topic = result
        
        if st.session_state.generated_topic:
            st.info("👇 這是你的題目：")
            st.markdown(st.session_state.generated_topic)
            current_topic = st.session_state.generated_topic
    else:
        current_topic = st.text_area("請輸入題目說明", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("📍 寫作與批改")
    
    # 📌 功能改進：在寫作區顯示題目，避免切換
    if current_topic:
        with st.expander("📄 點擊查看當前題目", expanded=False):
            st.markdown(current_topic)
    else:
        st.warning("⚠️ 尚未設定題目，建議先到「題目設定」頁面生成或輸入題目。")

    # 📌 功能改進：一鍵載入範文 (Demo 用)
    col_demo, col_empty = st.columns([1, 4])
    with col_demo:
        if st.button("📝 載入示範作文 (Demo)"):
            st.session_state.essay_content = """I think that robots will become helpful assistants in our future daily lives. For example, they can help us do household chores, such as sweeping the floor, washing the dishes, and taking out the garbage. With their assistance, we can save a lot of time and energy to do other meaningful things.

However, despite the convenience robots may bring, I am worried that they might make us lazy. If we rely on them too much, we might lose the ability to take care of ourselves. Therefore, while enjoying the benefits of technology, we should also remind ourselves not to be overly dependent on it."""

    # 寫作區
    user_essay = st.text_area(
        "請在此輸入英文作文：", 
        value=st.session_state.essay_content,
        height=250,
        key="essay_input"
    )
    
    # 📌 功能改進：即時字數統計
    word_count = len(re.findall(r'\w+', user_essay))
    if word_count > 0:
        if word_count < 120:
            st.caption(f"📊 目前字數：:red[{word_count}] 字 (建議至少 120 字)")
        else:
            st.caption(f"📊 目前字數：:green[{word_count}] 字 (已達標)")

    if st.button("🚀 開始批改", type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ 請先設定 API Key！")
        elif not user_essay:
            st.warning("⚠️ 請輸入作文內容！")
        else:
            # System Prompt (保持原本的三階段邏輯)
            system_prompt = f"""
            # Role: 台灣學測英文作文批改助手
            # Task: 執行「三階段回饋」流程
            
            # Context
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # 要求
            1. **第一階段**：依照學測 20 分制評分 (內容/組織/文法/字彙)。
               - 格式要求：請明確列出四個分數，例如：「內容: 4/5」、「組織: 3/5」。
            2. **第二階段**：詳細訂正，用 [粗體方框] 標示修改。
            3. **第三階段**：提供詞組、句型、練習題。
            
            請輸出完整 Markdown 報告。
            """

            with st.spinner(f"AI 名師正在閱卷中..."):
                result = call_gemini_api(system_prompt, api_key, model_option)
                
                if "⚠️" in result:
                    st.error(result)
                else:
                    # 📌 功能改進：將結果區分為「視覺化分數」與「詳細報告」
                    st.divider()
                    st.success("🎉 批改完成！請查看下方分析：")
                    
                    # 嘗試從文字中提取分數 (簡單的正則表達式)
                    # 這是一個小技巧，讓分數可以變成漂亮的儀表板
                    try:
                        scores = re.findall(r"(\w+)\s*[:：]\s*(\d+)[/-]5", result)
                        if scores and len(scores) >= 4:
                            c1, c2, c3, c4 = st.columns(4)
                            cols = [c1, c2, c3, c4]
                            for i, (cat, score) in enumerate(scores[:4]):
                                cols[i].metric(label=cat, value=f"{score} / 5")
                    except:
                        pass # 如果提取失敗，就直接顯示全文，不影響運作
                    
                    # 顯示完整 Markdown 結果
                    st.markdown(result)

                    # 這裡可以加入下一步建議的按鈕
                    with st.expander("🤔 覺得評分不準？"):
                        st.info("你可以嘗試在左側切換不同的 AI 模型 (如 gemini-2.5-pro) 再批改一次。")