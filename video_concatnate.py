import numpy as np
import cv2
import glob
import os
import base64


task_list = [
    {
        "task_name": "/home/yan/Videos/task12/",
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

    video_file_ = video_files[0+3]
    video_ = cv2.VideoCapture(video_file_)

    print('load video:', video_file)
    base64Frames = []

    ## 将60帧的视频转为20帧
    interval = 3
    count = 0


    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    size = (
        width*2,
        height
    )
    videoWriter = cv2.VideoWriter(
        "./output.mp4",
        cv2.VideoWriter_fourcc(*'mp4v'),  # 编码器
        60,
        size
    )
    while video_.isOpened():
        success, frame_left = video.read()
        success, frame_right = video_.read()

        if not success:
            break

        import numpy as np
        frame = np.concatenate((frame_left,frame_right),1)

        # cv2.imshow("frame", frame)
        # cv2.waitKey(1)

        videoWriter.write(frame)

        if count % interval == 0:
            _, buffer = cv2.imencode(".jpg", frame)
            base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        count += 1

    video.release()
    videoWriter.release()