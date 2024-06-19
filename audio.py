import pyaudio
import wave
import speech_recognition as sr
import threading
import os
# 设置参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "./temp/temp_wave_output.wav"

class Audio:
    
    def __init__(self):
        # 初始化PyAudio
        self.audio = pyaudio.PyAudio()
        # 全局变量
        self.frames = []
        self.recording = False
        self.recording_thread = None

    def start_recording(self):
        """ 开始录音

        轮询recording来确定是否停止录音,
        将录音记录在音频文件中
        """
        self.recording = True
    
        # 开启音频流
        stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        print("开始录音，请说话...")
    
        while self.recording:
            data = stream.read(CHUNK)
            self.frames.append(data)
    
        # 结束音频流
        stream.stop_stream()
        stream.close()
    
        # 保存录音文件
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
    
        print("录音结束")
    
    def stop_recording(self):
        """ 停止录音

        修改recording为False以结束录音
        """
        self.recording = False
    
    def recognize_audio(self):
        """ 音频文件识别
        """
        recognizer = sr.Recognizer()
        with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='zh-CN')
                print("Google Web Speech API 识别结果：", text)
                return text
            except sr.UnknownValueError:
                print("Google Web Speech API 无法理解音频")
                return ""
            except sr.RequestError as e:
                print(f"无法请求Google Web Speech API服务; {e}")
                return ""

    def start(self):
        ''' 开始录音识别
        '''
        if not self.recording:
            self.recording_thread = threading.Thread(target=self.start_recording)
            self.recording_thread.start()
            print("录音开始")

    def stop(self):
        """ 停止录音识别

        需要先调用self.start来启动录音识别
        return: 返回录音识别结果
        """
        if self.recording:
            self.stop_recording()
            self.recording_thread.join()
            text = self.recognize_audio() # 识别音频
            os.remove(WAVE_OUTPUT_FILENAME)
            self.frames = []
            self.recording = False
            self.recording_thread = None
            print("录音停止")
            return text
