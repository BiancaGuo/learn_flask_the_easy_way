from PIL import Image
from numpy import *
import os
embed_dir=upload_dir=os.path.join(os.getcwd(),'embed_file')

# 嵌入水印
def bin_value(value, bitsize):  # 将整数转化为固定长度的二进制字符串
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Too Large!")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval


def embed(input, watermark):
    print("image_watermark_embed!")
    im = Image.open(input)
    im = im.convert('L')  # 转化为灰度图片
    file_name = input.split("\\")[-1]+'.bmp'
    im.save(file_name)  # 防止压缩时水印易被破坏，bmp没有任何与圧缩过程

    im = Image.open(file_name)

    im_array = array(im)  # 转化为数组
    row, col = im_array.shape
    im_array_flatten = im_array.flatten()  # 转化为一位数组

    data_string = watermark
    data_length = len(data_string)
    bindata = bin_value(data_length, 8)  # 把要嵌入的水印都转化为8位二进制

    index = 0  #
    for c in bindata:  # 把长度嵌入
        if int(c) == 0:
            im_array_flatten[index] = im_array_flatten[index] & 254
        else:
            im_array_flatten[index] = im_array_flatten[index] | 1
        index += 1

    for char in data_string:  # 把内容嵌入
        for c in bin_value(ord(char), 8):
            if int(c) == 0:
                im_array_flatten[index] = im_array_flatten[index] & 254
            else:
                im_array_flatten[index] = im_array_flatten[index] | 1
            index += 1

    image_array_embed = reshape(im_array_flatten, (row, col))  # 一维转化为二维数组
    im_embed = Image.fromarray(image_array_embed)
    file_name = input.split("\\")[-1]+"_embed.bmp"
    im_embed.save(os.path.join(embed_dir,file_name))
    # os.remove(file_name)

    # 水印提取


def extract(input):
    print("image_watermark_extract!")
    im = Image.open(input)
    im_array = array(im)  # 转化为数组
    im_array_flatten = im_array.flatten()  # 转化为一位数组
    str_length = ''
    index = 0
    while index < 8:  # 提取长度
        if im_array_flatten[index] == im_array_flatten[index] & 254:
            str_length = str_length + '0'
        else:
            str_length = str_length + '1'
        index += 1

    length = int(str_length, 2)
    # 提取水印
    result = ''
    while index < 8 + length * 8:
        char_binary_string = ''
        for c in range(0, 8):
            if im_array_flatten[index] == im_array_flatten[index] & 254:
                char_binary_string = char_binary_string + '0'
            else:
                char_binary_string = char_binary_string + '1'
            index += 1

        char = chr(int(char_binary_string, 2))
        result += char

    print(result)
    return result
