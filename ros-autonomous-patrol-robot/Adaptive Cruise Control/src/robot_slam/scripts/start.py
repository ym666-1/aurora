#!/usr/bin/env python
'''
Copyright (c) [Zachary]
本代码受版权法保护，未经授权禁止任何形式的复制、分发、修改等使用行为。
Author:Zachary
'''
import rospy
from std_msgs.msg import String
import decoder
import sys
import signal

interrupted = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

def detected_callback():
    """语音唤醒成功后的回调函数"""
    global detector  # 必须在函数最顶部声明，否则 Python 报 SyntaxError

    # 播放音频文件
    decoder.play_audio_file()
    # 设置启动参数
    rospy.set_param('start', True)
    # 发布启动任务的话题（不使用 latch=True，避免旧消息残留导致其他节点误启动）
    pub = rospy.Publisher('/start_mission', String, queue_size=10)
    rospy.sleep(0.2)
    pub.publish("start")
    rospy.loginfo("语音唤醒成功，已发布启动任务信号！")

    # 1. 终止热词检测器
    detector.terminate()

    # 2. 关闭ROS节点
    rospy.signal_shutdown("已成功发布启动信号，关闭节点")

    # 3. 退出程序
    sys.exit(0)

if __name__ == '__main__':
    # 初始化ROS节点
    rospy.init_node('game_node', anonymous=True)

    # 设置模型路径
    model = '/home/abot/GT117Z/src/robot_slam/resources/models/start.pmdl'

    # 捕获SIGINT信号，例如Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # 创建热词检测器（声明为全局变量，方便在回调中终止）
    # sensitivity 使用原值 0.62（经过实际调试验证的值）
    global detector
    detector = decoder.HotwordDetector(model, sensitivity=0.62)

    # 给音频硬件充分的预热时间，避免初始化时的噪声尖峰被误识别为唤醒词
    print('Waiting for audio hardware to stabilize...')
    rospy.sleep(3.0)
    print('Audio warmed up. Listening... Press Ctrl+C to exit')

    # 主循环
    detector.start(detected_callback=detected_callback,
                   interrupt_check=interrupt_callback,
                   sleep_time=0.03)

    # 保持ROS节点运行（实际执行到这里时节点已被关闭）
    rospy.spin()

