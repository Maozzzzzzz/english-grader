import streamlit as st
import requests
import json
import re
import time
from datetime import datetime
import plotly.graph_objects as go # 用於繪製雷達圖

# ==========================================
# 👇👇👇 專題設定區 (已填入你的 API Key) 👇👇👇
PROJECT_API_KEY = "AIzaSyB__HHKjyIX0gB3avw5j_acBDy3fh_wblQ"
# ==========================================

# 頁面設定
st.set_page_config(
    page_title="英級棒!! 學測英文作文AI批改APP", 
    page_icon="💯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS
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
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #ffffff;
        text-align: center;
        color: #888;
        font-size: 12px;
        padding: 10px;
        border-top: 1px solid #eee;
        z-index: 100;
    }
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
if 'history' not in st.session_state: # 📜 歷史紀錄清單
    st.session_state.history = []
if 'timer_end' not in st.session_state: # ⏱️ 計時器結束時間
    st.session_state.timer_end = None

# --- 側邊欄設計 ---
with st.sidebar:
    st.title("⚙️ 設定與紀錄")
    
    if PROJECT_API_KEY:
        api_key = PROJECT_API_KEY
        st.success("✅ 已啟用專題展示模式")
    else:
        api_key_input = st.text_input("請輸入 Google API Key", type="password")
        api_key = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    
    # 📜 歷史紀錄功能
    with st.expander("📜 寫作歷史紀錄", expanded=False):
        if not st.session_state.history:
            st.caption("目前尚無紀錄")
        else:
            for i, record in enumerate(reversed(st.session_state.history)):
                # 顯示簡單資訊：時間 - 分數
                timestamp = record['time']
                score_summary = record.get('total_score', 'N/A')
                if st.button(f"{timestamp} - {score_summary}", key=f"hist_{i}"):
                    # 點擊後將舊資料載入主畫面
                    st.session_state.essay_content = record['essay']
                    st.session_state.grading_result = record['result']
                    st.session_state.generated_topic = record['topic']
                    st.toast(f"已載入 {timestamp} 的紀錄！", icon="📂")
                    time.sleep(1) # 讓 toast 顯示一下
                    st.rerun()

    st.markdown("---")
    
    # 模型選擇
    user_available_models = [
        'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 
        'gemini-1.5-flash', 'gemini-1.5-pro'
    ]
    model_option = st.selectbox("🤖 選擇 AI 模型", user_available_models, index=0)

    # 評分標準說明
    with st.expander("📚 大考中心評分標準", expanded=False):
        st.markdown("""
        **1. 內容 (Content) 0-5分**
        - 主題清楚切題？論點是否有具體細節支持？
        **2. 組織 (Organization) 0-5分**
        - 結構完整？轉折語使用流暢？
        **3. 文法句構 (Grammar) 0-5分**
        - 文法正確性？句型變化豐富度？
        **4. 字彙拼字 (Vocabulary) 0-5分**
        - 用字精準度與搭配詞？拼字正確性？
        """)

st.title("💯 英級棒!! 學測英文作文 AI 批改 APP")
st.caption("專為台灣高中生打造，依照大考中心數據嚴格校正的模擬閱卷系統。")

# --- 核心函數 ---
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
    # 確保分數有 4 個，沒有抓到的話補 0
    score_values = [int(s) for s in scores[:4]]
    while len(score_values) < 4:
        score_values.append(0)
    
    # 雷達圖需要封閉，所以把第一個點加到最後
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
        topic_type = st.selectbox(
            "請選擇題目類型：",
            ["生活情境 (食衣住行育樂)", "社會議題與時事", "校園生活與學習", "人際關係與情感", "隨機挑戰"]
        )
        
        if st.button("✨ 生成模擬試題", type="primary"):
            if not api_key:
                st.error("❌ 請先設定 API Key")
            else:
                with st.spinner("AI 正在設計題目中..."):
                    prompt_gen = f"""
                    角色：你是一位資深的高中英文學測出題老師。
                    任務：請針對「{topic_type}」這個領域，設計一個貼近台灣高中生程度的英文作文題目。
                    輸出要求：
                    1. **絕對不要**提到「隨機選出」或「主題是...」這類字眼。
                    2. **全中文**描述。
                    3. 格式：題目引文(50字) + 第一段引導 + 第二段引導。
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
    
    # 題目顯示
    if current_topic:
        with st.expander("📄 點擊查看當前題目", expanded=False):
            st.markdown(current_topic)
    else:
        st.warning("⚠️ 尚未設定題目，建議先到「題目設定」頁面生成或輸入題目。")

    # ⏱️ 計時器區塊
    with st.expander("⏱️ 考試計時器 (模擬考模式)", expanded=False):
        col_t1, col_t2, col_t3 = st.columns([2, 1, 2])
        with col_t1:
            timer_min = st.number_input("設定時間 (分鐘)", min_value=1, value=40, step=1)
        with col_t2:
            st.write("") # Spacer
            if st.button("開始計時"):
                st.session_state.timer_end = time.time() + timer_min * 60
                st.rerun()
        with col_t3:
            if st.session_state.timer_end:
                remaining = st.session_state.timer_end - time.time()
                if remaining > 0:
                    mins, secs = divmod(int(remaining), 60)
                    st.metric("剩餘時間", f"{mins:02d}:{secs:02d}")
                else:
                    st.metric("剩餘時間", "00:00", delta="- 時間到！", delta_color="inverse")
            else:
                st.info("尚未開始計時")

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

    col_grade, col_reset = st.columns([1, 1])
    
    with col_grade:
        start_grade = st.button("🚀 開始批改", type="primary", use_container_width=True)
    
    with col_reset:
        if st.button("🔄 寫下一篇 (重置)", type="secondary", use_container_width=True):
            st.session_state.essay_content = ""
            st.session_state.grading_result = ""
            st.session_state.timer_end = None
            st.rerun()

    if start_grade:
        if not api_key:
            st.error("❌ 請先設定 API Key！")
        elif not user_essay:
            st.warning("⚠️ 請輸入作文內容！")
        else:
            system_prompt = f"""
            # Role: 台灣學測英文作文「嚴格」閱卷委員
            # Objective: 根據 113 年學測得分統計數據進行「客觀且嚴格」的評分。
            
            # 📊 評分校正 (Calibration):
            - **15~20分 (頂標)**：前 7.8%。近乎完美。
            - **12~14分 (前標)**：前 20%。結構完整，錯誤極少。
            - **9~11分 (均標)**：約 50%。溝通清楚但有錯誤。
            - **0~8分 (後標)**：內容貧乏或嚴重錯誤。

            # Context
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # Task: 執行「三階段回饋」
            
            ## 第一階段：嚴格評分 (請務必回傳分數供圖表使用)
            格式：
            內容 (Content): [分數]/5
            組織 (Organization): [分數]/5
            文法句構 (Grammar): [分數]/5
            字彙拼字 (Vocabulary): [分數]/5
            
            *閱卷官總評*

            ## 第二階段：文章訂正
            **請務必使用標準 Markdown 列表格式**
            格式範例：
            - 🔴 **原句**: ...
            - 🟢 **訂正**: ... (:green[粗體]修正)
            - 💡 **解析**: ...
            
            ## 第三階段：學習資源
            - 📖 **:blue[推薦升級詞組] (Level 4-5 單字)**
            - ✍️ **:orange[實用加分句型]**

            請輸出完整 Markdown 報告。
            """

            with st.spinner(f"英級棒老師閱卷中..."):
                result = call_gemini_api(system_prompt, api_key, model_option)
                
                if "⚠️" in result:
                    st.error(result)
                else:
                    st.session_state.grading_result = result
                    
                    # 嘗試抓取分數並儲存歷史紀錄
                    try:
                        scores = re.findall(r"(\w+)\s*[:：]\( \)\s*(\d+)[/-]5", result)
                        # 備用 regex，避免括號或其他符號干擾
                        if not scores:
                            scores = re.findall(r"[:：]\s*(\d+)[/-]5", result)
                            if len(scores) >= 4:
                                # 只有分數沒有類別名時，自己補上
                                scores_data = scores[:4]
                            else:
                                scores_data = []
                        else:
                            scores_data = [s[1] for s in scores[:4]]
                        
                        # 儲存歷史紀錄
                        total_s = sum([int(s) for s in scores_data]) if scores_data else "N/A"
                        st.session_state.history.append({
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "topic": current_topic,
                            "essay": user_essay,
                            "result": result,
                            "total_score": f"約 {total_s}/20",
                            "raw_scores": scores_data
                        })
                    except:
                        pass # 歷史紀錄存取失敗不影響顯示

    # 顯示結果區
    if st.session_state.grading_result:
        st.divider()
        st.success("🎉 閱卷完成")
        
        # 1. 雷達圖區塊
        try:
            # 抓分數的 Regex (稍微放寬條件以防 AI 輸出格式微調)
            raw_scores = re.findall(r"[:：]\s*(\d)\s*/\s*5", st.session_state.grading_result)
            if len(raw_scores) >= 4:
                col_chart, col_text = st.columns([1, 2])
                with col_chart:
                    fig = plot_radar_chart(raw_scores)
                    st.plotly_chart(fig, use_container_width=True)
                with col_text:
                    # 顯示文字分數
                    cats = ["內容", "組織", "文法", "字彙"]
                    c1, c2 = st.columns(2)
                    for i in range(4):
                        if i < 2:
                            c1.metric(cats[i], f"{raw_scores[i]} / 5")
                        else:
                            c2.metric(cats[i], f"{raw_scores[i]} / 5")
        except Exception as e:
            # st.error(f"圖表繪製失敗: {e}") # Debug 用
            pass
        
        st.markdown(st.session_state.grading_result)
        
        st.download_button(
            label="📥 下載閱卷報告 (.md)",
            data=st.session_state.grading_result,
            file_name="essay_feedback.md",
            mime="text/markdown"
        )
        
        st.divider()
        st.caption("📢 本批改結果嚴格依據大學入學考試中心（CEEC）英文作文評分標準與學測得分統計數據進行運算，僅供學習參考。")

# 頁尾
st.markdown("""
<div class='footer'>
    製作者：中央大學資管系二年級 蔡仁懋
</div>
""", unsafe_allow_html=True)