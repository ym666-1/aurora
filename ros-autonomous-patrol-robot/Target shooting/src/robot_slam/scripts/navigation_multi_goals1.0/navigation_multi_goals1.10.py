#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import rospy
import math
import actionlib
import serial
import time
from std_msgs.msg import String, Int32
from actionlib_msgs.msg import *
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseWithCovarianceStamped, Point, Twist
from tf_conversions import transformations
from math import pi
import dynamic_reconfigure.client
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
from ar_track_alvar_msgs.msg import AlvarMarkers

Yaw_th = 0.050  # 0.045     #0.044981
Yaw_th1 = 0.035     #35 #42
Yaw_th2 = 0.398   #0.42 #0.393702
# 设置串口和波特率
serialPort = "/dev/shoot"
baudRate = 9600
# 打开串口
ser = serial.Serial(port=serialPort, baudrate=baudRate, parity="N", bytesize=8, stopbits=1)
id = 255
flog0 = 255
flog1 = 255
flog2 = 255
flog3 = 255
flog4 = 255
count = 0
time_cnt = 0  # 避免和内置 time 冲突，改名

move_flog = 0
Yaw_th = 0.065
Min_y = -0.23
Max_y = -0.21
Yaw_th1 = 0.004
ar_flog = 255
case = 255
case1 = 255
case2 = 255
case3 = 255
target_id_rotating = 255  # 修复变量名下划线
target_id_moving = 255    # 修复变量名下划线
find_cb_executed = False  # 补充缺失的标记变量


class navigation_demo:
    def __init__(self):
	self.find_cb_executed = False  # 初始化标记
        self.set_pose_pub = rospy.Publisher('/initialpose', PoseWithCovarianceStamped, queue_size=5)
        self.move_base = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        self.sub = rospy.Subscriber('/ar_pose_marker', AlvarMarkers, self.ar_cb)
        self.find_sub = rospy.Subscriber('/object_position', Point, self.find_cb)
        self.pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1000)
        self.arrive_pub = rospy.Publisher('/voiceWords', String, queue_size=10)
        # 修复订阅者的正确写法（下划线、类成员）
        self.target_id_rotating_sub = rospy.Subscriber('target_id_rotating', Int32, self.target_id_rotating_callback)
        self.target_id_moving_sub = rospy.Subscriber('target_id_moving', Int32, self.target_id_moving_callback)

        self.move_base.wait_for_server(rospy.Duration(60))
        

    def end(self):
        global time_cnt
        msg = Twist()
        msg.linear.x = -0.4
        msg.linear.y = -0.25
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0
        while time_cnt <= 11:
            self.pub.publish(msg)
            rospy.sleep(0.1)
            time_cnt += 1

    def find_cb(self, data):
        global flog0, flog1, flog2, count, move_flog, case
        if self.find_cb_executed:
            return
        # 获取接收到的Point消息
        point_msg = data
        flog0 = point_msg.x - 320
        # 计算偏差的绝对值
        flog1 = abs(flog0)
        print '************'
        print case
        print '************'
        # 如果偏差的绝对值大于0.5
        if abs(flog1) > 3 and case == 0:
            # 创建一个Twist消息
            msg = Twist()
            # 设置消息的角速度为偏差乘以0.01
            msg.angular.z = -0.015 * flog0
            # 发布Twist消息
            self.pub.publish(msg)
        # 如果偏差的绝对值小于等于0.5
        elif abs(flog1) <= 3:
            # 发送射击指令
            ser.write(b'\x55\x01\x12\x00\x00\x00\x01\x69')
            print ('射击')
            # 等待0.1秒
            time.sleep(0.1)
            # 发送停止射击指令
            ser.write(b'\x55\x01\x11\x00\x00\x00\x01\x68')
            # 这里假设goals已定义，实际需确保外部有定义
            self.goto(goals[4])
            self.goto(goals[1])
            rospy.sleep(1)
            case = 1
            self.find_cb_executed = True

    def ar_cb(self, data):
        global ar_flog, case, target_id_rotating, target_id_moving
        for marker in data.markers:
            # 修复条件语句语法（括号、逻辑）
            if marker.id == target_id_rotating and case == 1:
                ar_x_0 = marker.pose.pose.position.x
                ar_y_0 = marker.pose.pose.position.y
                print "X: ", ar_x_0
                print "Y: ", ar_y_0
                ar_x_0_abs = abs(ar_x_0)
                if ar_x_0_abs >= Yaw_th:
                    msg = Twist()
                    msg.angular.z = -1 * ar_x_0
                    self.pub.publish(msg)
                elif Min_y <= ar_y_0 <= Max_y:
                    ser.write(b'\x55\x01\x12\x00\x00\x00\x01\x69')
                    print('射击')
                    rospy.sleep(0.1)
                    ser.write(b'\x55\x01\x11\x00\x00\x00\x01\x68')
                    rospy.sleep(2)
                    print case
                    # 假设goals已定义
                    self.goto(goals[5])
                    self.goto(goals[2])
                    rospy.sleep(1)
                    case = 2
            if marker.id == target_id_moving and case == 2:
                ar_x_0 = marker.pose.pose.position.x
                ar_x_0_abs = abs(ar_x_0)
                print(ar_x_0_abs)
                if ar_x_0_abs >= Yaw_th1:
                    msg = Twist()
                    msg.angular.z = -0.5 * ar_x_0
                    self.pub.publish(msg)
                elif ar_x_0_abs < Yaw_th1:
                    ser.write(b'\x55\x01\x12\x00\x00\x00\x01\x69')
                    print ('射击')
                    rospy.sleep(0.1)
                    ser.write(b'\x55\x01\x11\x00\x00\x00\x01\x68')
                    case = 3
                    # 自身类调用，用self
                    self.goto(goals[3])
                    self.end()
                    rospy.sleep(1)

    def target_id_rotating_callback(self, msg):
        global target_id_rotating
        target_id_rotating = msg.data
        rospy.loginfo("收到 target_id_rotating: %d", target_id_rotating)

    def target_id_moving_callback(self, msg):
        global target_id_moving
        target_id_moving = msg.data
        rospy.loginfo("收到 target_id_moving: %d", target_id_moving)

    def set_pose(self, p):
        if self.move_base is None:
            return False
        x, y, th = p
        pose = PoseWithCovarianceStamped()
        pose.header.stamp = rospy.Time.now()
        pose.header.frame_id = 'map'
        pose.pose.pose.position.x = x
        pose.pose.pose.position.y = y
        q = transformations.quaternion_from_euler(0.0, 0.0, th / 180.0 * pi)
        pose.pose.pose.orientation.x = q[0]
        pose.pose.pose.orientation.y = q[1]
        pose.pose.pose.orientation.z = q[2]
        pose.pose.pose.orientation.w = q[3]
        self.set_pose_pub.publish(pose)
        return True

    def _done_cb(self, status, result):
        rospy.loginfo("navigation done! status:%d result:%s" % (status, result))
        #arrive_str = "arrived to traget point"
        #self.arrive_pub.publish(arrive_str)

    def _active_cb(self):
        rospy.loginfo("[Navi] navigation has be actived")

    def _feedback_cb(self, feedback):
        msg = feedback
        # rospy.loginfo("[Navi] navigation feedback\r\n%s"%feedback)

    def goto(self, p):
        rospy.loginfo("[Navi] goto %s" % p)
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = 'map'
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = p[0]
        goal.target_pose.pose.position.y = p[1]
        q = transformations.quaternion_from_euler(0.0, 0.0, p[2] / 180.0 * pi)
        goal.target_pose.pose.orientation.x = q[0]
        goal.target_pose.pose.orientation.y = q[1]
        goal.target_pose.pose.orientation.z = q[2]
        goal.target_pose.pose.orientation.w = q[3]
        self.move_base.send_goal(goal, self._done_cb, self._active_cb, self._feedback_cb)
        result = self.move_base.wait_for_result(rospy.Duration(60))
        if not result:
            self.move_base.cancel_goal()
            rospy.loginfo("Timed out achieving goal")
        else:
            state = self.move_base.get_state()
            if state == GoalStatus.SUCCEEDED:
                rospy.loginfo("reach goal %s succeeded!" % p)
        return True

    def cancel(self):
        self.move_base.cancel_all_goals()
        return True


if __name__ == "__main__":
    rospy.init_node('navigation_demo', anonymous=True)
    # 给默认参数，避免未设置参数时报错
    goalListX = rospy.get_param('~goalListX', '2.0,2.0,2.0')
    goalListY = rospy.get_param('~goalListY', '2.0,4.0,2.0')
    goalListYaw = rospy.get_param('~goalListYaw', '0,90.0,2.0')

    goals = [[float(x), float(y), float(yaw)] for (x, y, yaw) in
             zip(goalListX.split(","), goalListY.split(","), goalListYaw.split(","))]
    print(goals)
    r = rospy.Rate(1)
    r.sleep()

    def publish_audio():
        publisher = rospy.Publisher('audio_topic', String, queue_size=10)
        publish_count = 2
        while not rospy.is_shutdown() and publish_count > 0:
            audio_data = "audio message"
            publisher.publish(audio_data)
            rospy.loginfo("Published:%s", audio_data)
            publish_count -= 1
            rate = rospy.Rate(1)
            rate.sleep()

    navi = navigation_demo()
    while True:
        success = rospy.get_param('/start', False)
        if success:
            rospy.loginfo("开始比赛")
            break
    publish_audio()
    rospy.sleep(15)
    navi.goto(goals[0])
    rospy.sleep(1)
    case = 0
    while not rospy.is_shutdown():
        r.sleep()
