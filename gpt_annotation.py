from IPython.display import display, Image, Audio

import cv2  # We're using OpenCV to read video, to install !pip install opencv-python
import base64
import time
from openai import OpenAI
import os
import requests
import re
import json
import glob

prompt_dir = './prompt_en.txt'
task_list = [
    {
        "task_name": "./new_data/rearrange_coke/rearrange_coke_v0",
        "task_instruction": "Please pick up the cola and place it on the second layer of the cabinet."  
    },
        ]
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

for task in task_list:
    # 使用 glob 模块获取该目录下所有 .mp4 文件的路径
    video_files = glob.glob(os.path.join(task["task_name"], "*.mp4"))
    for video_file in video_files:
       
        video = cv2.VideoCapture(video_file)

        base64Frames = []
        while video.isOpened():
            success, frame = video.read()
            if not success:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

        video.release()
        print(len(base64Frames), "frames read.")

        task_instruction = task["task_instruction"]
        with open(prompt_dir, 'r', encoding='utf-8') as file:
            content_prompt = file.read()
        content = content_prompt.replace('#TASK_INSTRUCTION#', task_instruction)    
        PROMPT_MESSAGES = [
            {
                "role": "user",
                "content": [
                    f"{content}",
                    # *map(lambda x: {"image": x, "resize": 786}, base64Frames[0::18]),
                    *map(lambda x: {"type": "image_url", 
                                "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "auto"}}, base64Frames[0::18]),
                ],
            },
        ]
        params = {
            "model": "gpt-4o",
            "messages": PROMPT_MESSAGES,
            "max_tokens": 500,
            "temperature": 0.8,
        }

        result = client.chat.completions.create(**params)
        outputs = result.choices[0].message.content
        # print(outputs)

        # 正则表达式
        pattern = r'```Subtasks([\s\S]*?)```'


        # 使用re.search()来匹配并提取内容
        match = re.search(pattern, outputs)
        match_content = match.group(0)
        
        # 使用正则表达式提取每个step的内容
        steps = re.findall(r"step\d+: (.+)", match_content)

        data = []
        for i, step in enumerate(steps):
            step = {
                "step": i + 1,
                "content": step
            }
            data.append(step)
            # print(step)
            
        # 获取当前视频文件的名称（去掉路径和扩展名）
        video_name = os.path.basename(video_file)
        video_name_without_extension = os.path.splitext(video_name)[0]
        
        # 保存为 JSON 文件
        json_filename = os.path.join(task["task_name"], f"{video_name_without_extension}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"JSON file saved as {json_filename}")
        print("=========================================")
        # exit()

