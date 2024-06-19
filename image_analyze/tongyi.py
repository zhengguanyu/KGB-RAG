
from image_analyze.util import write_image
from config import tongyi_config
from http import HTTPStatus
import dashscope
import os
def analyze_image(image, text): 
    """图像分析

    image: streamlit UploadedFile 格式
    text: 文本
    """
    new_file_name = 'temp_tongyi_image.' + image.name.split('.')[-1]
    write_image(image,f"./temp/{new_file_name}")
    
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"./temp/{new_file_name}"},
                {"text": text}
            ]
        }
    ]
    response = dashscope.MultiModalConversation.call(model='qwen-vl-plus',
                                                     messages=messages,api_key=tongyi_config.DASHSCOPE_API_KEY)
    # The response status_code is HTTPStatus.OK indicate success,
    # otherwise indicate request is failed, you can get error code
    # and message from code and message.
    if response.status_code == HTTPStatus.OK:
        os.remove(f"./temp/{new_file_name}")
        return response['output']['choices'][0]['message']['content'][0]['text']
    else:
        os.remove(f"./temp/{new_file_name}")
        print(response.code)  # The error code.
        print(response.message)  # The error message.
   