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
def add_timestamp(input_mp4, output_mp4, use_gpu=False):
    # 预处理
    stamp = "-".join(os.path.splitext(os.path.basename(input_mp4))[0].split("-")[:-1])
    metadata = ffmpeg.probe(input_mp4)
    duration = float(metadata['streams'][0]['duration'])
    create_srt(stamp, duration, output_mp4 + ".srt")
    # 打开输入视频
    input_stream = ffmpeg.input(input_mp4)

    # 基本参数
    output_params = {
        'vf': 'subtitles=%s' % output_mp4 + ".srt",
        'movflags': '+faststart'  # 使视频能够快速开始播放
    }

    # 根据GPU选项设置编码参数
    if use_gpu:
        output_params.update({
            'vcodec': 'h264_nvenc',
            'preset': 'p7',    # NVENC的最高质量预设
            'rc': 'vbr_hq',    # 高质量可变比特率模式
            'cq': 15           # 较低的CQ值提供更高质量（移除b:v避免冲突）
        })
    else:
        output_params.update({
            'vcodec': 'libx264',  # 使用x264编码器
            'crf': 18,            # 设置高质量（18是推荐值，范围0-51，数值越小质量越高）
            'preset': 'slow'      # 使用较慢的预设以获得更好的压缩
        })

    # 添加字幕并使用编码参数
    output_stream = ffmpeg.output(input_stream, output_mp4, **output_params)
    # 运行 FFmpeg 命令
    ffmpeg.run(output_stream, overwrite_output=True)

# 合并mp4
def concatenate_videos(video_files, output_file):
    # ffmpeg的bug，先转成ts再合并能避免
    ts_files = []
    for vf in video_files:
        ts_file = vf.replace(".mp4", ".ts")
        # 转换为TS格式时直接复制流，避免重新编码
        ts_params = {
            'c': 'copy',
            'format': 'mpegts'
        }

        ffmpeg.input(vf).output(ts_file, **ts_params).run(overwrite_output=True)
        ts_files.append(ts_file)

    output_dir = os.path.dirname(os.path.dirname(output_file))
    concat_file = output_file.replace(".mp4", ".concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for i in ts_files:
            f.write("file " + i.replace("\\", "\\\\") + "\n")

    # 合并参数
    concat_params = {
        'format': 'concat',
        'safe': 0
    }

    # 合并时直接复制流，避免重新编码以保持质量和速度
    output_params = {'c': 'copy'}

    # 添加质量参数
    ffmpeg.input(concat_file, **concat_params).output(output_file, **output_params).run(overwrite_output=True)
    shutil.copy(output_file, output_dir)

# 主流程
def pipe_mp4(input_dir, output_dir, use_gpu=False):
    temp_dir = output_dir + "/tmp_dir_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    for i in os.listdir(input_dir):
        if i.endswith('.mp4'):
            mp4_file = input_dir + "/" + i
            add_timestamp(mp4_file, temp_dir + "/" + i.replace(".mp4", ".srt.mp4"), use_gpu)
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
    # 检查是否有GPU参数
    use_gpu = False
    if len(sys.argv) > 3 and sys.argv[3].lower() in ['gpu', 'true', '1', 'yes']:
        use_gpu = True
    pipe_mp4(sys.argv[1], sys.argv[2], use_gpu)
except Exception as e:
    print(f"Error: {e}")
    print("Usage: python TeslaReportCam.py <input_dir> <output_dir> [gpu]")

