#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rospy
from ar_track_alvar_msgs.msg import AlvarMarkers
id=0
class ARTracker:
    def __init__(self):
        # 初始化ROS节点，命名为'ar_tracker_node'，并设置为匿名节点
        rospy.init_node('ar_tracker_node', anonymous=True)
        # 创建一个订阅者，订阅AR标记的消息，消息类型为AlvarMarkers，回调函数为ar_cb
        self.sub = rospy.Subscriber('/ar_pose_marker', AlvarMarkers, self.ar_cb)

    # AR标记消息的回调函数
    def ar_cb(self, data):
	    global id
        # 遍历接收到的所有AR标记
            for marker in data.markers:
		    id=marker.id
		    print id
           

if __name__ == '__main__':
    try:
        # 创建ARTracker对象
        ar_tracker = ARTracker()
        # 进入ROS事件循环
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

