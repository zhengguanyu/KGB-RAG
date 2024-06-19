from zhipuai import ZhipuAI
from streamlit.runtime.uploaded_file_manager import UploadedFile

from image_analyze.util import encode_image
from config import zhipu_config


def analyze_image(image, text) : 
    """图像分析

    image: streamlit UploadedFile 格式
    text: 文本
    """
    image_type=image.type
    client = ZhipuAI(api_key=zhipu_config.ZHIPU_API_KEY) # 填写您自己的APIKey
    image = encode_image(image)

    response = client.chat.completions.create(
        model="glm-4v",  # 填写需要调用的模型名称
        messages=[
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": text
            },
            {
                "type": "image_url",
                "image_url": {
                    "url" : f"data:{image_type};base64,{image}"
                }
            }
            ]
        }
        ]
    )
    return response.choices[0].message.content