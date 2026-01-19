import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

# 1. 页面配置
st.set_page_config(page_title="DeepSeek Pro", page_icon="🔒", layout="wide")

# ==========================================
# 🔐 核心代码：简易登录门禁
# ==========================================

# A. 初始化登录状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# B. 定义一个函数：检查密码
def check_password():
    # 🔴 在这里修改你的密码！
    # 只有输入这个密码，才能进入 App
    if st.session_state.password_input == "123456": 
        st.session_state.logged_in = True
    else:
        st.error("密码错误，请重试 ❌")

# C. 如果没登录，就显示输入框，然后停止运行后面的代码
if not st.session_state.logged_in:
    st.markdown("## 🔒 请输入访问密码")
    st.text_input(
        "Password", 
        type="password",  # 隐藏输入的字符
        key="password_input", 
        on_change=check_password
    )
    st.stop()  # 🛑 关键：如果没有登录，程序在这里直接停止！后面的代码都不会执行

# ==========================================
# 👇 下面是原本的 App 代码（登录后才会看到）
# ==========================================

st.title("⚡ DeepSeek Pro (加密流式版)")

# 2. 配置 API (🔴 填你的 Key)
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# 初始化消息
if "messages" not in st.session_state:
    st.session_state.messages = []

# === 侧边栏 ===
with st.sidebar:
    st.success("✅ 已登录")
    # 添加一个登出按钮
    if st.button("🚪 退出登录"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.divider()
    
    st.header("🎛️ 控制面板")
    creativity = st.slider("🧠 创造力", 0.0, 1.3, 0.7)
    
    st.divider()
    
    uploaded_file = st.file_uploader("📂 上传文档", type=["pdf", "txt"])
    file_content = ""
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".pdf"):
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    file_content += page.extract_text() or ""
            else:
                file_content = uploaded_file.read().decode("utf-8")
            st.success(f"已加载: {uploaded_file.name}")
        except:
            st.error("读取失败")

    st.divider()
    if st.button("🗑️ 清空记录"):
        st.session_state.messages = []
        st.rerun()

# === 主界面聊天逻辑 ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入问题..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    final_messages = []
    if file_content:
        final_messages.append({"role": "system", "content": f"基于文档回答：\n{file_content}"})
    else:
        final_messages.append({"role": "system", "content": "你是个好助手。"})
    
    final_messages.extend(st.session_state.messages)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=final_messages,
                temperature=creativity,
                stream=True 
            )
            response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"出错: {e}")