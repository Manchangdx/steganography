import sys 
from PIL import Image


def make_even_image(image):
    """取得一个 PIL 图像并且更改所有值为偶数，使最低有效位为 0
    """
    # image.getdata 方法返回的是一个可迭代对象，其中包含图片中所有像素点的数据
    # 每个像素点表示一个颜色，每种颜色有红绿蓝三种颜色按比例构成
    # R Red 红色；G Green 绿色；B Blue 蓝色；A Alpha 透明度
    # 更改所有像素点中四个数值为偶数（魔法般的移位）
    # 这里使用位运算符 >> 和 << 来实现数据处理
    # 奇数减一变偶数，偶数不变，这样处理后，所有数值的最低位变为零
    # pixels 为更改后的像素点数据列表
    pixels = [(r >> 1 << 1, g >> 1 << 1, b >> 1 << 1, a >> 1 << 1) 
            for r, g, b, a in image.getdata()]  
    # 调用 Image 的 new 方法创建一个相同大小的图片副本
    # 参数为模式（字符串）和规格（二元元组）
    # 这里使用 image 的属性值即可
    even_image = Image.new(image.mode, image.size)  
    # 把处理之后的像素点数据写入副本图片
    even_image.putdata(pixels)  
    return even_image


def encode_data_in_image(image, data):
    """将字符串编码到图片中
    """
    # 获得最低有效位为 0 的图片副本
    even_image = make_even_image(image)  
    # 匿名函数用于将十进制数值转换成 8 位二进制数值的字符串
    int_to_binary_str = lambda i: '0' * (8 - len(bin(i)[2:])) + bin(i)[2:]
    # 将需要隐藏的字符串转换成二进制字符串
    # 每个字符转换成二进制之后，对应一个或多个字节码
    # 每个字节码为一个十进制数值，将其转换为 8 为二进制字符串后相加
    binary = ''.join(map(int_to_binary_str, bytearray(data, 'utf-8'))) 
    # 每个像素点的 RGBA 数据的最低位都已经空出来，分别可以存储一个二进制数据
    # 所以图片可以存储的最大二进制数据的位数是像素点数量的 4 倍
    # 如果需要隐藏的字符串转换成二进制字符串之后的长度超过这个数，抛出异常
    if len(binary) > len(even_image.getdata()) * 4:  
        raise Exception("Error: Can't encode more than " + 
                len(even_image.getdata()) * 4 + " bits in this image. ")
    # 二进制字符串 binary 的长度一定是 8 的倍数
    # 将二进制字符串信息编码进像素点中
    # 当二进制字符串的长度大于像素点索引乘以 4 时
    # 这些像素点用于存储数据
    # 否则，像素点内 RGBT 数值不变
    encoded_pixels = [(r+int(binary[index*4+0]),
                       g+int(binary[index*4+1]),
                       b+int(binary[index*4+2]),
                       t+int(binary[index*4+3])) 
            if index * 4 < len(binary) else (r,g,b,t) 
            for index, (r, g, b, t) in enumerate(even_image.getdata())] 
    # 创建新图片以存放编码后的像素
    encoded_image = Image.new(even_image.mode, even_image.size)  
    # 把处理之后的像素点数据写入新图片
    encoded_image.putdata(encoded_pixels)  
    # 返回图片对象
    return encoded_image


def binary_to_string(binary):
    '''将二进制字符串转换为 UTF-8 字符串
    '''
    # 参数 binary 为二进制字符串，且长度为 8 的倍数
    # index 是 binary 的索引，初始值为 0
    index = 0
    # 创建空列表，以用于添加解析得到的人类能够看懂的 UTF-8 字符
    strings = []

    # 创建嵌套函数，参数为二进制字符串片段和字节数，返回值为有效二进制字符串
    def effective_binary(binary_part, zero_index):
        if not zero_index:
            return binary_part[1:]
        binary_list = []
        for i in range(zero_index):
            small_part = binary_part[8 * i: 8 * i + 8]
            binary_list.append(small_part[small_part.find('0') + 1:])
        return ''.join(binary_list)

    while index + 1 < len(binary):
        # 字符所占字节数举例：
        # 字符 'a' 转换为字节码后，占 1 个字节，且字节的最高位是 0
        # 字符 '哈' 转换为字节码后，占 3 个字节，且第一个字节的最高位是 1110
        # 占 1 个字节，开头是 0xxxxxxx
        # 占 2 个字节，开头是 110xxxxx
        # 占 3 个字节，开头是 1110xxxx
        # 占 4 个字节，开头是 11110xxx
        # zero_index 为第一个 ‘0’ 的索引，根据它我们可以知道字节数
        zero_index = binary[index:].index('0') 
        # 单个字符转换为二进制字节码后的长度：字节数乘以 8
        length = zero_index * 8 if zero_index else 8
        # 调用 effective_binary 函数，参数有两个：binary 片段，字节数
        # 返回的是有效二进制字符串，该字符串通过 int 方法转换成十进制数值
        # 然后使用 chr 方法即可获得对应的字符啦
        string = chr(int(effective_binary(
                binary[index: index+length], zero_index), 2))
        # 将字符添加到字符列表 strings 中
        strings.append(string)
        # 索引变量增加已经处理的二进制字符串长度
        index += length
    # 最后返回解析得到的字符串
    return ''.join(strings)


def decode_data_from_image(image):
    '''解码图片中的隐藏数据
    '''
    # 从图片的像素点数据中获得存储数据的二进制字符串
    binary = ''.join([bin(r)[-1] + bin(g)[-1] + bin(b)[-1] + bin(a)[-1]
            for r, g, b, a in image.getdata()])
    # 出现连续 16 个 0 的字符串片段的索引判定为有效数据截止处
    many_zero_index = binary.find('0' * 16)
    # 有效数据字符串的长度一定是 8 的倍数
    # 以此判定准确的断点索引，获得有效数据的二进制字符串
    end_index = (many_zero_index + 8 - many_zero_index % 8 
            if many_zero_index % 8 != 0 else many_zero_index)
    data = binary_to_string(binary[:end_index])
    return data


def main():
    '''主函数
    '''
    # 获取原图片文件和新图片文件的名字
    image_file, new_image_file = sys.argv[1:]
    # 调用 Image 的 open 方法获取原图片对象
    image = Image.open(image_file)
    # 需要隐藏到图片中的字符串
    str_to_hide = '你好世界 Hello World!'
    # 调用此函数生成包含字符串数据的新图片对象
    new_image = encode_data_in_image(image, str_to_hide)
    # 将新图片对象保存到新文件里
    new_image.save(new_image_file)
    # 调用此函数获取隐藏在新图片对象中的字符串并打印
    print(decode_data_from_image(new_image))


if __name__ == '__main__':
    main()
