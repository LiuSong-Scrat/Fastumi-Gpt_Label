import base64
from openai import OpenAI
import json
import glob
import cv2 
import os
import re


client = OpenAI(
    base_url="http://35.220.164.252:3888/v1/",
    api_key=""
)


prompt_dir = '/home/yan/Liusong/DataProcessing/prompt_en.txt'
task_list = [
    {
        "task_name": "/home/yan/Liusong/DataProcessing/video_half",
        # "task_instruction": "Please open the shoebox, first place one shoe inside, then place the other shoe inside as well." 
        "task_instruction": "Please grab the leaves and bread to make sandwiches."  
        # "task_instruction": "Please grab the bottle and pour the water into the cup"
        # "task_instruction": "Please place the fork and spoon into the utensil holder."
    },
        ]

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


for task in task_list:

    # 使用 glob 模块获取该目录下所有 .mp4 文件的路径
    video_files = glob.glob(os.path.join(task["task_name"], "*.mp4"))
    video_files = sorted(video_files)

    for video_file in video_files:

        video_file = video_files[0]
        video = cv2.VideoCapture(video_file)
        print('load video:', video_file)
        base64Frames = []

        interval = 3
        count = 0
        while video.isOpened():
            success, frame = video.read()
            
            if not success:
                break

            if count % interval == 0:
                _, buffer = cv2.imencode(".jpg", frame)
                base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
            count += 1

        video.release()
        
        task_instruction = task["task_instruction"]
        image_number = str(len(base64Frames))
        with open(prompt_dir, 'r', encoding='utf-8') as file:
            content_prompt = file.read()
        content = content_prompt.replace('#TASK_INSTRUCTION#', task_instruction)    
        content = content_prompt.replace('#Number#', image_number)  

        print("frames read: ", len(base64Frames))

        slice = len(base64Frames) // 2
        base64Frames_front = base64Frames[:slice]
        base64Frames_back = base64Frames[slice:]

        interval_sample = 5
        print("interval_sample: ", interval_sample)
        print('input num:', len(base64Frames_front[0::interval_sample]))
        
        PROMPT_MESSAGES = [
            {
                "role": "user",
                "content": [
                    f"{content}",
                    # *map(lambda x: {"image": x, "resize": 786}, base64Frames[0::18]),
                    *map(lambda x: {"type": "image_url", 
                                "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "auto"}}, base64Frames_back[0::interval_sample]),
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
        json_filename = os.path.join(task["task_name"], f"{video_name_without_extension}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"JSON file saved as {json_filename}")
        print("=========================================")

        exit()

