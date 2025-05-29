import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import h5py
import json
import os
import glob

qpos_data = None

# 读取hdf5文件中的图片
def load_image(frame_index):
    # with h5py.File(hdf5_file, 'r') as f:
    #     img_data = f['frames'][frame_index]  # 假设数据存储在 'images' 键下

    img_data = qpos_data[frame_index]  # 读取当前帧数据
    img = Image.fromarray(img_data.astype(np.uint8))  # 转换为PIL图像
    return ImageTk.PhotoImage(img)

# 更新当前帧的显示
def update_frame():
    global frame_index, current_subtask_text
    img = load_image(frame_index)
    panel.config(image=img)
    panel.image = img

    frame_label.config(text=f'Frame {frame_index + 1}/{total_frames}')  # 更新帧数显示

    global left_frame, task_info_labels, current_subtask
    
    # 可选：高亮当前选中的任务（改变背景色）
    for i, label in enumerate(task_info_labels):
        if i == current_subtask:
            label.config(bg="lightblue")  # 高亮当前任务
        else:
            label.config(bg="white")  # 恢复其他任务背景

# 读取json文件中的subtasks
def load_subtasks(json_file):
    with open(json_file, 'r') as f:
        subtasks = json.load(f)
    # return subtasks['sub-tasks']
    return subtasks

# 处理标签的输入
def add_label(event):
    global frame_index, current_subtask, labels, json_filename, current_subtask_text
    subtasks = load_subtasks(json_filename)
    subtask_label = subtasks[current_subtask]
    
    # 标记当前帧
    labels.append({'frame': frame_index + 1, 'label': subtask_label})
    print(f"Label '{subtask_label}' added at frame {frame_index + 1}")
    
    # 如果标注完了，切换到下一个subtask
    current_subtask += 1

    if current_subtask >= len(subtasks):  # 如果所有subtask都标注完了
        messagebox.showinfo("Task Complete", "All subtasks have been labeled!")
    else:
        # 跳转到下一个subtask的开始帧
        # subtask_start_frame = subtasks[current_subtask]['start_frame']
        # frame_index = subtask_start_frame - 1  # 下一个subtask的起始帧
        update_frame()

# 保存标签数据
def save_labels():
    
    json_filename = os.path.join(task["task_name"], f"{hdf5_name_without_extension}_manual.json")
    with open(json_filename, 'w') as f:
        json.dump(labels, f, indent=4)
    print("Labels saved to labels.json")
    exit()

# 切换到下一帧
def next_frame(event):
    global frame_index
    if frame_index < total_frames - 1:
        frame_index += 1
        update_frame()

# 切换到上一帧
def prev_frame(event):
    global frame_index
    if frame_index > 0:
        frame_index -= 1
        update_frame()

task_list = [
    {
        # "task_name": "./new_data/rearrange_coke/rearrange_coke_v0",
        "task_name": "/home/yan/Liusong/DataProcessing/file/video",
    },
        ]
parent_dir = None

for task in task_list:

    parent_dir = os.path.dirname(task["task_name"])
    hdf5_dir = os.path.join(parent_dir, "hdf5")
    # 使用 glob 模块获取该目录下所有 .hdf5 文件的路径
    hdf5_files = glob.glob(os.path.join(hdf5_dir, "*.hdf5"))
    hdf5_files = sorted(hdf5_files)
    # for hdf5_file in hdf5_files:
    hdf5_file = hdf5_files[5]#######################################################-------------------

    with h5py.File(hdf5_file, 'r') as f:
        qpos_data = np.array(f['frames'])  
    # 初始化
    frame_index = 0
    labels = []  # 存储标注结果

    total_frames = qpos_data.shape[0] # 假设总帧数为180
    # total_frames = 180

    hdf5_name = os.path.basename(hdf5_file)

    hdf5_name_without_extension = os.path.splitext(hdf5_name)[0]
    
    # 保存为 JSON 文件
    parent_dir = os.path.dirname(task["task_name"])
    json_dir = os.path.join(parent_dir, "json")
    json_filename = os.path.join(json_dir, f"{hdf5_name_without_extension}_manual.json")

    current_subtask = 0 




# # 创建GUI界面
root = tk.Tk()
root.title("Frame Labeling Tool")


# 创建左边 Frame（放 task_info）
left_frame = tk.Frame(root)
left_frame.grid(row=1, column=0, sticky="w", padx=10, pady=5)

# 创建右边 Frame（放图片）
right_frame = tk.Frame(root)
right_frame.grid(row=1, column=1, sticky="e", padx=10, pady=5)

# 显示当前帧数（顶部）
frame_label = tk.Label(root, text=f'Frame {frame_index + 1}/{total_frames}', font=("Arial", 24))
frame_label.grid(row=0, column=0, columnspan=2, sticky="w")

task_info_labels = []  # 用于存储所有 task_info 标签

# 显示当前subtask的信息（左边 Frame）
json_dir = os.path.join(parent_dir, "json")
json_filename = os.path.join(json_dir, f"{hdf5_name_without_extension}.json")
subtasks = load_subtasks(json_filename)
for i in range(len(subtasks)):
    current_subtask_text = subtasks[i]['content']
    task_info = tk.Label(left_frame, text=current_subtask_text, font=("Arial", 12))
    task_info.grid(row=i, column=0, sticky="w", padx=5, pady=2)  # 在 left_frame 里排列

    task_info_labels.append(task_info)  # 存储标签


# 显示图片的区域（右边 Frame）
img = load_image(frame_index)
panel = tk.Label(right_frame, image=img)
panel.image = img
panel.pack()  # 在 right_frame 里用 pack() 或 grid()



# 绑定键盘事件
root.bind("<Right>", next_frame)  # 右键切换到下一帧
root.bind("<Left>", prev_frame)   # 左键切换到上一帧

# 绑定按键事件，Space键进行标注
root.bind("<space>", add_label)

# 按ESC键保存并结束
root.bind("<Escape>", lambda e: save_labels())

# 进入事件循环
update_frame()  # 初始化时加载第一帧
root.mainloop()
