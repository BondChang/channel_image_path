import json
from collections import OrderedDict
from flask import Flask, jsonify
import os
import configparser
import ipaddress
from datetime import datetime

app = Flask(__name__)

# 读取配置文件
def read_config(config_path):
    """
    读取配置文件中的root_directory和ip_range
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    root_directory = config.get('RTSP', 'root_directory')
    ip_range = config.get('RTSP', 'ip_range')
    return root_directory, ip_range


# 获取IP范围内的所有IP地址
def get_ip_range(ip_range):
    """
    根据给定的IP范围返回所有IP地址的列表
    """
    start_ip, end_ip = ip_range.split('-')
    start_ip = ipaddress.IPv4Address(start_ip.strip())
    end_ip = ipaddress.IPv4Address(end_ip.strip())

    ip_list = []
    current_ip = start_ip

    # 从start_ip到end_ip遍历，生成所有IP
    while current_ip <= end_ip:
        ip_list.append(str(current_ip))
        current_ip += 1  # 下一地址

    return ip_list


# 获取最大时间戳的子文件夹
def get_latest_timestamp_folder(ip_path):
    """
    获取ip路径下时间戳文件夹中最新的文件夹路径
    """
    if not os.path.isdir(ip_path):
        return None
    timestamp_folders = [f for f in os.listdir(ip_path) if os.path.isdir(os.path.join(ip_path, f))]
    if not timestamp_folders:
        return None
    latest_folder = max(timestamp_folders, key=lambda folder: datetime.strptime(folder, '%Y%m%d_%H%M%S'))
    return os.path.join(ip_path, latest_folder)


# 获取channel_1.jpg或channel_2.jpg的文件路径
def get_channel_image_path(latest_folder, root_directory):
    """
    获取时间戳文件夹中的channel_1.jpg或channel_2.jpg文件路径
    并返回相对于root_directory的路径
    """
    if latest_folder is None:
        return None
    for channel in ['channel_1.jpg', 'channel_2.jpg']:
        channel_path = os.path.join(latest_folder, channel)
        if os.path.exists(channel_path):
            # 返回相对于root_directory的路径
            return os.path.relpath(channel_path, root_directory)
    return None


#  generate_json 中的调用
def generate_json(root_directory, ip_range):
    """
    根据配置文件中的root_directory和ip_range生成JSON对象
    """
    ip_list = get_ip_range(ip_range)
    result = []

    for ip in ip_list:
        ip_path = os.path.join(root_directory, ip)

        # 如果ip文件夹不存在，添加该ip对象
        ip_entry = {"IP": ip, "picUrl": None}

        if os.path.exists(ip_path):
            timestamp_folder = get_latest_timestamp_folder(ip_path)
            image_path = get_channel_image_path(timestamp_folder, root_directory)

            # 如果找到了channel_1.jpg或channel_2.jpg
            if image_path:
                ip_entry["picUrl"] =  image_path

        # 将该IP条目加入结果列表
        result.append(ip_entry)

    return result


@app.route('/generate_json', methods=['GET'])
def generate_json_endpoint():
    """
    处理生成JSON并返回接口
    """
    # 配置文件路径
    config_path = 'config.ini'

    # 读取配置文件
    root_directory, ip_range = read_config(config_path)

    # 生成JSON数据
    json_data = generate_json(root_directory, ip_range)

    # 将字典转换为JSON字符串并返回
    return json.dumps(json_data)


if __name__ == '__main__':
    # 运行Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)
