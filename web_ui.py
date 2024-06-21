import streamlit as st
from streamlit_float import *
import api
from web_ui_func import *

# 初始化session
session_init()
#设置页面标题、图标、布局
st.set_page_config(page_title="KGB-RAG", page_icon='./image/logo.png',layout="wide")
st.logo(image='./image/logo.png', icon_image='./image/logo.png')
#### 左边设置区

left_settings = st.sidebar

left_settings.image('./image/logo.png')


# 查询limit,参数一是标题,参数二是最小值,参数三是最大值,参数四是默认值,参数五是步长，返回值是当前值
limit = left_settings.slider("Cypher Limit", 0, 20, 10, 1)
if limit != st.session_state.limit:
    st.session_state.limit = limit
    api.change_limit(limit)
# --------------
left_settings.divider()
# 模型选择:
model_name = left_settings.selectbox(
    '模型选择',
    ('gpt-4o','gpt-4', 'gpt-3.5-turbo','qwen','glm-4')
)
# 如果当前选择的模型和之前的不一样,更换模型
if model_name != st.session_state.model_name:
    st.session_state.model_name = model_name
    api.change_model(model=model_name)
    
left_settings.divider()

history_window = left_settings.number_input("历史对话轮次", 0, 10, 5, 1)
if history_window != st.session_state.history_window:
    st.session_state.history_window = history_window
    clear_chat()

# 图片相关
left_settings.divider()
st.session_state.image = left_settings.file_uploader("上传图片", type=["png", "jpg", "jpeg","webp"])
if st.session_state.image != None:
    left_settings.image(st.session_state.image)
imgModelName = left_settings.selectbox(
    "图片输入处理模型",
    ("tongyi","gpt","zhipu")
)
if imgModelName != st.session_state.imgModelName:
    st.session_state.imgModelName = imgModelName

left_settings.button("清空对话记录",on_click=clear_chat)

#### 以下是聊天区

if "messages" not in st.session_state.keys(): 
    st.session_state.messages = [
        {"role": "assistant", "content": "快来问吧! :kissing_heart:"}
    ] # 初始化聊天记录


# 聊天区的输入框
user_input()

if st.session_state.query != "":
    st.session_state.messages.append({"role": "user", "content": st.session_state.query})
    st.session_state.query = ""

# 显示聊天记录
for message in st.session_state.messages: 
    if message["role"] == "Image":
        with st.chat_message("Image",avatar=":material/photo_library:"):
            st.image(message["content"])
    elif message["role"] == "user":
        with st.chat_message("user",avatar=":material/face:"):
            st.write(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant",avatar=":material/smart_toy:"):
            st.write(message["content"])
    scroll_down()
        
# 如果聊天区的最后一句话不是ai说的,回答用户问题
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant",avatar=":material/smart_toy:"):
        with st.spinner("Thinking..."):
            query = st.session_state.messages[-1]["content"]
            # 如果问题带有图片
            if st.session_state.messages[-2]["role"] == "Image":
                full_respose = api.analyze_image(st.session_state.messages[-2]["content"],query,st.session_state.imgModelName)
                st.write(full_respose)
            else:
                respose = api.chat_stream(query) # 获取答案
                full_respose = st.write_stream(respose)# 显示答案
            scroll_down()
            api.save_history(query,full_respose)
            st.session_state.messages.append({"role": "assistant", "content": full_respose})# 答案添加到聊天记录
current_theme = st.get_option('theme.base')
