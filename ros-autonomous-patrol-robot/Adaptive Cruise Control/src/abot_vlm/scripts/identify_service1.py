#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
数学题识别节点 - 将两位数结果映射到1-9
映射关系：
31->1, 32->2, 33->3
40->4, 41->5, 42->6
49->7, 50->8, 51->9
Author: Zachary
'''
import rospy
import cv2
import numpy as np
import time
from sensor_msgs.msg import Image as ROSImage
from std_srvs.srv import Trigger, TriggerResponse
import base64
import sys
import os
import re

# 从配置文件导入API密钥
try:
    from API_KEY import YI_KEY
except ImportError:
    rospy.logerr("无法导入API_KEY，请确保API_KEY.py文件存在且包含YI_KEY变量")
    YI_KEY = ""

# 结果映射表
RESULT_MAPPING = {
    31: "1", 32: "2", 33: "3",
    40: "4", 41: "5", 42: "6",
    49: "7", 50: "8", 51: "9"
}

def imgmsg_to_cv2(img_msg):
    """将ROS图像消息转换为OpenCV格式"""
    try:
        dtype = np.dtype("uint8")
        dtype = dtype.newbyteorder('>' if img_msg.is_bigendian else '<')
        image_opencv = np.ndarray(
            shape=(img_msg.height, img_msg.width, 3), 
            dtype=dtype, 
            buffer=img_msg.data
        )

        if img_msg.is_bigendian == (sys.byteorder == 'little'):
            image_opencv = image_opencv.byteswap().newbyteorder()

        if img_msg.encoding == "rgb8":
            image_opencv = cv2.cvtColor(image_opencv, cv2.COLOR_RGB2BGR)
        elif img_msg.encoding == "bgr8":
            pass
        elif img_msg.encoding == "mono8":
            image_opencv = cv2.cvtColor(image_opencv, cv2.COLOR_GRAY2BGR)
        else:
            rospy.logerr("Unsupported encoding: %s", img_msg.encoding)
            return None

        return image_opencv
    except Exception as e:
        rospy.logerr(f"图像转换失败: {e}")
        return None

class MathProblemIdentifier:
    """数学题识别器类"""
    
    def __init__(self):
        self.save_path = '/home/abot/GT117Z/src/abot_vlm/temp2/vl_now.jpg'
        self.max_retry = 3
        self.timeout = 30
        
        # 确保保存目录存在
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # 初始化大模型客户端
        if YI_KEY:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=YI_KEY,
                base_url="https://ark.cn-beijing.volces.com/api/v3"
            )
        else:
            rospy.logerr("API密钥未配置，无法初始化大模型客户端")
            self.client = None
        
        # 有效结果列表（映射后的1-9）
        self.valid_results = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "无"]
        
        # 修改Prompt，要求识别完整的两位数结果
        self.prompt = (
            '图中有一道数学题，请计算并给出最终的数字答案。'
            '要求：最后一行只输出答案数字（仅数字，无任何其他字符）。'
            '如果无法识别或计算，最后一行输出"无"。'
        )
        
        # 有效的原始结果（映射前的两位数）
        self.valid_raw_results = list(RESULT_MAPPING.keys())
        
        rospy.loginfo("数学题识别器初始化完成")
        rospy.loginfo(f"映射关系: {RESULT_MAPPING}")
    
    def map_result(self, number):
        """将原始结果映射到1-9"""
        if number in RESULT_MAPPING:
            mapped = RESULT_MAPPING[number]
            rospy.loginfo(f"映射: {number} -> {mapped}")
            return mapped
        else:
            rospy.logwarn(f"数字 {number} 不在映射表中")
            return "无"
    
    def extract_number(self, text):
        """从文本中提取数字"""
        # 查找所有数字
        numbers = re.findall(r'\d+', text)
        if numbers:
            # 取最后一个数字
            last_number = int(numbers[-1])
            rospy.loginfo(f"提取到的数字: {last_number}")
            return last_number
        return None
    
    def save_image(self, cv_image):
        """保存图像"""
        try:
            cv2.imwrite(self.save_path, cv_image)
            rospy.loginfo(f'图像已保存至: {self.save_path}')
            return True
        except Exception as e:
            rospy.logerr(f'保存图像失败: {e}')
            return False
    
    def identify_math_answer(self, img_path=None):
        """识别数学题答案并进行映射"""
        if img_path is None:
            img_path = self.save_path
        
        # 检查客户端是否初始化
        if not self.client:
            rospy.logerr("大模型客户端未初始化")
            return "无"
        
        # 检查图像文件是否存在
        if not os.path.exists(img_path):
            rospy.logerr(f"图像文件不存在: {img_path}")
            return "无"
        
        # 编码图像
        try:
            with open(img_path, 'rb') as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            image_url = f'data:image/jpeg;base64,{image_base64}'
        except Exception as e:
            rospy.logerr(f'读取图片失败: {e}')
            return "无"
        
        # 重试循环
        for retry_count in range(self.max_retry):
            try:
                # 调用大模型API
                response = self.client.chat.completions.create(
                    model="doubao-1-5-vision-pro-32k-250115",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": self.prompt},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]
                        }
                    ],
                    timeout=self.timeout
                )
                
                # 解析结果
                result_str = response.choices[0].message.content.strip()
                rospy.loginfo(f'大模型原始返回:\n{result_str}')
                
                # 提取数字
                raw_number = self.extract_number(result_str)
                
                if raw_number is None:
                    rospy.logwarn(f'未能从返回中提取数字，第{retry_count+1}次重试...')
                    if retry_count < self.max_retry - 1:
                        time.sleep(1)
                    continue
                
                # 检查是否为有效的原始结果
                if raw_number in self.valid_raw_results:
                    # 进行映射
                    final_result = self.map_result(raw_number)
                    if final_result in self.valid_results:
                        rospy.loginfo(f'识别成功: {raw_number} -> {final_result}')
                        return final_result
                else:
                    rospy.logwarn(f'数字 {raw_number} 不在有效范围 {self.valid_raw_results}，第{retry_count+1}次重试...')
                    if retry_count < self.max_retry - 1:
                        time.sleep(1)
                    
            except Exception as e:
                rospy.logerr(f'调用大模型失败 (第{retry_count+1}次): {e}')
                if retry_count < self.max_retry - 1:
                    time.sleep(1)
        
        rospy.logerr(f'超过最大重试次数({self.max_retry}次)，返回"无"')
        return "无"
    
    def image_callback(self, image_msg):
        """图像回调函数"""
        # 获取检测标志
        detect = rospy.get_param('/detect', 255)
        
        if detect == 1:
            rospy.loginfo("检测到触发信号，开始处理图像")
            
            # 转换图像
            cv_image = imgmsg_to_cv2(image_msg)
            if cv_image is None:
                rospy.logerr("图像转换失败")
                return
            
            # 保存图像
            if not self.save_image(cv_image):
                return
            
            # 重置检测标志
            rospy.set_param('/detect', 255)
            
            # 识别数学题答案并进行映射
            result = self.identify_math_answer()
            rospy.loginfo(f'最终映射结果: {result}')
            
            # 存储结果到参数服务器
            rospy.set_param('/math_answer', result)
            
            # 也可以发布识别结果
            # self.result_pub.publish(result)
    
    def handle_service_request(self, req):
        """服务请求处理函数"""
        try:
            result = self.identify_math_answer()
            rospy.loginfo(f'服务调用结果: {result}')
            return TriggerResponse(
                success=True,
                message=f"识别结果: {result}"
            )
        except Exception as e:
            rospy.logerr(f'服务调用失败: {e}')
            return TriggerResponse(
                success=False,
                message=f"识别失败: {str(e)}"
            )
    
    def get_mapping_info(self):
        """获取映射信息（用于调试）"""
        info = "结果映射关系:\n"
        for raw, mapped in RESULT_MAPPING.items():
            info += f"  {raw} -> {mapped}\n"
        return info

def main():
    """主函数"""
    rospy.init_node('math_identifier_node', anonymous=True)
    
    # 创建识别器实例
    identifier = MathProblemIdentifier()
    
    # 打印映射信息
    rospy.loginfo(identifier.get_mapping_info())
    
    # 订阅图像话题
    rospy.Subscriber('/usb_cam/image_raw', ROSImage, identifier.image_callback)
    
    # 初始化参数
    rospy.set_param('/detect', 255)
    rospy.set_param('/math_answer', '无')
    
    # 创建服务
    rospy.Service('fruit_detection', Trigger, identifier.handle_service_request)
    
    rospy.loginfo('数学题识别节点启动成功！')
    rospy.loginfo('等待图像输入...')
    
    try:
        rospy.spin()
    except KeyboardInterrupt:
        rospy.loginfo("节点关闭")
    finally:
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
