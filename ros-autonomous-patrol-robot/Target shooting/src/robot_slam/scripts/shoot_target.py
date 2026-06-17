#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import String, Int32

# 定义全局变量存储目标 ID
target_id_rotating = None  # 旋转靶 ID
target_id_moving = None    # 移动靶 ID

# 中文数字到旋转靶 ID 的映射字典
target_id_rotating_mapping = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5
}

# 中文数字到移动靶 ID 的映射字典
target_id_moving_mapping = {
    "六": 6,
    "七": 7,
    "八": 8
}

def chinese_callback(msg):
    """
    处理接收到的中文消息，检测旋转靶和移动靶的 ID。
    :param msg: 接收到的消息
    """
    global arrive_pub, target_id_rotating, target_id_moving
    # 检测旋转靶的 target_id
    for keyword, value in target_id_rotating_mapping.items():
        if keyword in msg.data:
            target_id_rotating = value
            rospy.loginfo("检测到旋转靶关键词: %s, 设置 target_id_rotating = %d" % (keyword, target_id_rotating))
            arrive_str = "比赛开始，旋转靶为{}号".format(keyword)
            arrive_pub.publish(arrive_str)
            try:
                target_id_rotating_pub.publish(target_id_rotating)
            except Exception as e:
                rospy.logerr("发布旋转靶 target_id 时出错: %s" % str(e))
            break
    # 检测移动靶的 target_id
    for keyword, value in target_id_moving_mapping.items():
        if keyword in msg.data:
            target_id_moving = value
            rospy.loginfo("检测到移动靶关键词: %s, 设置 target_id_moving = %d" % (keyword, target_id_moving))
            arrive_str = "移动靶为{}号".format(keyword)
            arrive_pub.publish(arrive_str)
            try:
                target_id_moving_pub.publish(target_id_moving)
            except Exception as e:
                rospy.logerr("发布移动靶 target_id 时出错: %s" % str(e))
            break

def chinese_subscriber():
    """
    初始化 ROS 节点，创建发布者和订阅者。
    """
    global arrive_pub, target_id_rotating_pub, target_id_moving_pub
    rospy.init_node('chinese_subscriber', anonymous=True)

    # 创建发布者
    arrive_pub = rospy.Publisher('/voiceWords', String, queue_size=10)
    target_id_rotating_pub = rospy.Publisher('target_id_rotating', Int32, queue_size=10)
    target_id_moving_pub = rospy.Publisher('target_id_moving', Int32, queue_size=10)

    # 创建订阅者
    rospy.Subscriber("chinese_topic", String, chinese_callback)

    rospy.loginfo("Chinese subscriber node started")
    rospy.spin()

if __name__ == '__main__':
    try:
        chinese_subscriber()
    except rospy.ROSInterruptException:
        rospy.loginfo("ROS 节点被中断")
