import base64
from streamlit.runtime.uploaded_file_manager import UploadedFile
import os
def encode_image(image: UploadedFile):
  """ 对图像进行编码
    
  image: streamlit UploadedFile格式
  return: 图片的base64编码
  """
  file_contents = image.read()
  base64_image = base64.b64encode(file_contents).decode('utf-8')
  return base64_image

def write_image(image:UploadedFile, filename:str):
  with open(filename, "wb") as f:
    f.write(image.getbuffer())