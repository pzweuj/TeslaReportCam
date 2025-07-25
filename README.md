# TeslaReportCam
准备写一个脚本，用于给特斯拉的行车记录加时间标签、合并视频。

方便我举报非紧急走应急车道的狗。



## 介绍
依赖[ffmpeg](https://ffmpeg.org/)，需要安装并放在环境变量里

使用前，先安装以下两个库，基于python3

```cmd
pip install ffmpeg-python
pip install pysrt
```

全程保持原始清晰度，为了效率使用了GPU，因为广州交警仅支持提交H264，因此用了h264_nvenc（GPU模式）或libx264（CPU模式）。[tesla dashcam](https://github.com/ehendrix23/tesla_dashcam)这个项目挺好用的，但是并不适用于我，可能是ffmpeg的版本原因，单独输出非正面镜头时会有报错。



添加时间 -> 分别合并四个镜头的视频（已完成）；

```cmd
python TeslaReportCam.py <input_dir> <output_dir> [gpu]
```

建议搭配[Lossless-Cut](https://github.com/mifi/lossless-cut)使用，

广州交警公众号现在支持上传200M的视频，可以不压缩了。



## 功能

这个项目完全是个人使用向，主要功能包括：

1，根据时间合并视频，保持视频的清晰度及大小；

2，添加时间戳；

3，四个视觉独立输出，因为交警同志反馈四个镜头合在一起他们也只是截一个来核实的，因此只需要提交包含清晰车牌的违法行为过程镜头即可。
