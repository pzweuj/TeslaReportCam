# coding=utf-8
# pzw
# 20231010
# 开发中

import os
import ffmpeg
from datetime import datetime

# 处理特斯拉的时间格式
def datetime_to_seconds(date_time_str):
    date_format = "%Y-%m-%d_%H-%M-%S"
    date_time_obj = datetime.strptime(date_time_str, date_format)
    return date_time_obj

# 将时间戳加入到视频中
def add_timestamp(input_mp4, output_mp4, start_time):
    start_seconds = datetime_to_seconds(start_time)
    start_seconds = start_seconds.strftime("%Y-%m-%d %H:%M:%S")

    # 打开输入视频
    input_stream = ffmpeg.input(input_mp4)
    draw_stream = ffmpeg.drawtext(input_stream,
                             text = start_seconds,
                             x = "(w-text_w)/2",
                             y = "H-th-10",
                             fontsize = 25,
                             fontcolor = "white")

    # 输出
    output_stream = ffmpeg.output(draw_stream, output_mp4)

    # 运行 FFmpeg 命令
    ffmpeg.run(output_stream, overwrite_output=True)

################ 测试 #################
input = r"D:\TeslaReportCam\2023-09-27_18-42-17\2023-09-27_18-38-29-back.mp4"
stamp = "-".join(os.path.splitext(os.path.basename(input))[0].split("-")[:-1])
print(stamp)
add_timestamp(input, "test.mp4", stamp)

