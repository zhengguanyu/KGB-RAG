from langchain_community.chat_models import ChatZhipuAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai.chat_models import ChatOpenAI
from streamlit.runtime.uploaded_file_manager import UploadedFile

from config import openai_config
from config import tongyi_config
from config import zhipu_config

from audio import Audio
import image_analyze.openai
import image_analyze.tongyi
import image_analyze.zhipu
from KGB_RAG import KGB_RAG
import image_analyze

kgb_rag = KGB_RAG()
audio = Audio()

def chat(query: str):
    """ 对话接口
    query: 问题
    return: 回答
    """
    return kgb_rag.chat(query=query,stream='no')

def chat_stream(query: str):
    """ 同步流式输出 对话接口
    query: 问题
    return: langchain的同步流迭代器
    """
    return kgb_rag.chat(query=query,stream='stream')

def chat_astream(query):
    """ 异步流式输出 对话接口
    query: 问题
    return: 答案的异步生成器
    """
    # 定义一个异步生成器
    async def generation():
        astream = kgb_rag.chat(query,'astream')
        async for chunk in astream:
            # yield 表示该函数不是'函数', 而是生成器
            # yield 在每次调用时起到return作用
            # 返回后会使生成器停滞在yield语句之后
            yield chunk.content
    # 返回生成器
    g = generation()
    return g

def save_history(query: str, answer: str):
    """ 保存对话历史接口

    query: human的提问
    answer: ai的回答
    """
    kgb_rag.save_history(query, answer)

def refresh_history(k: int):
    """刷新对话历史
    
    k: 记忆的轮数
    """
    kgb_rag.refresh_history(k=k)

def start_audio():
    """ 开始语音识别接口
    """
    audio.start()

def stop_audio():
    """ 停止语音识别接口
    """
    text = audio.stop()
    return text

def change_model(model: str):
    """ 修改模型接口

    model: 模型名称
    """
    llm = ''
    if model == 'qwen':
        llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
    elif model in ['gpt-4', 'gpt-4o', 'gpt-3.5-turbo']:
        llm = ChatOpenAI(model=model,
                         api_key=openai_config.OPENAI_API_KEY,
                         base_url=openai_config.base_url)
    elif model == 'glm-4':
        llm = ChatZhipuAI(model="glm-4",
                         api_key=zhipu_config.ZHIPU_API_KEY)
    else:
        llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)

    # 修改模型 
    kgb_rag.change_model(llm=llm)
    print('new model: ',llm.get_name())

def change_limit(limit: str):
    """ limit修改接口

    修改cypher语句的limit

    limit: 数量
    """
    kgb_rag.change_limit(limit=limit)

def analyze_image(image: UploadedFile, text: str, model: str=None):

    """图像分析接口

    image: streamlit UploadedFile 格式
    text: 一段文本
    model: 所选模型, tongyi, zhipu, gpt
    """
    print(image._file_urls)
    if model == 'tongyi':
        return image_analyze.tongyi.analyze_image(image, text)
    elif model == 'zhipu':
        return image_analyze.zhipu.analyze_image(image, text)
    elif model == 'gpt':
        return image_analyze.openai.analyze_image(image, text)
    else:
        # 默认使用gpt
        return image_analyze.openai.analyze_image(image, text)
