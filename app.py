import streamlit as st
import requests
import json
import re
import random
import google.generativeai as genai

# 頁面設定
st.set_page_config(
    page_title="英級棒!! 學測英文作文AI批改APP", 
    page_icon="💯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 👇👇👇 三刀流：多重金鑰負載平衡系統 👇👇👇
# ==========================================
def get_random_api_key():
    """
    從 Streamlit Secrets 中讀取 API_KEY_1, API_KEY_2, API_KEY_3
    並隨機選出一組使用，分散流量風險。
    """
    available_keys = []
    
    # 嘗試抓取 3 把鑰匙
    if "API_KEY_1" in st.secrets:
        available_keys.append(st.secrets["API_KEY_1"])
    
    if "API_KEY_2" in st.secrets:
        available_keys.append(st.secrets["API_KEY_2"])
        
    if "API_KEY_3" in st.secrets:
        available_keys.append(st.secrets["API_KEY_3"])
    
    # 相容舊設定 (如果有設 GOOGLE_API_KEY 也納入)
    if "GOOGLE_API_KEY" in st.secrets:
        available_keys.append(st.secrets["GOOGLE_API_KEY"])
    
    # 🎲 隨機選一把鑰匙回傳
    if available_keys:
        return random.choice(available_keys)
    else:
        return None

# 初始化：選定本次操作預設要用的 Key
PROJECT_API_KEY = get_random_api_key()

# ==========================================

# 自訂 CSS
st.markdown("""
<style>
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; }
    .metric-card { background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; color: #888; font-size: 12px; padding: 10px; background-color: #ffffff; pointer-events: none; border-top: 1px solid #eee; z-index: 100; }
    .block-container { padding-bottom: 80px; }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄設計 ---
with st.sidebar:
    st.title("⚙️ 設定與評分標準")
    
    # 顯示目前系統狀態
    if PROJECT_API_KEY:
        api_key = PROJECT_API_KEY
        # 這裡不顯示具體 Key，只顯示狀態，比較美觀且安全
        st.success("✅ 系統已就緒 (三金鑰輪替中)")
    else:
        st.warning("⚠️ 未偵測到雲端 Key，請手動輸入")
        api_key_input = st.text_input("請輸入 Google API Key", type="password")
        api_key = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    
    # API 健檢
    with st.expander("🔍 API 連線狀態檢測"):
        if st.button("檢測當前線路"):
            if not api_key:
                st.error("❌ 未偵測到 API Key")
            else:
                try:
                    # 簡單測試連線
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
        'gemini-1.5-flash', 'gemini-1.5-pro'
    ]
    model_option = st.selectbox("🤖 選擇 AI 模型", user_available_models, index=0)
    
    st.markdown("---")
    
    with st.expander("📚 大考中心評分標準 (點擊展開)"):
        st.markdown("""
        **依據 113 年學測統計數據校正：**
        **🏆 頂標 (15-20分)** - 僅前 7.8% 考生。
        **👍 前標 (12-14分)** - 約前 20% 考生。
        **😐 均標 (9-11分)** - 約 50% 考生落點。
        **📉 後標 (0-8分)** - 內容貧乏或嚴重離題。
        """)

st.title("💯 英級棒!! 學測英文作文 AI 批改 APP")
st.caption("專為台灣高中生打造，依照大考中心數據嚴格校正的模擬閱卷系統。")

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
            return f"⚠️ 連線錯誤 (Status {response.status_code}): {response.text}"
    except Exception as e:
        return f"⚠️ 系統錯誤: {str(e)}"

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
                    prompt_gen = """
                    角色：你是一位資深的高中英文學測出題老師。
                    任務：請從以下領域中選一個貼近台灣高中生生活的主題：
                    「食衣住行育樂、人際關係、校園生活、親情、友情、自我成長、科技與生活」。
                    輸出要求：
                    1. 絕對不要提到「隨機選出」或「主題是...」這類字眼。
                    2. 全中文描述，模擬學測考卷的題目呈現方式。
                    3. 格式包含：題目引文、第一段引導、第二段引導。
                    """
                    # 每次呼叫都重新抽一把鑰匙
                    current_key = get_random_api_key() or api_key
                    result = call_gemini_api(prompt_gen, current_key, model_option)
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
        st.warning("⚠️ 尚未設定題目")

    col_demo, col_empty = st.columns([1, 4])
    with col_demo:
        if st.button("📝 載入示範作文 (Demo)"):
            st.session_state.essay_content = """I think that robots will become helpful assistants in our future daily lives. For example, they can help us do household chores, such as sweeping the floor, washing the dishes, and taking out the garbage. With their assistance, we can save a lot of time and energy to do other meaningful things.
However, despite the convenience robots may bring, I am worried that they might make us lazy. If we rely on them too much, we might lose the ability to take care of ourselves. Therefore, while enjoying the benefits of technology, we should also remind ourselves not to be overly dependent on it."""

    user_essay = st.text_area("請在此輸入英文作文：", value=st.session_state.essay_content, height=250, key="essay_input")
    
    word_count = len(re.findall(r'\w+', user_essay))
    if word_count > 0:
        st.caption(f"📊 目前字數：{word_count} 字")

    if st.button("🚀 開始批改", type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ 請先設定 API Key！")
        elif not user_essay:
            st.warning("⚠️ 請輸入作文內容！")
        else:
            system_prompt = f"""
            # Role: 台灣學測英文作文「嚴格」閱卷委員
            # Objective: 根據 113 年學測得分統計數據進行「客觀且嚴格」的評分。
            # Context:
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # Task: 執行「三階段回饋」
            1. 嚴格評分 (內容/組織/文法/字彙 各 0-5 分) 並給予簡評。
            2. 文章訂正 (使用條列式，標出 🔴原句 🟢訂正 💡解析)。
            3. 學習資源 (提供 :blue[升級詞組] 與 :orange[加分句型])。
            請輸出完整 Markdown 報告。
            """
            
            with st.spinner(f"AI 閱卷官正在嚴格評分中..."):
                # 每次呼叫都重新抽一把鑰匙，確保負載平衡
                current_key = get_random_api_key() or api_key
                result = call_gemini_api(system_prompt, current_key, model_option)
                if "⚠️" in result:
                    st.error(result)
                else:
                    st.success("🎉 閱卷完成！")
                    st.markdown(result)
                    st.divider()
                    st.caption("📢 本批改結果僅供學習參考。")

st.markdown("---")
st.markdown("<div class='footer'>製作者：中央大學資管系二年級 蔡仁懋</div>", unsafe_allow_html=True)