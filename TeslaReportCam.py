# coding=utf-8
# pzw
# 20231010
# 开发中

import os
import sys
import shutil
import datetime
import ffmpeg
from pysrt import SubRipFile, SubRipItem, SubRipTime

# 处理特斯拉的时间格式
def datetime_to_seconds(date_time_str):
    date_format = "%Y-%m-%d_%H-%M-%S"
    date_time_obj = datetime.datetime.strptime(date_time_str, date_format)
    return date_time_obj

# 创建SRT字幕文件
def create_srt(start_time, duration, subtitles_file):
    start_seconds = datetime_to_seconds(start_time)
    srt_file = SubRipFile()

    for i in range(int(duration) + 1):
        text = (start_seconds + datetime.timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S")
        item = SubRipItem(i, start=SubRipTime(0, 0, i, 0), end=SubRipTime(0, 0, i+1, 0), text=text)
        srt_file.append(item)

    srt_file.save(subtitles_file, encoding="utf-8")

# 将SRT字幕文件嵌入到视频中
def add_timestamp(input_mp4, output_mp4):
    # 预处理
    stamp = "-".join(os.path.splitext(os.path.basename(input_mp4))[0].split("-")[:-1])
    metadata = ffmpeg.probe(input_mp4)
    duration = float(metadata['streams'][0]['duration'])
    create_srt(stamp, duration, output_mp4 + ".srt")
    # 打开输入视频
    input_stream = ffmpeg.input(input_mp4)
    # 添加字幕
    output_stream = ffmpeg.output(input_stream, output_mp4, vf='subtitles=%s' % output_mp4 + ".srt", vcodec='h264_nvenc')
    # 运行 FFmpeg 命令
    ffmpeg.run(output_stream, overwrite_output=True)

# 合并mp4
def concatenate_videos(video_files, output_file):
    # ffmpeg的bug，先转成ts再合并能避免
    ts_files = []
    for vf in video_files:
        ts_file = vf.replace(".mp4", ".ts")
        ffmpeg.input(vf).output(ts_file, c='copy', format='mpegts', vcodec='h264_nvenc').run(overwrite_output=True)
        ts_files.append(ts_file)
    output_dir = os.path.dirname(os.path.dirname(output_file))
    concat_file = output_file.replace(".mp4", ".concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for i in ts_files:
            f.write("file " + i.replace("\\", "\\\\") + "\n")
    ffmpeg.input(concat_file, format="concat", safe=0).output(output_file, c='copy', vcodec='h264_nvenc').run(overwrite_output=True)
    shutil.copy(output_file, output_dir)

# 主流程
def pipe_mp4(input_dir, output_dir):
    temp_dir = output_dir + "/tmp_dir_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    for i in os.listdir(input_dir):
        if i.endswith('.mp4'):
            mp4_file = input_dir + "/" + i
            add_timestamp(mp4_file, temp_dir + "/" + i.replace(".mp4", ".srt.mp4"))
    view_dict = {"front": [], "back": [], "left": [], "right": []}
    temp_dir = os.path.abspath(temp_dir)
    for i in os.listdir(temp_dir):
        if i.endswith('.mp4'):
            if "-front" in i:
                view_dict["front"].append(temp_dir + "/" + i)
            elif "-back" in i:
                view_dict["back"].append(temp_dir + "/" + i)
            elif "-left" in i:
                view_dict["left"].append(temp_dir + "/" + i)
            elif "-right" in i:
                view_dict["right"].append(temp_dir + "/" + i)
    for j in view_dict:
        concatenate_videos(view_dict[j], view_dict[j][0].replace(".srt.mp4", ".merge.mp4"))
    
    # 删除临时文件
    shutil.rmtree(temp_dir)

################ 主流程 #################
try:
    pipe_mp4(sys.argv[1], sys.argv[2])
except:
    print("Usage: python TeslaReportCam.py <input_dir> <output_dir>")

