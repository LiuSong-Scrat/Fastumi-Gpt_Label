import os
import glob
import json
import tkinter as tk
from tkinter import messagebox

import numpy as np
import h5py
from PIL import Image, ImageTk

# ──────────────────────────────────────────────────────────────────────────────
# 配置区：请根据实际情况修改以下常量
# ──────────────────────────────────────────────────────────────────────────────

# 所有任务（每个任务为一个目录）的根路径
TASK_ROOT_PATH = "/home/chenpengan/hny/hdf5s_song/"

# 每个子任务 JSON 文件所在的子目录名（用于保存手工标注结果）
JSON_SUBDIR_NAME = "json"

# 每个任务目录下的子任务定义文件名
SUBTASK_DEFINITION_FILENAME = "subtask.json"


# ──────────────────────────────────────────────────────────────────────────────
# 全局变量（尽可能使用描述性变量名）
# ──────────────────────────────────────────────────────────────────────────────

# 当前任务目录下所有 .hdf5 文件的路径列表
hdf5_file_list = []

# 所有任务目录列表
all_task_dirs = []

# 索引用的变量（内部使用 0-based）
current_task_index = 0
current_file_index = 0

# 加载后的图像数据（ndarray）
image_frames = None

# 当前帧索引（0-based）
current_frame_index = 0

# 当前子任务的索引（0-based）
current_subtask_index = 0

# 存储已标注的结果：列表项为 dict，格式如 {'step': str, 'label': str, 'frame': "start-end"}
labeled_frames = []

# 记录上一次开始标注的帧（1-based）。初始值设为 1
last_frame_index = 1

# 总帧数
total_frames = 0

# 当前 HDF5 文件所在的目录路径
current_task_dir = None

# 当前 HDF5 文件名（不含扩展名）
current_hdf5_basename = None

# 当前任务目录下的子任务定义列表（此变量在 load_task_directory 中加载）
current_subtasks = []

# 保存标注结果的 JSON 文件完整路径
current_json_output_path = None

# Tkinter 界面相关
root = None
image_panel = None

# 顶部显示标签
frame_label_widget = None
file_index_label_widget = None
task_index_label_widget = None

# 用于手动输入索引的 Entry（1-based 显示）
task_index_entry = None
file_index_entry = None

subtask_label_widgets = []


# ──────────────────────────────────────────────────────────────────────────────
# 工具函数区
# ──────────────────────────────────────────────────────────────────────────────

def load_subtasks(json_path):
    """
    从一个 JSON 文件中加载子任务列表。
    JSON 文件结构示例：
    [
        {"content": "子任务1描述", "step": "Step1", ...},
        {"content": "子任务2描述", "step": "Step2", ...},
        ...
    ]
    :param json_path: 子任务 JSON 文件路径
    :return: 返回一个 Python 列表，每个元素为一个 dict，其中至少包含 'content' 和 'step' 字段
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        subtasks = json.load(f)
    return subtasks


# ──────────────────────────────────────────────────────────────────────────────
# HDF5 加载与初始化
# ──────────────────────────────────────────────────────────────────────────────

def load_hdf5_file(hdf5_path):
    """
    从指定的 HDF5 文件中读取图像序列数据，并初始化全局变量。
    :param hdf5_path: HDF5 文件完整路径
    """
    global image_frames
    with h5py.File(hdf5_path, 'r') as f:
        # 假设图像存储在路径 'observations/images/front'
        image_frames = np.array(f['observations']['images']['front'], dtype=np.uint8)


def initialize_task_file(hdf5_path):
    """
    给定一个 HDF5 文件路径，完成以下初始化：
      - 读取 image_frames
      - 设置 total_frames、current_frame_index、labeled_frames、current_subtask_index、last_frame_index
      - 更新 current_hdf5_basename、current_json_output_path
    :param hdf5_path: 当前要处理的 .hdf5 文件完整路径
    """
    global total_frames, current_frame_index, labeled_frames, current_subtask_index, last_frame_index
    global current_hdf5_basename, current_json_output_path

    # 1. 载入 HDF5 中的图像数据
    load_hdf5_file(hdf5_path)

    # 2. 初始化帧索引和标签信息
    current_frame_index = 0
    labeled_frames = []
    current_subtask_index = 0

    # 每个文件开始标注时，起始帧都从 1 开始
    last_frame_index = 1

    # 3. 设置总帧数
    total_frames = image_frames.shape[0]

    # 4. 当前 HDF5 文件的基础文件名（不含扩展名）
    current_hdf5_basename = os.path.splitext(os.path.basename(hdf5_path))[0]

    # 5. 确保 JSON 子目录存在
    json_dir = os.path.join(current_task_dir, JSON_SUBDIR_NAME)
    os.makedirs(json_dir, exist_ok=True)

    # 6. 设置 JSON 文件路径，用于保存本次手工标注结果
    current_json_output_path = os.path.join(
        json_dir, f"{current_hdf5_basename}.json"
    )


def load_task_directory(task_dir, file_idx=0):
    """
    给定一个任务目录（所有 HDF5 文件都在此目录下），完成：
      - 列出目录中所有 .hdf5 文件，排序后赋值给 hdf5_file_list
      - 加载同目录下的 subtask.json 到 current_subtasks
      - 加载指定索引的 HDF5 文件，调用 initialize_task_file()
      - 更新 UI 显示
    :param task_dir: 当前任务目录路径
    :param file_idx: 要加载的 HDF5 文件索引（0-based）
    """
    global hdf5_file_list, current_file_index, current_task_dir, current_subtasks

    current_task_dir = task_dir
    hdf5_file_list = sorted(glob.glob(os.path.join(task_dir, "*.hdf5")))
    current_file_index = file_idx

    # 读取该任务目录下的 subtask.json
    subtask_def_path = os.path.join(current_task_dir, SUBTASK_DEFINITION_FILENAME)
    if not os.path.isfile(subtask_def_path):
        raise FileNotFoundError(f"未找到子任务定义文件：{subtask_def_path}")
    current_subtasks = load_subtasks(subtask_def_path)

    # 加载指定索引的 HDF5 文件
    if 0 <= current_file_index < len(hdf5_file_list):
        initialize_task_file(hdf5_file_list[current_file_index])
    else:
        raise IndexError("File index out of range for this task directory.")


# ──────────────────────────────────────────────────────────────────────────────
# 图像显示与 UI 更新
# ──────────────────────────────────────────────────────────────────────────────

def load_current_frame_image(scale_half=True):
    """
    从全局 image_frames 中读取当前帧，将其转换为 PIL Image 再转为 ImageTk.PhotoImage。
    如果 scale_half=True，则宽高都缩小一半以加速显示。
    :return: ImageTk.PhotoImage 对象
    """
    frame_array = image_frames[current_frame_index]
    pil_img = Image.fromarray(frame_array)

    if scale_half:
        w, h = pil_img.size
        pil_img = pil_img.resize((w // 2, h // 2))

    return ImageTk.PhotoImage(pil_img)


def update_frame_display():
    """
    更新主界面上图像显示面板和帧号标签，并高亮当前子任务。
    """
    # 1. 更新图像
    img_tk = load_current_frame_image()
    image_panel.config(image=img_tk)
    image_panel.image = img_tk

    # 2. 更新帧号显示（1-based）
    frame_label_widget.config(
        text=f"Frame {current_frame_index + 1}/{total_frames}"
    )

    # 3. 高亮当前子任务（左侧列表）
    for idx, lbl in enumerate(subtask_label_widgets):
        lbl.config(bg="white")
        if idx == current_subtask_index:
            lbl.config(bg="lightblue")


def update_file_index_display():
    """
    更新界面上当前是第几个视频的显示标签（1-based）。
    """
    total_files = len(hdf5_file_list)
    file_index_label_widget.config(
        text=f"File {current_file_index + 1}/{total_files}"
    )


def update_task_index_display():
    """
    更新界面上当前是第几个任务的显示标签（1-based）。
    """
    total_tasks = len(all_task_dirs)
    task_index_label_widget.config(
        text=f"Task {current_task_index + 1}/{total_tasks}"
    )


def update_subtask_list_display():
    """
    使用当前任务加载进来的 current_subtasks，在左侧面板生成 Label 控件显示它们。
    """
    global subtask_label_widgets

    # 清理旧的 Label
    for lbl in subtask_label_widgets:
        lbl.destroy()
    subtask_label_widgets.clear()

    # 遍历 current_subtasks 列表，每个元素是一个 dict，其中至少包含 'content' 和 'step'
    for idx, subtask_item in enumerate(current_subtasks):
        content = subtask_item.get('content', '')
        lbl = tk.Label(left_frame, text=content, font=("Arial", 12))
        lbl.grid(row=idx, column=0, sticky="w", padx=5, pady=2)
        subtask_label_widgets.append(lbl)


# ──────────────────────────────────────────────────────────────────────────────
# 交互回调函数
# ──────────────────────────────────────────────────────────────────────────────

def on_next_frame(event=None):
    """
    按右箭头键或调用此函数时，切换到下一帧（如果不是最后一帧）。
    """
    global current_frame_index
    if current_frame_index < total_frames - 1:
        current_frame_index += 1
        update_frame_display()


def on_prev_frame(event=None):
    """
    按左箭头键或调用此函数时，切换到上一帧（如果不是第一帧）。
    """
    global current_frame_index
    if current_frame_index > 0:
        current_frame_index -= 1
        update_frame_display()


def on_label_frame(event=None):
    """
    按空格键或调用此函数时，对当前帧进行标注：
      - 从 current_subtasks 中获取当前子任务的 content 和 step
      - 将 {'step': 子任务 step, 'label': 子任务 content, 'frame': "start-end"} 添加到 labeled_frames
      - 更新 last_frame_index 和 current_subtask_index
      - current_subtask_index 超过时提示“标注完成”
      - 否则更新显示到下一子任务状态
    """
    global current_subtask_index, last_frame_index

    if current_subtask_index >= len(current_subtasks):
        return

    # 1-based 结束帧
    end_frame = current_frame_index + 1
    # 拼接区间字符串
    interval_str = f"{last_frame_index}-{end_frame}"

    # 获取当前子任务的内容和 step
    subtask_content = current_subtasks[current_subtask_index].get('content', "")
    step_content = current_subtasks[current_subtask_index].get('step', "")

    labeled_frames.append({
        'step': step_content,
        'label': subtask_content,
        'frame': interval_str
    })
    print(f"Label '{subtask_content}' (step '{step_content}') added for frames {interval_str}")

    # 将下一个子任务的起始帧设为当前结束帧 + 1
    last_frame_index = end_frame + 1

    current_subtask_index += 1
    if current_subtask_index >= len(current_subtasks):
        messagebox.showinfo("Task Complete", "所有子任务已标注完毕！")
    else:
        update_frame_display()


def on_undo_label(event=None):
    """
    撤销上一次标注操作：
      - 如果 labeled_frames 不为空，则弹出最后一个元素，并将 current_subtask_index 和 last_frame_index 恢复
      - 更新界面显示
    """
    global current_subtask_index, last_frame_index

    if labeled_frames and current_subtask_index > 0:
        removed = labeled_frames.pop()
        current_subtask_index -= 1

        # 恢复 last_frame_index 为移除项的起始值
        start_str = removed['frame'].split('-')[0]
        last_frame_index = int(start_str)

        print(f"Removed label '{removed['label']}' (step '{removed['step']}') for frames {removed['frame']}")
        update_frame_display()
    else:
        messagebox.showinfo("Undo", "没有可撤销的标注。")


def on_save_and_next_file(event=None):
    """
    按下 's' 键或调用此函数时，如果当前所有子任务都已标注完毕，则：
      - 将 labeled_frames 写入 JSON 文件
      - 弹窗提示“已保存”
      - 切换到下一个 HDF5 文件；如果当前任务文件列表处理完毕，则切换到下一个任务目录
      - 更新界面显示；如果所有任务都完成，则弹窗提示并退出
    """
    global current_file_index, current_task_index

    # 如果还没标注完所有子任务，则提示
    if current_subtask_index < len(current_subtasks):
        messagebox.showinfo("提示", "请先完成所有子任务的标注，再保存。")
        return

    # 1. 保存标注结果到 JSON
    with open(current_json_output_path, 'w', encoding='utf-8') as f:
        json.dump(labeled_frames, f, indent=4, ensure_ascii=False)

    # 弹窗提示保存成功
    messagebox.showinfo("保存成功", f"已将标注结果保存到：\n{current_json_output_path}")

    # 2. 增加文件索引，切换到下一个 HDF5 文件
    current_file_index += 1

    # 如果当前目录下所有文件都处理完了，则尝试切换到下一个任务目录
    if current_file_index >= len(hdf5_file_list):
        current_file_index = 0
        current_task_index += 1

        if current_task_index < len(all_task_dirs):
            load_task_directory(all_task_dirs[current_task_index], file_idx=0)
        else:
            messagebox.showinfo("Congratulations", "所有任务都已标注完毕！")
            root.quit()
            return
    else:
        # 继续在当前任务目录里处理下一个文件
        initialize_task_file(hdf5_file_list[current_file_index])

    # 更新界面
    update_file_index_display()
    update_task_index_display()
    update_subtask_list_display()
    update_frame_display()


def on_exit(event=None):
    """
    按 ESC 键或调用此函数时，确认是否退出程序。
    """
    if messagebox.askokcancel("Exit", "确定要退出吗？"):
        root.quit()


def on_load_indices():
    """
    点击 “Load” 按钮时，从 Entry 里读取用户输入的 task_index 和 file_index（1-based），
    并重新加载对应的任务目录和文件（转换为 0-based）。
    """
    global current_task_index, current_file_index

    try:
        ti_input = int(task_index_entry.get())
        fi_input = int(file_index_entry.get())
    except ValueError:
        messagebox.showerror("输入错误", "Task Index 和 File Index 必须是整数。")
        return

    # 将用户输入的 1-based 转为 0-based
    ti = ti_input - 1
    fi = fi_input - 1

    if not (0 <= ti < len(all_task_dirs)):
        messagebox.showerror("输入错误", f"Task Index 必须在 1 到 {len(all_task_dirs)} 之间。")
        return

    current_task_index = ti
    task_dir = all_task_dirs[current_task_index]

    # 列出该目录下的所有 .hdf5
    temp_list = sorted(glob.glob(os.path.join(task_dir, "*.hdf5")))
    if not temp_list:
        messagebox.showerror("错误", f"任务目录 {task_dir} 下没有 .hdf5 文件。")
        return

    if not (0 <= fi < len(temp_list)):
        messagebox.showerror("输入错误", f"File Index 必须在 1 到 {len(temp_list)} 之间。")
        return

    current_file_index = fi
    load_task_directory(task_dir, file_idx=current_file_index)

    # 重新更新 UI 显示
    update_task_index_display()
    update_file_index_display()
    update_subtask_list_display()
    update_frame_display()


# ──────────────────────────────────────────────────────────────────────────────
# 主程序入口：构建并启动 Tkinter 界面
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1. 获取所有任务目录列表，并排序
    all_task_dirs = sorted(glob.glob(os.path.join(TASK_ROOT_PATH, "*")))
    if not all_task_dirs:
        raise RuntimeError(f"在路径 {TASK_ROOT_PATH} 下未找到任何任务目录。")

    # 2. 默认先加载第 1 个任务和第 1 个文件（1-based）
    current_task_index = 0
    current_file_index = 0
    load_task_directory(all_task_dirs[current_task_index], file_idx=current_file_index)

    # 3. 初始化 Tkinter 主窗口
    root = tk.Tk()
    root.title("Frame Labeling Tool")

    # ─── 索引输入区 ────────────────────────────────────────────────────────────
    index_frame = tk.Frame(root)
    index_frame.grid(row=0, column=0, columnspan=3, pady=5, sticky="w")

    tk.Label(index_frame, text="Task Index (1-based):", font=("Arial", 12)).grid(row=0, column=0, padx=5)
    task_index_entry = tk.Entry(index_frame, width=5)
    task_index_entry.insert(0, str(current_task_index + 1))  # 显示为 1-based
    task_index_entry.grid(row=0, column=1, padx=5)

    tk.Label(index_frame, text="File Index (1-based):", font=("Arial", 12)).grid(row=0, column=2, padx=5)
    file_index_entry = tk.Entry(index_frame, width=5)
    file_index_entry.insert(0, str(current_file_index + 1))
    file_index_entry.grid(row=0, column=3, padx=5)

    load_button = tk.Button(index_frame, text="Load", command=on_load_indices)
    load_button.grid(row=0, column=4, padx=10)

    # ─── 状态显示区 ────────────────────────────────────────────────────────────
    frame_label_widget = tk.Label(root, text=f"Frame 1/{total_frames}", font=("Arial", 24))
    frame_label_widget.grid(row=1, column=0, sticky="w", padx=10)

    file_index_label_widget = tk.Label(
        root, text=f"File {current_file_index+1}/{len(hdf5_file_list)}", font=("Arial", 24)
    )
    file_index_label_widget.grid(row=1, column=1, sticky="w", padx=10)

    task_index_label_widget = tk.Label(
        root, text=f"Task {current_task_index+1}/{len(all_task_dirs)}", font=("Arial", 24)
    )
    task_index_label_widget.grid(row=1, column=2, sticky="w", padx=10)

    # ─── 左侧子任务列表 ─────────────────────────────────────────────────────────
    left_frame = tk.Frame(root)
    left_frame.grid(row=2, column=0, sticky="nw", padx=10, pady=5)

    # ─── 右侧图像显示 ───────────────────────────────────────────────────────────
    right_frame = tk.Frame(root)
    right_frame.grid(row=2, column=1, columnspan=2, sticky="ne", padx=10, pady=5)

    # 初始化子任务列表和图像显示
    update_subtask_list_display()
    img_tk = load_current_frame_image()
    image_panel = tk.Label(right_frame, image=img_tk)
    image_panel.image = img_tk
    image_panel.pack()

    # 绑定按键事件
    root.bind("<Right>", on_next_frame)        # 右箭头 → 下一帧
    root.bind("<Left>", on_prev_frame)         # 左箭头 ← 上一帧
    root.bind("<space>", on_label_frame)       # 空格键 → 标注当前帧
    root.bind("<u>", on_undo_label)            # 'u' 键 → 撤销上一次标注
    root.bind("<s>", on_save_and_next_file)    # 's' 键 → 保存并切换文件/任务
    root.bind("<Escape>", on_exit)             # ESC 键 → 退出

    # 启动主循环
    update_frame_display()
    update_file_index_display()
    update_task_index_display()
    root.mainloop()
