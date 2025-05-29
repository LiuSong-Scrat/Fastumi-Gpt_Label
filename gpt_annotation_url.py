import base64
from openai import OpenAI
import openai
import json
import glob
import cv2 
import os
import re
import time
import threading
import h5py
import numpy as np
import cv2

client = OpenAI(
    base_url="http://35.220.164.252:3888/v1/",
    api_key="sk-dmDU1ULZle1tTmiS0SLT3nmLnKMf3b8QLifyG2PnCMe7E1Ae"
)

prompt_dir = '/home/yan/Liusong/DataProcessing/prompt_en.txt'
task_list = [
    {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/clean_table",
        "task_instruction": "Please grab the rag, and clean the stains off the table." 
    },
    {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/close_ricecooker",
        "task_instruction": "Please close the ricecooker." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/cover_beef",
        "task_instruction": "Please pick up the pot lid and then cover the steak with it." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/fold_tower",
        "task_instruction": "Please fold the tower." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/hotdog_in_roaster",
        "task_instruction": "Please open the roaster, and put the hotdog inside"  
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/open_container",
        "task_instruction": "Please subtask what you see." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/open_drawer",
        "task_instruction": "Please open the drawer." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/open_ricecooker",
        "task_instruction": "Please open the ricecooker." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/open_roaster",
        "task_instruction": "Please open the roaster." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/open_suitcase",
        "task_instruction": "Please open the suitcase." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/pick_bear",
        "task_instruction": "Please pick the bear toy, and put it inside the box." 
    },
        {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/pick_cup",
        "task_instruction": "Please pick up the cup, and place it on the coaster." 
    },
            {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/pick_lid",
        "task_instruction": "Please pick up the lid, and place it inside the box." 
    },
            {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/pick_pen",
        "task_instruction": "Please pick up the pen, and place it inside the pen holder." 
    },
                {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/place_plate",
        "task_instruction": "Please pick up the plate and place it on the tray." 
    },
            {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/place_pot",
        "task_instruction": "Please pick up the pot, and place it on the induction cooker." 
    },
            {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/pour_coke",
        "task_instruction": " Please pick the coke, and pour the water into the cup. And then place the coke on the coaster" 
    },
            {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/rearrange_coke",
        "task_instruction": "Please pick up the coke, and place it on the second shelf. " 
    },
            {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/sweep_trash",
        "task_instruction": "Please grasb the broom, and then sweep the trash into the dustpan. And then place the broom to the initial place." 
    },
            {
        "task_name": "/home/yan/Liusong/Workspace/hdf5/unplug_charger",
        "task_instruction": "Please unplug the charger." 
    },

    
        ]




def get_gpt_label(params,task,video_file):
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
    parent_dir = os.path.dirname(video_file)
    json_dir = os.path.join(parent_dir, "json")

    # 确保json文件夹存在
    os.makedirs(json_dir, exist_ok=True)
    json_filename = os.path.join(json_dir, f"{video_name_without_extension}.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"JSON file saved as {json_filename}")
    print("=========================================")
 






for task in task_list:
    threads = []
    # 使用 glob 模块获取该目录下所有 .mp4 文件的路径
    video_files = glob.glob(os.path.join(task["task_name"], "*.hdf5"))
    video_files = sorted(video_files)
    for sno,video_file in enumerate(video_files):
        
        with h5py.File(video_file, 'r') as f:
            qpos_data = np.array(f['observations']['images']['front'])  


        print('load video:', video_file)
        base64Frames = []
        ## 将60帧的视频转为20帧   hdf5为20帧
        interval = 1
        count = 0
        for img in qpos_data:
            frame = img
            if count % interval == 0:
                _, buffer = cv2.imencode(".jpg", frame)
                base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
            count += 1

        #     cv2.imshow("frame",frame)
        #     cv2.waitKey(1)
        # #See the files video and add the instruction label
        # input_task_instruction = input("please describe what you see: ")
        # if input_task_instruction!='':
        #     task["task_instruction"]=input_task_instruction
        # break


        
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
            "temperature": 0.8,
        }

        t = threading.Thread(target=get_gpt_label,args=(params, task, video_file))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
            
