import streamlit as st
import requests
import json
import re
import random
import time
import plotly.graph_objects as go # 引入圖表庫

# 頁面設定
st.set_page_config(
    page_title="英級棒!! 學測英文作文AI智慧批卷系統", 
    page_icon="💯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 多重金鑰負載平衡系統
# ==========================================
def get_random_api_key():
    available_keys = []
    if "API_KEY_1" in st.secrets: available_keys.append(st.secrets["API_KEY_1"])
    if "API_KEY_2" in st.secrets: available_keys.append(st.secrets["API_KEY_2"])
    if "API_KEY_3" in st.secrets: available_keys.append(st.secrets["API_KEY_3"])
    if "API_KEY_4" in st.secrets: available_keys.append(st.secrets["API_KEY_4"])
    if "API_KEY_5" in st.secrets: available_keys.append(st.secrets["API_KEY_5"])
    if "GOOGLE_API_KEY" in st.secrets: available_keys.append(st.secrets["GOOGLE_API_KEY"])
    
    if available_keys:
        return random.choice(available_keys)
    else:
        return None

PROJECT_API_KEY = get_random_api_key()

# ==========================================
# CSS 優化
# ==========================================
st.markdown("""
<style>
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; }
    
    /* 指標卡片自適應 */
    .metric-card { 
        background-color: var(--secondary-background-color); 
        border-radius: 10px; 
        padding: 15px; 
        text-align: center; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1); 
    }
    
    /* 頁尾固定 */
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        text-align: center; color: var(--text-color); font-size: 12px; 
        padding: 10px; background-color: var(--background-color); 
        pointer-events: none; border-top: 1px solid rgba(49, 51, 63, 0.2); z-index: 100; 
    }
    .block-container { padding-bottom: 80px; }
    
    /* 自適應文字顏色 */
    h1, h2, h3, h4, h5, h6 { color: var(--text-color) !important; font-weight: 600 !important; }
    p, li, span, div { color: var(--text-color) !important; font-size: 16px !important; }
    
    /* Widget Label */
    .stRadio label, .stTextInput label, .stTextArea label, .stSelectbox label {
        color: var(--text-color) !important; font-size: 18px !important; font-weight: bold !important;
    }

    .stTabs [data-baseweb="tab"] { color: var(--text-color); }
    
    /* Metric 數值顏色 */
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #ff4b4b !important; }
    [data-testid="stMetricLabel"] { font-size: 16px !important; color: var(--text-color) !important; }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄 ---
with st.sidebar:
    st.title("⚙️ 設定與評分標準")
    if PROJECT_API_KEY:
        st.success("✅ 系統已就緒 (多重金鑰保護中)")
    else:
        st.warning("⚠️ 未偵測到雲端 Key，請手動輸入")
        api_key_input = st.text_input("請輸入 Google API Key", type="password")
        PROJECT_API_KEY = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    st.subheader("🤖 AI 模型設定")
    target_model = "gemini-2.5-flash" 
    st.info("⚡ **AI 閱卷委員** (連線中)")
    
    st.markdown("---")
    with st.expander("📚 大考中心評分標準 (細項)", expanded=True):
        st.markdown("""
        **內容 (Content)**
        - **5-4分**: 主題清楚切題，細節支持完整。
        - **3分**: 主題不夠突顯。
        **組織 (Organization)**
        - **5-4分**: 連貫性佳。
        **文法 & 字彙**
        - **5-4分**: 精確，無明顯錯誤。
        """)

st.title("💯英級棒!! 學測英文作文AI智慧批卷系統")
st.caption("專為學測英文科所打造，依大考中心數據校正的模擬閱卷系統。")

if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""
if 'essay_content' not in st.session_state:
    st.session_state.essay_content = ""
if 'grading_result' not in st.session_state: # 儲存批改結果供下載用
    st.session_state.grading_result = ""

# --- 核心連線函數 ---
def call_gemini_api(prompt, key, model_name):
    keys_pool = []
    if "API_KEY_1" in st.secrets: keys_pool.append(st.secrets["API_KEY_1"])
    if "API_KEY_2" in st.secrets: keys_pool.append(st.secrets["API_KEY_2"])
    if "API_KEY_3" in st.secrets: keys_pool.append(st.secrets["API_KEY_3"])
    if "API_KEY_4" in st.secrets: keys_pool.append(st.secrets["API_KEY_4"])
    if "API_KEY_5" in st.secrets: keys_pool.append(st.secrets["API_KEY_5"])
    if "GOOGLE_API_KEY" in st.secrets: keys_pool.append(st.secrets["GOOGLE_API_KEY"])
    
    if not keys_pool and key: keys_pool = [key]
    
    clean_model_name = model_name.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }

    max_retries = max(3, len(keys_pool))
    
    for attempt in range(max_retries):
        current_key = keys_pool[attempt % len(keys_pool)]
        current_url = f"{url}?key={current_key}"
        try:
            response = requests.post(current_url, headers=headers, json=data)
            if response.status_code == 200:
                try:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                except: return "⚠️ AI 回傳格式錯誤，請重試。"
            elif response.status_code == 429:
                st.toast(f"⚠️ 線路 {attempt+1} 忙碌，切換中...", icon="🔄")
                time.sleep(1.5)
                continue
            else:
                return f"⚠️ 連線錯誤: {response.status_code}"
        except Exception as e:
            return f"⚠️ 系統錯誤: {str(e)}"
    return "❌ 系統忙碌中，請稍後再試。"

# --- 雷達圖繪製函數 ---
def plot_radar_chart(scores):
    categories = ['內容', '組織', '文法', '字彙']
    # 補齊數據確保 list 長度
    values = [int(s) for s in scores]
    while len(values) < 4: values.append(0)
    
    # 封閉圖形
    values += values[:1]
    categories += categories[:1]

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line_color='#FF4B4B',
        fillcolor='rgba(255, 75, 75, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickfont=dict(color='gray')
            ),
            angularaxis=dict(
                tickfont=dict(size=14, color='gray') # 調整標籤顏色以適應深淺模式
            )
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)', # 透明背景
        plot_bgcolor='rgba(0,0,0,0)'
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
    
    if topic_source == "AI 自動出題":
        if st.button("✨ 生成模擬試題 (隨機)", type="primary"):
            if not PROJECT_API_KEY:
                st.error("❌ 請先設定 API Key")
            else:
                with st.spinner("AI 閱卷委員正在出題..."):
                    prompt_gen = """
                    角色：大考中心出題委員。
                    任務：隨機設計一個學測英文作文題目 (食/衣/住/行/文化/校園/時事/成長)。
                    
                    ⚠️ **Strict Output Rules**:
                    1. 禁止開場白。
                    2. 禁止英文指令。
                    3. 格式統一。
                    
                    請直接輸出以下內容 (全繁體中文)：
                    ### 題目：[題目名稱]
                    **引文說明**：[50-80字引導]
                    **第一段引導**：[說明重點]
                    **第二段引導**：[說明重點]
                    """
                    current_key = get_random_api_key() or PROJECT_API_KEY
                    result = call_gemini_api(prompt_gen, current_key, target_model)
                    st.session_state.generated_topic = result
        
        if st.session_state.generated_topic:
            st.markdown(st.session_state.generated_topic)
            st.info("💡 **小提醒：學測英文作文建議作答字數為 120 字以上 (約 150-180 字為佳)！**")
            current_topic = st.session_state.generated_topic
        else:
            current_topic = ""
    else:
        current_topic = st.text_area("請輸入題目說明", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("📍 寫作與批改")
    
    if current_topic:
        with st.expander("📄 點擊查看當前題目", expanded=False):
            st.markdown(current_topic)
    else:
        st.warning("⚠️ 尚未設定題目")

    user_essay = st.text_area("請在此輸入英文作文：", value=st.session_state.essay_content, height=300, key="essay_input")
    
    word_count = len(re.findall(r'\w+', user_essay))
    if word_count > 0:
        st.caption(f"📊 目前字數：{word_count} 字")

    if st.button("🚀 開始批改", type="primary", use_container_width=True):
        if not PROJECT_API_KEY:
            st.error("❌ 請先設定 API Key！")
        elif not user_essay:
            st.warning("⚠️ 請輸入作文內容！")
        else:
            # 🔥 批改 Prompt：新增 Diff 標示指令 🔥
            system_prompt = f"""
            # Role: 台灣學測英文作文「地獄級」閱卷委員
            
            # Context:
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # 評分邏輯 (Strict Scoring):
            **基準分：10分**
            - ❌ **上限 11 分**: 國中程度用字。
            - ❌ **上限 14 分**: 有明顯文法錯誤。
            - ✅ **15 分以上**: 深度 + 精準用字 + 無錯。
            - 常模：15-20分(前7%), 12-14分(前27%), 9-11分(中段)。

            # Task: 產出 Markdown 報告
            
            ## Part 1: 總分與犀利點評
            總分 (0-20)：[分數]
            一句話點評：(嚴格點評)
            
            ## Part 2: 四大構面評分 (0-5分)
            - 內容: [分數] 
            - 組織: [分數] 
            - 文法: [分數] 
            - 字彙: [分數] 
            
            ## Part 3: 逐句訂正 (Visual Diff)
            **請找出 3-5 個錯誤。**
            **⚠️ 關鍵要求：請使用「刪除線」與「粗體」標示差異，讓學生一眼看出改了哪裡。**
            格式範例：
            > ### 🚩 改進點 1
            > - 🔴 **原句**: He :red[~~go~~] to school yesterday.
            > - 🟢 **訂正**: He :green[**went**] to school yesterday.
            > - 💡 **解析**: 時態錯誤，yesterday 為過去式。
            
            ## Part 4: Level 5-6 高級字彙升級
            **提供 3-5 個高級單字 (含詞性/中文/等級)。**
            > ### 🌟 升級建議 1
            > - 🔹 **原文**: :blue[...]
            > - 🚀 **升級**: **[單字]** ([詞性], [中文]) (Level [5/6])
            > - 📝 **解析**: ...
            
            ## Part 5: 實用加分句型
            **提供 3 組「截然不同類型」的高級句型 (如倒裝、分詞、虛擬)。**
            """
            
            # 💡 優化：在等待時顯示實用小撇步 (隨機)
            tips = ["💡 Tip: 善用轉折詞 (However, Therefore) 能大幅提升組織分數！", 
                    "💡 Tip: 避免一直使用 'very'，改用 'extremely' 或 'significantly'。", 
                    "💡 Tip: 嘗試使用倒裝句來增強語氣，閱卷老師會眼睛一亮！"]
            
            with st.spinner(f"AI 閱卷委員正在嚴格審視中...\n{random.choice(tips)}"):
                current_key = get_random_api_key() or PROJECT_API_KEY
                result = call_gemini_api(system_prompt, current_key, target_model)
                st.session_state.grading_result = result # 存起來供下載
                
                if "⚠️" in result:
                    st.error(result)
                else:
                    st.success("🎉 閱卷完成！")
                    
                    # --- 儀表板區域 ---
                    try:
                        total_match = re.search(r"總分.*?[:：]\s*(\d+)", result)
                        content_match = re.search(r"內容.*?[:：]\s*(\d+)", result)
                        org_match = re.search(r"組織.*?[:：]\s*(\d+)", result)
                        gram_match = re.search(r"文法.*?[:：]\s*(\d+)", result)
                        vocab_match = re.search(r"字彙.*?[:：]\s*(\d+)", result)
                        
                        scores = [
                            content_match.group(1) if content_match else "0",
                            org_match.group(1) if org_match else "0",
                            gram_match.group(1) if gram_match else "0",
                            vocab_match.group(1) if vocab_match else "0"
                        ]
                        total_score = total_match.group(1) if total_match else "N/A"

                        st.subheader("📊 評分摘要")
                        
                        # 左邊放數字，右邊放雷達圖
                        col_metrics, col_radar = st.columns([2, 1])
                        
                        with col_metrics:
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("📝 內容", f"{scores[0]} / 5")
                            c2.metric("🏗️ 組織", f"{scores[1]} / 5")
                            c3.metric("⚖️ 文法", f"{scores[2]} / 5")
                            c4.metric("🔤 字彙", f"{scores[3]} / 5")
                            st.metric("🏆 總分", f"{total_score} / 20", delta="請繼續加油" if int(total_score)<15 else "表現優異")
                        
                        with col_radar:
                            fig = plot_radar_chart(scores)
                            st.plotly_chart(fig, use_container_width=True)
                            
                        st.divider()
                        
                    except Exception as e:
                        pass
                    
                    st.markdown(result)
                    
                    # 💡 新增：下載按鈕
                    st.download_button(
                        label="📥 下載完整評語 (.md)",
                        data=result,
                        file_name=f"Essay_Feedback_{int(time.time())}.md",
                        mime="text/markdown"
                    )
                    
                    st.divider()
                    st.caption("📢 本結果依大考中心配分標準所批改，若有疑問請洽詢製作者。")

st.markdown("---")
st.markdown("<div class='footer'>製作者：中央大學資管系二年級 蔡仁懋 m20060719@gmail.com </div>", unsafe_allow_html=True)