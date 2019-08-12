FFMPEG_BIN = "ffmpeg.exe"

import subprocess as sp#调用外部程序
import numpy
import robust
import os

#embed_dir
embed_dir=os.path.join(os.getcwd(),'embed_file')

def embed(input_video,  watermark_string):
    print("video_watermark_embed!")

    command_read = [FFMPEG_BIN,
                    '-i', input_video,
                    '-f', 'image2pipe',
                    '-pix_fmt', 'yuv420p',
                    '-vcodec', 'rawvideo', '-']
    pipe_read = sp.Popen(command_read, stdout=sp.PIPE, bufsize=10 ** 8)
    # print(input_video)
    file_name=input_video.split("//")[-1]+"_embed.ts"
    # print(file_name)
    file_dir=os.path.join(embed_dir,file_name)
    # print(file_dir)
    command_write = [FFMPEG_BIN,
                     '-y',  # (optional) overwrite output file if it exists
                     '-f', 'rawvideo',
                     '-vcodec', 'rawvideo',
                     '-s', '1920x1080',
                     '-pix_fmt', 'yuv420p',
                     '-i', '-',  # The imput comes from a pipe
                     '-q:v', '2',
                     file_dir]

    pipe_write = sp.Popen(command_write, stdin=sp.PIPE)

    raw_image = pipe_read.stdout.read(1920 * 1080 * 3)

    while raw_image != None and len(raw_image) != 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        image = image.reshape((1080, 1920, 3))
        # throw away the data in the pipe's buffer.
        pipe_read.stdout.flush()
        # 图片是三维的[1080(行),1920,3]：YCbCr用于电视影像，Y代表亮度，CbCr代表色差
        img_tmp = image[:1080, :1920, 0]#0号元素
        robust.embed_watermark(img_tmp, watermark_string)
        pipe_write.stdin.write(image.tostring())
        raw_image = pipe_read.stdout.read(1920 * 1080 * 3)


def extract(input_video):
    print("video_watermark_extract!")
    command_read = [FFMPEG_BIN,
                    '-i', input_video,
                    '-f', 'image2pipe',
                    '-pix_fmt', 'yuv420p',
                    '-vcodec', 'rawvideo', '-']
    pipe_read = sp.Popen(command_read, stdout=sp.PIPE, bufsize=10 ** 8)

    raw_image = pipe_read.stdout.read(1920 * 1080 * 3)
    result=[]
    while raw_image != None and len(raw_image) != 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        image = image.reshape((1080, 1920,3))
        # throw away the data in the pipe's buffer.
        pipe_read.stdout.flush()

        img_tmp = image[:1080, :1920, 0]
        result.append(robust.extract_watermark(img_tmp))
        raw_image = pipe_read.stdout.read(1920 * 1080 * 3)





