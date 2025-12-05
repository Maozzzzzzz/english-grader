import streamlit as st
import google.generativeai as genai

# 頁面設定：更換了標題與圖示
st.set_page_config(
    page_title="英級棒!! 學測英文作文AI批改APP", 
    page_icon="💯", 
    layout="wide"
)

# --- 側邊欄設計 ---
with st.sidebar:
    st.title("⚙️ 設定")
    api_key = st.text_input("請輸入 Google API Key", type="password", help="請前往 Google AI Studio 免費申請")
    
    st.markdown("---")
    st.subheader("📚 大考中心評分機制")
    st.info("""
    本系統嚴格依照大學入學考試中心（CEEC）英文作文評分標準進行批改，滿分 20 分。
    
    **四大評分項目 (各佔 0~5 分)：**
    
    1. **內容 (Content)**: 
       - 是否切題？
       - 論點是否有具體細節支持？
       
    2. **組織 (Organization)**: 
       - 是否有明確的開頭、發展、結尾？
       - 轉折詞 (Transitions) 使用是否流暢？
       
    3. **文法句構 (Grammar)**: 
       - 文法正確性。
       - 句型變化的豐富度。
       
    4. **字彙拼字 (Vocabulary)**: 
       - 用字精準度 (搭配詞)。
       - 拼字與大小寫正確性。
    """)

# --- 主頁面標題 ---
st.title("💯 英級棒!! 學測英文作文 AI 批改 APP")
st.markdown("### 專為台灣高中生打造，你的 24 小時專屬英文家教！")
st.markdown("由 AI 名師提供「手術式」精準批改，直擊你的寫作痛點。")

# 初始化 Session State (用來記憶出題內容)
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""

# 分頁設計
tab1, tab2 = st.tabs(["🎲 題目設定", "✍️ 作文批改"])

# --- Tab 1: 題目設定 ---
with tab1:
    st.subheader("📍 步驟一：設定題目")
    topic_source = st.radio("請選擇題目來源：", ["自行上傳/輸入題目", "請 AI 幫我出題 (食衣住行育樂)"])
    
    current_topic = ""
    
    if topic_source == "請 AI 幫我出題 (食衣住行育樂)":
        if st.button("✨ 立即生成模擬試題"):
            if not api_key:
                st.error("請先在左側輸入 Google API Key 才能出題喔！")
            else:
                try:
                    # 設定 Gemini (使用 gemini-pro)
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-pro')
                    
                    prompt_gen = """
                    你現在是台灣高中英文學測的出題老師。請從「食、衣、住、行、育、樂」中隨機選一個主題，
                    設計一個符合學測格式的英文作文題目。
                    格式要求：
                    1. 題目提示：一段約 50 字的繁體中文背景描述，貼近台灣學生生活。
                    2. 清楚列出「第一段」與「第二段」必須涵蓋的內容。
                    請直接輸出題目內容即可，不要有多餘的開場白。
                    """
                    with st.spinner("正在絞盡腦汁出題中..."):
                        response = model.generate_content(prompt_gen)
                        st.session_state.generated_topic = response.text
                except Exception as e:
                    st.error(f"出題錯誤，請檢查 API Key 是否正確。錯誤訊息：{e}")
        
        if st.session_state.generated_topic:
            st.success("出題完成！")
            st.markdown(st.session_state.generated_topic)
            current_topic = st.session_state.generated_topic

    else:
        current_topic = st.text_area("請輸入題目說明 (或貼上題目文字)", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗... 第一段請描述... 第二段請說明...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("📍 步驟二：輸入作文並批改")
    
    user_essay = st.text_area("請在此輸入你的英文作文 (建議至少 120 字)", height=300)
    
    if st.button("🚀 英級棒批改開始！"):
        if not api_key:
            st.error("請先在左側輸入 API Key！")
        elif not user_essay:
            st.warning("請輸入作文內容！")
        else:
            try:
                # 設定 Gemini (使用 gemini-pro)
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-pro')
                
                # 核心 System Prompt
                system_prompt = f"""
                你是一位台灣頂尖的高中英文補習班名師，專精於「大學學測英文作文」。
                你的風格專業、幽默且一針見血，目標是幫學生在學測拿到 15 級分。
                
                【題目資訊】
                {current_topic}
                
                【學生作文】
                {user_essay}
                
                【評分任務】
                請依據「大考中心」評分標準進行評分 (每項 0-5 分，滿分 20)：
                1. 內容 (Content): 切題度與細節支持。
                2. 組織 (Organization): 結構連貫性與轉承語。
                3. 文法句構 (Grammar): 正確性與句型變化。
                4. 字彙拼字 (Vocabulary): 用字精準度與拼字。
                
                **分數控制**：中位數約 12 分，15 分以上為高標。

                【輸出格式 (Markdown)】
                請務必按照以下格式輸出：
                
                ## 📊 綜合評分: [總分]/20
                - **內容**: [分數]/5
                - **組織**: [分數]/5
                - **文法**: [分數]/5
                - **字彙**: [分數]/5

                ## 📝 名師總評
                (約 100 字，先肯定優點，再指出主要弱點。請用鼓勵但嚴格的語氣。)

                ## 🔍 手術式批改 (重點改進)
                (請挑出 3 個最具代表性的錯誤或可升級的句子，這是最精華的部分)
                **1. [分類：如 文法/中式英文/句型]**
                > **原文**: "..."
                > **❌ 問題**: ...
                > **✅ 名師升級**: "..."
                > **💡 解析**: ...

                **2. [分類]**
                ...

                **3. [分類]**
                ...

                ## 🚀 下一步練習建議
                (給出一個具體可執行的建議)
                """

                with st.spinner("AI 名師正在仔細批改中..."):
                    response = model.generate_content(system_prompt)
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"批改時發生錯誤：{e}")