import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import h5py
import json
import os
import glob
import re

qpos_data = None
file_index = 6
hdf5_dir = None
hdf5_name_without_extension = None
hdf5_files = []
frame_index = 0
labels = []
current_subtask = [] 
total_frames = 0  
json_filename = None
json_filename_show = None
index_begin = 1
index_begin_gpt = 1
task_path = "/home/chenpengan/hny/hdf5s_song/"
task_list = glob.glob(os.path.join(task_path, "*"))
task_list = sorted(task_list)
# task_list = task_list[]
task_index = 0
task_info_labels = [] 


# 读取hdf5文件中的图片
def load_image(frame_index):
    img_data = qpos_data[frame_index]  # 读取当前帧数据
    img = Image.fromarray(img_data.astype(np.uint8))  # 转换为PIL图像
    
    # 获取原始尺寸
    w, h = img.size
    
    # 缩小一半
    img = img.resize((w // 2, h // 2))  # ANTIALIAS 提高缩放质量
    
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

    global frame_index, current_subtask, labels, json_filename_show, current_subtask_text
    subtasks = load_subtasks(json_filename_show)
    if current_subtask >= len(subtasks):
        return 
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


def interval_iou(a_start, a_end, b_start, b_end):
    inter_start = max(a_start, b_start)
    inter_end = min(a_end, b_end)
    inter_len = max(0, inter_end - inter_start)

    union_start = min(a_start, b_start)
    union_end = max(a_end, b_end)
    union_len = union_end - union_start

    return inter_len / union_len if union_len > 0 else 0

def compute_score(label):
    """
    计算标签的分数
    :param label: 标签内容
    :return: 分数
    """
    # 这里可以根据具体的标签内容计算分数
    # 例如，假设每个标签的分数为1
    global index_begin, index_begin_gpt
    score = 0
    for i in range(len(label)):
        gt_s = label[i]['frame']
        s = label[i]['label']
        if not s:
            continue
        s = str(s)
        numbers = list(map(int, re.findall(r'\d+', s)))
        numbers = numbers[1:]

        if len(numbers) < 2:
            score += interval_iou(index_begin_gpt, (numbers[0])*5, index_begin, gt_s)
        else:
            score += interval_iou(index_begin_gpt, (numbers[-1])*5, index_begin, gt_s)
        
        index_begin = gt_s + 1
        index_begin_gpt = (numbers[-1])*5 + 1

    return score/ len(label) * 100 if label else 0

# 保存标签数据
def save_labels():
    
    global frame_index, current_subtask, labels, json_filename_show, current_subtask_text, task_index, hdf5_dir, index_begin, index_begin_gpt
    subtasks = load_subtasks(json_filename_show)

    if current_subtask >= len(subtasks):  # 如果所有subtask都标注完了
        print("All subtasks have been labeled, saving...")
    else:
        messagebox.showinfo("Wake Up!.", "Please finish all subtask before saving.")
        return

    global json_filename, file_index, hdf5_files, labels

    with open(json_filename, 'w') as f:
        json.dump(labels, f, indent=4)

    score = compute_score(labels)

    print("Save, score is ", score)

    score_path = os.path.join(hdf5_dir, "tasks_scores.txt")
    with open(score_path, "a") as f:
        f.write(f"{json_filename_show}: {score}\n")

    current_subtask = 0
    file_index = file_index + 1

    index_begin = 1
    index_begin_gpt = 1

    if file_index >= (len(hdf5_files)):

        file_index = 0

        if task_index < len(task_list):
            task_index += 1

        hdf5_dir = task_list[task_index]
        # 使用 glob 模块获取该目录下所有 .hdf5 文件的路径
        hdf5_files = glob.glob(os.path.join(hdf5_dir, "*.hdf5"))
        hdf5_files = sorted(hdf5_files)
        file_index_label.config(text=f'File Index: {file_index + 1}/{len(hdf5_files)}')  # 更新文件索引显示
        
        score_path = os.path.join(hdf5_dir, "tasks_scores.txt")
        with open(score_path, "w") as f:
            pass
        
        load_task(hdf5_files, file_index)
        update_task_info()
        update_frame()
        return

    file_index_label.config(text=f'File Index: {file_index + 1}/{len(hdf5_files)}')  # 更新文件索引显示
    load_task(hdf5_files, file_index)
    update_task_info()
    update_frame()
    if task_index >= len(task_list):
        messagebox.showinfo("Task Complete", "All tasks have been labeled!")
        root.quit()


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




def print_hdf5_structure(file_path):
    def print_attrs(name, obj):
        print(name)
    
    with h5py.File(file_path, 'r') as f:
        f.visititems(print_attrs)


def load_task(task_list, file_index=0):
    """
    加载任务列表中的hdf5文件
    :param task_list: 任务列表
    :param file_index: 当前处理的hdf5文件索引
    :return: hdf5文件路径
    """

    hdf5_file = task_list[file_index]
    # print_hdf5_structure(hdf5_file)  # 打印hdf5文件结构

    global qpos_data, frame_index, labels, current_subtask, total_frames, hdf5_dir, hdf5_name_without_extension, json_filename, json_filename_show

    with h5py.File(hdf5_file, 'r') as f:
        qpos_data = np.array(f['observations']['images']['front'])  # 假设数据在 'observations/qpos' 路径下

    # 初始化
    
    frame_index = 0
    labels = []  # 存储标注结果
    current_subtask = 0 
    total_frames = qpos_data.shape[0] # 假设总帧数为180

    hdf5_name = os.path.basename(hdf5_file)
    hdf5_name_without_extension = os.path.splitext(hdf5_name)[0]
    
    # 保存为 JSON 文件
    json_dir = os.path.join(hdf5_dir, "json")
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    json_filename = os.path.join(json_dir, f"{hdf5_name_without_extension}_manual.json")
    json_filename_show = os.path.join(json_dir, f"{hdf5_name_without_extension}.json")
    

# for task in task_list:

hdf5_dir = task_list[task_index]
# 使用 glob 模块获取该目录下所有 .hdf5 文件的路径
hdf5_files = glob.glob(os.path.join(hdf5_dir, "*.hdf5"))
hdf5_files = sorted(hdf5_files)
score_path = os.path.join(hdf5_dir, "tasks_scores.txt")
with open(score_path, "w") as f:
    pass

load_task(hdf5_files, file_index)


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

file_index_label = tk.Label(root, text=f'File Index: {file_index + 1}/{len(hdf5_files)}', font=("Arial", 24))
file_index_label.grid(row=0, column=1, sticky="w")

def update_task_info():
    global task_info_labels, current_subtask_text, json_filename_show
    # 清除之前的标签
    for label in task_info_labels:
        label.destroy()
    
    task_info_labels.clear()  # 清空列表

    # 显示当前subtask的信息（左边 Frame）
    subtasks = load_subtasks(json_filename_show)
    for i in range(len(subtasks)):
        current_subtask_text = subtasks[i]['content']
        task_info = tk.Label(left_frame, text=current_subtask_text, font=("Arial", 12))
        task_info.grid(row=i, column=0, sticky="w", padx=5, pady=2)  # 在 left_frame 里排列

        task_info_labels.append(task_info)  # 存储标签

def init_image():
    global img, panel
    img = load_image(frame_index)
    panel = tk.Label(right_frame, image=img)
    panel.image = img
    panel.pack()  # 在 right_frame 里用 pack() 或 grid()


update_task_info()
# 显示图片的区域（右边 Frame）
init_image()

# 绑定键盘事件
root.bind("<Right>", next_frame)  # 右键切换到下一帧
root.bind("<Left>", prev_frame)   # 左键切换到上一帧

# 绑定按键事件，Space键进行标注
root.bind("<space>", add_label)

def exit_program(event):
    if messagebox.askokcancel("Exit", "Do you want to exit?"):
        root.quit()
root.bind("<Escape>", exit_program)

# 按ESC键保存并结束
root.bind("<s>", lambda e: save_labels())

# 进入事件循环
update_frame()  # 初始化时加载第一帧
root.mainloop()
