import cv2
import numpy as np
# 不同图片选择的像素点不同（白色背景 or 风景图片）


def bin_value(value, bitsize=8):
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Larger than the expected size")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval

# 扩频
def spread_spectrum(bit_string, spread_width):
    ret = ""
    for bit in bit_string:#字符串串接
        ret += bit * spread_width
    return ret


def get_original_bin(bit_string, spread_width):
    if len(bit_string) % spread_width != 0:#看扩频后是否为整数倍
        print("长度错误，需是%d整数倍。" % spread_width)
        return None

    ret_string = ""
    for i in range(int(len(bit_string) / spread_width)):#每一组统计1的个数
        count = 0
        for j in range(spread_width):
            count += int(bit_string[i * spread_width + j])
        if count < spread_width /3:# 阈值为50%，1的个数没超过50%
            ret_string += "0"
        elif count > spread_width-spread_width /3:
            ret_string += "1"#0的个数没超过50%

    return ret_string


def watermark_encode(watermark_string):#（8*7《水印长度》+6*8*7《水印》个bit）
    # 初始化水印信息
    watermark = ""

    # 水印字符串长度转化为32bits的二进制字符串并加入水印信息中
    watermark_size = bin_value(len(watermark_string), 8)
    watermark += spread_spectrum(watermark_size, 7)

    # 循环转化字符串中的字符为二进制字符串并加入+水印信息中
    for char in watermark_string:
        temp_string = bin_value(ord(char))
        watermark += spread_spectrum(temp_string, 7)
    return watermark

# 水印强度
def embed_bit(bit, dcted_block, alpha):
    if bit == 1:
        if dcted_block[4, 3] < dcted_block[5, 2]:
            dcted_block[4, 3], dcted_block[5, 2] = dcted_block[5, 2], dcted_block[4, 3]#a,b=b,a 交换值
            if dcted_block[4, 3] - dcted_block[5, 2] < alpha:
                dcted_block[4, 3] += alpha
        elif dcted_block[4, 3] == dcted_block[5, 2]:
            dcted_block[4, 3] += alpha
    elif bit == 0:
        if dcted_block[4, 3] > dcted_block[5, 2]:
            dcted_block[4, 3], dcted_block[5, 2] = dcted_block[5, 2], dcted_block[4, 3]
            if dcted_block[5, 2] - dcted_block[4, 3] < alpha:
                dcted_block[4, 3] -= alpha
        elif dcted_block[4, 3] == dcted_block[5, 2]:
            dcted_block[4, 3] -= alpha
    else:
        print("请输入正确的水印值，0或1。")


def extract_bit(dcted_block):
    if dcted_block[4, 3] > dcted_block[5, 2]:
        return 1
    else:
        return 0


def embed_watermark(image, watermark_string):


    # print(watermark_string)
    watermark = watermark_encode(watermark_string)
    # print(watermark)

    iHeight, iWidth = image.shape
    # 初始化空矩阵保存量化结果
    img2 = np.empty(shape=(iHeight, iWidth))

    index = 0

    # 分块DCT
    for startY in range(0, iHeight, 8):
        for startX in range(0, iWidth, 8):
            block = image[startY:startY + 8, startX:startX + 8].reshape((8, 8))#

            # 进行DCT
            blockf = np.float32(block)
            block_dct = cv2.dct(blockf)

            if index < len(watermark):
                embed_bit(int(watermark[index]), block_dct,50)
                index += 1

            # store the result
            for y in range(8):
                for x in range(8):
                    img2[startY + y, startX + x] = block_dct[y, x]


    # DCT逆变换
    for startY in range(0, iHeight, 8):
        for startX in range(0, iWidth, 8):
            block = img2[startY:startY + 8, startX:startX + 8].reshape((8, 8))

            blockf = np.float32(block)
            dst = cv2.idct(blockf)

            # 保存逆变换结果
            for y in range(8):
                for x in range(8):
                    image[startY + y, startX + x] = dst[y, x]




def extract_watermark(image):
    iHeight, iWidth = image.shape

    index = 0
    length_string = ""
    watermark_length = 0
    watermark_string = ""

    # 分块DCT
    for startY in range(0, iHeight, 8):
        for startX in range(0, iWidth, 8):
            block = image[startY:startY + 8, startX:startX + 8].reshape((8, 8))

            # 进行DCT
            blockf = np.float32(block)
            block_dct = cv2.dct(blockf)

            if index < 8 * 7:
                bit = extract_bit(block_dct)

                if bit == 1:
                    length_string += "1"
                else:
                   length_string += "0"

                if index == 8 * 7 - 1:
                    length_string = get_original_bin(length_string, 7)
                    watermark_length = int(length_string, 2)

                index += 1

            elif index < 8 * 7 + watermark_length * 8 * 7:

                bit = extract_bit(block_dct)

                if bit == 1:
                    watermark_string += "1"
                else:
                    watermark_string += "0"

                if index == 8 * 7 + watermark_length * 8 * 7 - 1:
                    watermark_string = get_original_bin(watermark_string, 7)

                    decoded_watermark = ""
                    for i in range(watermark_length):
                        decoded_watermark += chr(int(watermark_string[i*8 : (i+1)*8], 2))

                    # print(decoded_watermark)
                    return decoded_watermark

                index += 1