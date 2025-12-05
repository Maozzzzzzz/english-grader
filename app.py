import streamlit as st
import google.generativeai as genai

# 頁面設定
st.set_page_config(page_title="學測英文作文AI批改名師", page_icon="📝", layout="wide")

# 側邊欄：設定與說明
with st.sidebar:
    st.title("⚙️ 設定")
    api_key = st.text_input("請輸入 Google API Key", type="password", help="請前往 Google AI Studio 免費申請")
    
    st.markdown("---")
    st.subheader("關於評分標準")
    st.info("""
    本模型依據 113 學年度學測英文作文評分標準：
    
    - **內容**: 主題清楚、細節具體完整。
    - **組織**: 重點分明、轉承語恰當。
    - **文法**: 句構變化豐富、幾無錯誤。
    - **字彙**: 用字精確、拼字正確。
    
    *本系統使用 Google Gemini 免費模型運算*
    """)

st.title("📝 高中學測英文作文 AI 批改 (免費版)")
st.markdown("專為台灣高中生設計，提供像補習班老師一樣的「手術式」修改建議。")

# 初始化 Session State
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""

# 分頁設計
tab1, tab2 = st.tabs(["🎲 題目設定", "✍️ 作文批改"])

# --- Tab 1: 題目設定 ---
with tab1:
    st.subheader("題目來源")
    topic_source = st.radio("選擇題目來源", ["自行上傳/輸入題目", "請 AI 幫我出題 (食衣住行育樂)"])
    
    current_topic = ""
    
    if topic_source == "請 AI 幫我出題 (食衣住行育樂)":
        if st.button("✨ 立即生成模擬試題"):
            if not api_key:
                st.error("請先在左側輸入 Google API Key！")
            else:
                try:
                    # 設定 Gemini
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt_gen = """
                    你現在是台灣高中英文學測的出題老師。請從「食、衣、住、行、育、樂」中隨機選一個主題，
                    設計一個符合學測格式的英文作文題目。
                    格式要求：
                    1. 題目提示：一段約 50 字的中文背景描述，貼近台灣學生生活。
                    2. 清楚列出「第一段」與「第二段」必須涵蓋的內容。
                    請直接輸出題目內容即可。
                    """
                    with st.spinner("正在絞盡腦汁出題中..."):
                        response = model.generate_content(prompt_gen)
                        st.session_state.generated_topic = response.text
                except Exception as e:
                    st.error(f"出題錯誤：{e}")
        
        if st.session_state.generated_topic:
            st.success("出題完成！")
            st.markdown(st.session_state.generated_topic)
            current_topic = st.session_state.generated_topic

    else:
        current_topic = st.text_area("請輸入題目說明 (或貼上題目文字)", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗... 第一段請描述... 第二段請說明...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("上傳你的作文")
    
    user_essay = st.text_area("請在此輸入你的英文作文 (建議至少 120 字)", height=300)
    
    if st.button("🚀 開始批改"):
        if not api_key:
            st.error("請先在左側輸入 API Key！")
        elif not user_essay:
            st.warning("請輸入作文內容！")
        else:
            try:
                # 設定 Gemini
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 核心 Prompt
                system_prompt = f"""
                你是一位台灣頂尖的高中英文補習班名師，專精於「大學學測英文作文」。
                
                題目：{current_topic}
                學生作文：{user_essay}
                
                請依據以下標準評分 (每項0-5分，總分20)：
                1. 內容 (Content): 切題度與細節。
                2. 組織 (Organization): 結構連貫性。
                3. 文法句構 (Grammar): 正確性與句型變化。
                4. 字彙拼字 (Vocabulary): 用字精準度。
                
                **分數控制**：中位數約 12 分，15 分以上為高標。

                請輸出以下 Markdown 格式：
                
                ## 📊 綜合評分: [總分]/20
                - **內容**: [分數]/5
                - **組織**: [分數]/5
                - **文法**: [分數]/5
                - **字彙**: [分數]/5

                ## 📝 老師總評
                (100字左右簡評)

                ## 🔍 手術式批改
                (挑出 3 個最具代表性的錯誤或可升級的句子)
                **1. [分類]**
                > **原文**: "..."
                > **❌ 問題**: ...
                > **✅ 名師升級**: "..."
                > **💡 解析**: ...

                ## 🚀 下一步練習建議
                """

                with st.spinner("老師正在仔細批改中 (使用 Google Gemini)..."):
                    response = model.generate_content(system_prompt)
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"批改錯誤：{e}")