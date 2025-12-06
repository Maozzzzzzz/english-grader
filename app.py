import streamlit as st
import requests
import json
import re # 用於計算字數
import plotly.graph_objects as go # 用於繪製雷達圖

# ==========================================
# 👇👇👇 安全版設定：自動從 Streamlit 後台讀取密碼 👇👇👇
try:
    # 程式會自動去抓你剛剛在 Secrets 填寫的 "GEMINI_API_KEY"
    PROJECT_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # 如果沒抓到（例如你在自己電腦跑且沒設定），就留空
    PROJECT_API_KEY = "" 
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
    /* 作者署名樣式 */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        color: #888;
        font-size: 12px;
        padding: 10px;
        background-color: #ffffff;
        border-top: 1px solid #eee;
        z-index: 100;
    }
    /* 避免 footer 擋住內容 */
    .block-container {
        padding-bottom: 80px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State 初始化 ---
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""
if 'essay_content' not in st.session_state:
    st.session_state.essay_content = ""
if 'grading_result' not in st.session_state:
    st.session_state.grading_result = ""

# --- 側邊欄設計 ---
with st.sidebar:
    st.title("⚙️ 設定與評分標準")
    
    # 判斷是否有內建 Key (現在是從 Secrets 讀取)
    if PROJECT_API_KEY:
        api_key = PROJECT_API_KEY
        st.success("✅ 已啟用專題展示模式")
    else:
        api_key_input = st.text_input("請輸入 Google API Key", type="password")
        api_key = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    
    # API 健檢
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
    
    # 評分標準
    with st.expander("📚 大考中心評分標準 (點擊展開)"):
        st.markdown("""
        **依據 113 年學測統計數據校正：**
        
        **🏆 頂標 (15-20分)**
        - 僅前 **7.8%** 考生。
        - 內容深刻、文法零失誤、修辭優美。
        
        **👍 前標 (12-14分)**
        - 約前 **20%** 考生。
        - 結構完整、錯誤極少。
        
        **😐 均標 (9-11分)**
        - 約 **50%** 考生落點。
        - 溝通清楚，但有明顯文法錯誤或用字單調。
        
        **📉 後標 (0-8分)**
        - 內容貧乏或嚴重離題。
        """)

st.title("💯 英級棒!! 學測英文作文 AI 批改 APP")
st.caption("專為台灣高中生打造，依照大考中心數據嚴格校正的模擬閱卷系統。")

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

# 繪製雷達圖函數
def plot_radar_chart(scores):
    categories = ['內容', '組織', '文法', '字彙']
    score_values = [int(s) for s in scores[:4]]
    # 補足數據長度
    while len(score_values) < 4:
        score_values.append(0)
    
    # 封閉雷達圖
    score_values.append(score_values[0])
    categories.append(categories[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=score_values,
        theta=categories,
        fill='toself',
        name='得分',
        line_color='#FF4B4B'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=300
    )
    return fig

# 分頁設計
tab1, tab2 = st.tabs(["🎲 題目設定", "✍️ 作文批改區"])

# --- Tab 1: 題目設定 ---
with tab1:
    st.subheader("📍 設定題目")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        topic_source = st.radio("題目來源：", ["AI 自動出題", "自行輸入"])
    
    current_topic = ""
    
    if topic_source == "AI 自動出題":
        if st.button("✨ 生成模擬試題", type="primary"):
            if not api_key:
                st.error("❌ 請先設定 API Key")
            else:
                with st.spinner("AI 正在設計貼近高中生活的題目..."):
                    # 🔥 出題 Prompt 🔥
                    prompt_gen = """
                    角色：你是一位資深的高中英文學測出題老師。
                    任務：請從以下領域中選一個貼近台灣高中生生活的主題：
                    「食衣住行育樂、人際關係、校園生活、親情、友情、自我成長、科技與生活」。
                    
                    輸出要求：
                    1. **絕對不要**提到「隨機選出」或「主題是...」這類字眼。直接給題目。
                    2. **全中文**描述，模擬學測考卷的題目呈現方式。
                    3. 格式必須包含：
                       - 題目引文 (約 50 字，設定情境)
                       - 第一段引導 (說明應包含的內容)
                       - 第二段引導 (說明應包含的內容)
                    
                    範例格式：
                    提示：在成長過程中，我們常面臨...
                    第一段：請描述...
                    第二段：請說明...
                    """
                    result = call_gemini_api(prompt_gen, api_key, model_option)
                    st.session_state.generated_topic = result
        
        if st.session_state.generated_topic:
            st.info("👇 模擬試題：")
            st.markdown(st.session_state.generated_topic)
            current_topic = st.session_state.generated_topic
    else:
        current_topic = st.text_area("請輸入題目說明", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("📍 寫作與批改")
    
    if current_topic:
        with st.expander("📄 點擊查看當前題目", expanded=False):
            st.markdown(current_topic)
    else:
        st.warning("⚠️ 尚未設定題目，建議先到「題目設定」頁面生成或輸入題目。")

    # Demo 按鈕
    col_demo, col_empty = st.columns([1, 4])
    with col_demo:
        if st.button("📝 載入示範作文 (Demo)"):
            st.session_state.essay_content = """I think that robots will become helpful assistants in our future daily lives. For example, they can help us do household chores, such as sweeping the floor, washing the dishes, and taking out the garbage. With their assistance, we can save a lot of time and energy to do other meaningful things.

However, despite the convenience robots may bring, I am worried that they might make us lazy. If we rely on them too much, we might lose the ability to take care of ourselves. Therefore, while enjoying the benefits of technology, we should also remind ourselves not to be overly dependent on it."""
            st.rerun()

    user_essay = st.text_area(
        "請在此輸入英文作文：", 
        value=st.session_state.essay_content,
        height=250,
        key="essay_input"
    )
    
    # 字數統計
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
            # 🔥 全新升級：基於真實統計數據的嚴格評分 Prompt 🔥
            system_prompt = f"""
            # Role: 台灣學測英文作文「嚴格」閱卷委員
            # Objective: 根據 113 年學測得分統計數據進行「客觀且嚴格」的評分。
            
            # 📊 評分校正數據 (Statistical Calibration):
            你必須嚴格遵守此常態分佈，不要給分過於甜美：
            - **15~20分 (頂標)**：僅前 **7.8%** 的考生。文章必須近乎完美，有深度思想、精準的 6000 單字彙運用、複雜句構且零重大錯誤。
            - **12~14分 (前標)**：約前 **20%** 的考生。結構完整，論點清楚，錯誤極少。
            - **9~11分 (均標/中位數)**：約 **50%** 的考生落在此區間。內容基本切題，但文法有明顯錯誤，用字較為基礎(國中程度)。
            - **0~8分 (後標)**：內容貧乏、字數不足、離題或嚴重文法錯誤導致無法理解。

            # Context
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # Task: 執行「三階段回饋」 (重點：請優化排版與配色)
            
            ## 第一階段：嚴格評分 (各項 0-5 分)
            1. **內容 (Content)**
            2. **組織 (Organization)**
            3. **文法句構 (Grammar)**
            4. **字彙拼字 (Vocabulary)**
            *請給予一段「閱卷官風格」的簡評，直接指出為什麼他拿不到 15 分的原因。*

            ## 第二階段：文章訂正 (詳細批改)
            **請務必使用條列式清單 (List) 呈現，並使用不同顏色標示重點，讓閱讀更輕鬆。**
            
            格式範例：
            1. **(錯誤類別/段落指示)**
               - 🔴 **原句**: ... (錯誤的地方)
               - 🟢 **訂正**: ... (請用 **:green[粗體綠色]** 標示修正處)
               - 💡 **解析**: ... (簡單扼要說明原因)
            
            (請列出至少 3-5 個主要錯誤)

            ## 第三階段：學習資源 (請善用顏色區分)
            請使用以下格式：
            - 📖 **:blue[推薦升級詞組] (Level 4-5 單字)**
              1. word - definition
              2. word - definition
            
            - ✍️ **:orange[實用加分句型]**
              - 句型: ...
              - 例句: ...

            請輸出完整 Markdown 報告，確保排版清晰易讀 (Indentation is key)。
            """

            with st.spinner(f"AI 閱卷官正在嚴格評分中..."):
                result = call_gemini_api(system_prompt, api_key, model_option)
                
                if "⚠️" in result:
                    st.error(result)
                else:
                    st.session_state.grading_result = result

    # 顯示結果區 (包含雷達圖與下載按鈕)
    if st.session_state.grading_result:
        st.divider()
        st.success("🎉 閱卷完成！")
        
        # 繪製雷達圖
        try:
            raw_scores = re.findall(r"[:：]\s*(\d)\s*/\s*5", st.session_state.grading_result)
            if len(raw_scores) >= 4:
                col_chart, col_text = st.columns([1, 2])
                with col_chart:
                    fig = plot_radar_chart(raw_scores)
                    st.plotly_chart(fig, use_container_width=True)
                with col_text:
                    cats = ["內容", "組織", "文法", "字彙"]
                    c1, c2 = st.columns(2)
                    for i in range(4):
                        if i < 2:
                            c1.metric(cats[i], f"{raw_scores[i]} / 5")
                        else:
                            c2.metric(cats[i], f"{raw_scores[i]} / 5")
        except:
            pass
        
        st.markdown(st.session_state.grading_result)
        
        # 下載按鈕
        st.download_button(
            label="📥 下載閱卷報告 (.md)",
            data=st.session_state.grading_result,
            file_name="essay_feedback.md",
            mime="text/markdown"
        )
        
        # 頁尾聲明
        st.divider()
        st.caption("📢 本批改結果嚴格依據大學入學考試中心（CEEC）英文作文評分標準與 113 年學測得分統計數據進行運算，僅供學習參考。")

# --- 頁尾署名 ---
st.markdown("---")
st.markdown("""
<div class='footer'>
    製作者：中央大學資管系二年級 蔡仁懋
</div>
""", unsafe_allow_html=True)