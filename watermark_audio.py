import wave
import struct
import os
embed_dir=os.path.join(os.getcwd(),'embed_file')

def bin_value(value, bitsize=8):
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Larger than the expected size")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval

def embed(input, watermark_str):
    print("audio_watermark_embed:")
    # 初始化水印信息
    watermark = ""
    # 水印字符串长度转化为32bits的二进制字符串并加入水印信息中
    watermark_size = bin_value(len(watermark_str), 32)
    watermark += watermark_size
    # 循环转化字符串中的字符为二进制字符串并加入水印信息中
    for char in watermark_str:
        watermark += bin_value(ord(char))
    # 利用wave库读取wav文件
    cover_audio = wave.open(input, 'rb')
    # 保存wav原始文件的参数信息
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = cover_audio.getparams()
    # 读取所有数据，数据长度为帧数*声道数
    frames = cover_audio.readframes(nframes * nchannels)
    #解析帧数据
    samples = struct.unpack_from("%dh" % nframes * nchannels, frames)
    # 水印过长时抛出异常
    if len(samples) < len(watermark):
        raise OverflowError(
            "水印长度共%d比特，采样点数量为%d，采样点不足请减少水印长度。" % (
                len(watermark), len(samples)))
    encoded_samples = []
    watermark_position = 0
    for sample in samples:
        encoded_sample = sample
        if watermark_position < len(watermark):
            encode_bit = int(watermark[watermark_position])
            if encode_bit == 1:
                encoded_sample = sample | 1
            else:
                encoded_sample = sample
                if sample & 1 != 0:
                    encoded_sample = sample - 1
            watermark_position = watermark_position + 1
        encoded_samples.append(encoded_sample)
    #写入文件
    #embed_dir
    file_name = input.split("\\")[-1]+"_embed.wav"
    encoded_audio = wave.open(os.path.join(embed_dir,file_name), 'wb')
    encoded_audio.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
    encoded_frames = struct.pack("%dh" % len(encoded_samples), *encoded_samples)
    encoded_audio.writeframes(encoded_frames)


def extract(input):
    print("video_watermark_extract!")
    watermarked_audio = wave.open(input, 'rb')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = watermarked_audio.getparams()
    frames = watermarked_audio.readframes(nframes * nchannels)
    samples = struct.unpack_from("%dh" % nframes * nchannels, frames)
    watermark_bytes = ""
    for i in range(32):
        if samples[i] & 1 == 0:
            watermark_bytes += '0'
        else:
            watermark_bytes += '1'
    watermark_size  = int(watermark_bytes, 2)
    print("提取到长度为%d字节的水印。" % watermark_size)
    watermark = ""
    sample_index = 32
    for n in range(watermark_size):
        bytes = ""
        for i in range(8):
            if samples[sample_index] & 1 == 0:
                bytes += '0'
            else:
                bytes += '1'
            sample_index += 1
        watermark += chr(int(bytes, 2))
    print(watermark)
    return watermark

