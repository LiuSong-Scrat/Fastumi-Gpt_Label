import cv2
import h5py
import numpy as np
import glob
import os

path = "/home/yan/Liusong/DataProcessing/file/video"
# video_files = ["/home/yan/Liusong/DataProcessing/video/temp_video_3.mp4"]
video_files = glob.glob(os.path.join(path, "*.mp4"))

for video_file in video_files:
    # 1. 读取视频帧（原逻辑不变）
    video_file = "/home/yan/Liusong/DataProcessing/file/video/dual_arm_video_4.mp4"
    video = cv2.VideoCapture(video_file)
    print('Loading video:', video_file)
    
    frames = []
    interval = 3
    count = 0

    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        if count % interval == 0:
            frames.append(frame)
        count += 1
    video.release()

    if not frames:
        print("No frames extracted!")
        continue

    # 2. 关键优化：将帧列表转为 numpy 数组一次性写入
    frames_array = np.stack(frames)  # shape: (N, H, W, C)
    
    # 3. 保存到 HDF5（批量写入）
    filename = os.path.splitext(os.path.basename(video_file))[0]
    hdf5_path = os.path.join(path+"/../hdf5/", f"{filename}.hdf5")
    
    with h5py.File(hdf5_path, 'w') as hf:
        hf.create_dataset(
            "frames",
            data=frames_array,  # 直接写入整个数组
            dtype='uint8',
            compression="gzip",
            chunks=True         # 启用分块存储（加速大文件读写）
        )
    
    print(f"Saved {len(frames)} frames to {hdf5_path} (shape: {frames_array.shape})")
    exit(0)