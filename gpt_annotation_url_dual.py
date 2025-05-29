import base64
from openai import OpenAI
import openai
import json
import glob
import cv2 
import os
import re
import time


client = OpenAI(
    base_url="http://35.220.164.252:3888/v1/",
    api_key=""
)

prompt_dir = '/home/yan/Liusong/DataProcessing/prompt_en.txt'
task_list = [
    {
        "task_name": "/home/yan/Liusong/DataProcessing/file/video",
        # "task_instruction": "Press the button to open the rice cooker lid, take out the spoon and scoop a spoonful of rice into the rice cooker, then place the spoon and close the lid. "  
        # "task_instruction": "Put the toothbrush and toothpaste into the cup, then place the cup on the coaster."  
        # "task_instruction": "Remove all plugs from the power strip."  
        # "task_instruction": "Place the pot filled with soybeans on top of the induction cooker."  
        "task_instruction": "Please open the microwave, and put the bread inside, and then close the microwave."  
        # "task_instruction": "Please open the shoebox, first place one shoe inside, then place the other shoe inside as well." 
        # "task_instruction": "Please grab the leaves and bread to make sandwiches"  
        # "task_instruction": "Please pick up the bottle, pour the water into the cup, put the bottle down on the table"
        # "task_instruction": "Please place the fork and spoon into the utensil holder"
        # "task_instruction": "Please pick up the cola and place it on the second layer of the cabinet" 
    },
        ]


for task in task_list:

    # 使用 glob 模块获取该目录下所有 .mp4 文件的路径
    video_files = glob.glob(os.path.join(task["task_name"], "*.mp4"))
    video_files = sorted(video_files)

    video_file = video_files[0]  
    video = cv2.VideoCapture(video_file)

    print('load video:', video_file)
    base64Frames = []

    ## 将60帧的视频转为20帧
    interval = 3
    count = 0
    while video.isOpened():
        success, frame= video.read()

        if not success:
            break


        if count % interval == 0:
            _, buffer = cv2.imencode(".jpg", frame)
            base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        count += 1

    video.release()
    
    ## 
    interval_sample = 5
    image_number = str(len(base64Frames[0::interval_sample]))
    
    task_instruction = task["task_instruction"]

    with open(prompt_dir, 'r', encoding='utf-8') as file:
        content_prompt = file.read()

    content_prompt = content_prompt.replace('#TASK_INSTRUCTION#', task_instruction)    
    content = content_prompt.replace('#Number#', image_number)  
    
    print("interval_sample: ", interval_sample)
    print("frames read: ", len(base64Frames))
    print('input num:', image_number)
    
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                f"{content}",
                # *map(lambda x: {"image": x, "resize": 786}, base64Frames[0::18]),
                *map(lambda x: {"type": "image_url", 
                            "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "auto"}}, base64Frames[0::interval_sample]),
            ],

        },
    ]
    params = {
        "model": "gpt-4o",
        "messages": PROMPT_MESSAGES,
        # "response_format" : {"type": "json_object"},
        "max_tokens": 500,
        "temperature": 0.6,
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

        # parts = step.split("---frames: ")
        # action = parts[0]
        # frames = parts[1].strip() 

        content_output = {
            "step": i + 1,
            "content": step,
            # "frames": frames,
        }
        data.append(content_output)
        # print(step)
        
    # 获取当前视频文件的名称（去掉路径和扩展名）
    video_name = os.path.basename(video_file)
    video_name_without_extension = os.path.splitext(video_name)[0]
    
    # 保存为 JSON 文件
    parent_dir = os.path.dirname(task["task_name"])
    json_dir = os.path.join(parent_dir, "json")

    # 确保json文件夹存在
    os.makedirs(json_dir, exist_ok=True)
    json_filename = os.path.join(json_dir, f"{video_name_without_extension}.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"JSON file saved as {json_filename}")
    print("=========================================")

    exit()

