#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''
Copyright (c) [Zachary]
本代码受版权法保护，未经授权禁止任何形式的复制、分发、修改等使用行为。
Author:Zachary
'''

import rospy
import actionlib
from actionlib_msgs.msg import *
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseWithCovarianceStamped
from tf.transformations import quaternion_from_euler
from math import pi
from std_msgs.msg import String
from std_msgs.msg import Int32
from ar_track_alvar_msgs.msg import AlvarMarkers
from geometry_msgs.msg import Twist
from geometry_msgs.msg import Point
import sys
import os
import dynamic_reconfigure.client
from std_srvs.srv import Trigger, TriggerRequest
from TTS_audio.srv import StringService, StringServiceRequest
import time

time_val = 1
find_id = 0
id = 0
clue = 1

# 检测点索引，保持你原来的结构
points = [10, 11, 12, 13]

# 按识别顺序收集任务编号
task_numbers = []

point_audio = {
    12: "/home/abot/demo/src/robot_slam/mp3/01.mp3",
    13: "/home/abot/demo/src/robot_slam/mp3/02.mp3",
    14: "/home/abot/demo/src/robot_slam/mp3/03.mp3",
    15: "/home/abot/demo/src/robot_slam/mp3/04.mp3"
}

class navigation_demo:
    def __init__(self):
        self.set_pose_pub = rospy.Publisher('/initialpose', PoseWithCovarianceStamped, queue_size=5)
        self.arrive_pub = rospy.Publisher('/voiceWords', String, queue_size=10)
        self.find_sub = rospy.Subscriber('/object_position', Point, self.find_cb)
        self.ar_sub = rospy.Subscriber('/ar_pose_marker', AlvarMarkers, self.ar_cb)
        self.move_base = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        self.move_base.wait_for_server(rospy.Duration(60))
        self.pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1000)

        # 自动停车 launch
        self.auto_parking_launch = rospy.get_param(
            "~auto_parking_launch",
            "robot_slam auto_single_point_test.launch"
        )

        # 如果检测结果是 31~39, 则映射成 1~9
        # 例如 31 -> 1, 32 -> 2
        self.enable_task_id_31_to_39_mapping = rospy.get_param(
            "~enable_task_id_31_to_39_mapping",
            True
        )

        # 如果某些点想先导航到过渡点 14, 再开始停车, 保留这个开关
        self.go_transition_before_tasks = rospy.get_param(
            "~go_transition_before_tasks",
            True
        )

        # 等待视觉大模型检测服务
        rospy.loginfo("等待视觉大模型检测服务 /fruit_detection 可用...")
        rospy.wait_for_service('/fruit_detection', timeout=20)
        self.fruit_detection_service = rospy.ServiceProxy('/fruit_detection', Trigger)
        rospy.loginfo("视觉大模型检测服务连接成功!")

        # 等待并初始化 TTS 服务
        rospy.loginfo("等待TTS服务 /tts_service 可用...")
        rospy.wait_for_service('tts_service', timeout=20)
        self.tts_service = rospy.ServiceProxy('tts_service', StringService)
        rospy.loginfo("TTS服务连接成功!")

    def tts_client(self, text):
        """
        适配你的TTS服务: 请求字段为data
        """
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        try:
            request = StringServiceRequest()
            request.data = text
            response = self.tts_service(request)
            rospy.loginfo("TTS播报成功: %s | 响应: %s" % (text, response.result))
            return True
        except rospy.ServiceException as e:
            rospy.logerr("TTS服务调用失败: %s" % str(e))
            return False

    def call_fruit_detection_service(self):
        """调用视觉大模型检测服务"""
        try:
            rospy.set_param('/detect', 1)
            rospy.sleep(0.5)
            response = self.fruit_detection_service()
            rospy.loginfo("视觉大模型识别结果: %s" % response.message)
            return response.message
        except rospy.ServiceException as e:
            rospy.logerr("视觉大模型服务调用失败: %s" % e)
            return "无"

    def end24(self):
        """终点动作2/4"""
        global time_val
        time_val = 1
        msg = Twist()
        msg.linear.x = -0.25
        msg.linear.y = -0.1
        msg.angular.z = 0.0

        while time_val <= 13 and not rospy.is_shutdown():
            self.pub.publish(msg)
            rospy.sleep(0.1)
            time_val += 1

        self.stop_robot()

    def end13(self):
        """终点动作1/3"""
        global time_val
        time_val = 1
        msg = Twist()
        msg.linear.x = -0.3
        msg.linear.y = 0.3
        msg.angular.z = 0.0

        while time_val <= 13 and not rospy.is_shutdown():
            self.pub.publish(msg)
            rospy.sleep(0.1)
            time_val += 1

        self.stop_robot()

    def rotate(self):
        """旋转动作"""
        time1 = 0
        msg = Twist()
        msg.angular.z = 1.0

        while time1 <= 8 and not rospy.is_shutdown():
            self.pub.publish(msg)
            rospy.sleep(0.1)
            time1 += 1

        self.stop_robot()

    def right(self):
        """右移动作"""
        time1 = 0
        msg = Twist()
        msg.linear.y = -0.5

        while time1 <= 20 and not rospy.is_shutdown():
            self.pub.publish(msg)
            rospy.sleep(0.1)
            time1 += 1

        self.stop_robot()

    def stop_robot(self):
        msg = Twist()
        for _ in range(8):
            self.pub.publish(msg)
            rospy.sleep(0.03)

    def ar_cb(self, data):
        """AR标签回调"""
        global id
        if len(data.markers) > 0:
            id = data.markers[0].id
        else:
            id = 0

    def find_cb(self, data):
        """目标位置回调"""
        global find_id
        z = data.z

        if (1 < z <= 30) or (241 <= z < 255) or (255 < z <= 270):
            find_id = 1
        elif (31 <= z <= 60) or (271 <= z <= 300):
            find_id = 2
        elif (61 <= z <= 90) or (301 <= z <= 330):
            find_id = 3
        elif (91 <= z <= 120) or (331 <= z <= 360):
            find_id = 4
        elif (121 <= z <= 150) or (453 <= z <= 466):
            find_id = 5
        elif 151 <= z <= 180:
            find_id = 6
        elif 181 <= z <= 210:
            find_id = 7
        elif 211 <= z <= 240:
            find_id = 8

    def set_pose(self, p):
        """设置初始位姿"""
        if self.move_base is None:
            return False

        x, y, th = p

        pose = PoseWithCovarianceStamped()
        pose.header.stamp = rospy.Time.now()
        pose.header.frame_id = 'map'
        pose.pose.pose.position.x = x
        pose.pose.pose.position.y = y

        q = quaternion_from_euler(0.0, 0.0, th / 180.0 * pi)

        pose.pose.pose.orientation.x = q[0]
        pose.pose.pose.orientation.y = q[1]
        pose.pose.pose.orientation.z = q[2]
        pose.pose.pose.orientation.w = q[3]

        self.set_pose_pub.publish(pose)

        return True

    def _done_cb(self, status, result):
        """导航完成回调"""
        rospy.loginfo("导航完成! status=%s result=%s" % (status, result))
        self.arrive_pub.publish("arrived to target point")

    def _active_cb(self):
        """导航激活回调"""
        rospy.loginfo("[Navi] 导航已激活")

    def _feedback_cb(self, feedback):
        """导航反馈回调"""
        pass

    def goto(self, p):
        """导航到指定目标点"""
        rospy.loginfo("[Navi] 前往目标点: %s" % p)

        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = 'map'
        goal.target_pose.header.stamp = rospy.Time.now()

        goal.target_pose.pose.position.x = p[0]
        goal.target_pose.pose.position.y = p[1]

        q = quaternion_from_euler(0.0, 0.0, p[2] / 180.0 * pi)

        goal.target_pose.pose.orientation.x = q[0]
        goal.target_pose.pose.orientation.y = q[1]
        goal.target_pose.pose.orientation.z = q[2]
        goal.target_pose.pose.orientation.w = q[3]

        self.move_base.send_goal(goal, self._done_cb, self._active_cb, self._feedback_cb)

        result = self.move_base.wait_for_result(rospy.Duration(60))
        if not result:
            self.move_base.cancel_goal()
            rospy.loginfo("导航超时，取消目标")
            return False
        else:
            if self.move_base.get_state() == GoalStatus.SUCCEEDED:
                rospy.loginfo("到达目标点 %s 成功!" % p)
                return True
            else:
                rospy.logwarn("导航未成功, state=%s" % self.move_base.get_state())
                return False

    def cancel(self):
        """取消所有导航目标"""
        self.move_base.cancel_all_goals()
        return True

    def normalize_task_id(self, task_id):
        """
        将检测到的任务编号映射为 goals 下标。
        你原程序 mission() 里允许 31~50。
        但 go_to_task_positions() 原来又判断 1~9。
        这里做兼容：
        31 -> 1
        32 -> 2
        ...
        39 -> 9

        如果检测服务本来就返回 1~9, 也直接使用。
        """
        if 1 <= task_id <= 9:
            return task_id

        if self.enable_task_id_31_to_39_mapping:
            if 31 <= task_id <= 39:
                return task_id - 30

        return task_id

    def mission(self, point):
        """单个检测点任务逻辑"""
        global clue, id, find_id

        id = 0
        find_id = 0

        rospy.sleep(0.1)

        rospy.loginfo("导航到检测点 → 目标点索引%s" % point)
        self.goto(goals[point])

        detect_result = self.call_fruit_detection_service()
        rospy.loginfo("当前检测点%s结果: %s" % (point, detect_result))

        if detect_result != "无":
            try:
                raw_task_id = int(detect_result)

                # 保持你原来的检测范围 31~50, 同时也兼容 1~9
                if (31 <= raw_task_id <= 50) or (1 <= raw_task_id <= 9):
                    task_id = self.normalize_task_id(raw_task_id)

                    if 1 <= task_id <= 9:
                        task_numbers.append(task_id)
                        rospy.loginfo(
                            "收集到任务编号: raw=%s -> task=%s" %
                            (raw_task_id, task_id)
                        )

                        tts_text = u"已检测第%d条线索为%d号" % (clue, task_id)
                        self.tts_client(tts_text)
                        clue += 1
                    else:
                        rospy.logwarn(
                            "任务编号映射后不在1~9范围: raw=%s mapped=%s" %
                            (raw_task_id, task_id)
                        )
                else:
                    rospy.logwarn("任务编号超出范围: %s" % raw_task_id)

            except ValueError:
                rospy.logwarn("检测结果不是有效数字: %s" % detect_result)

        id = 0
        find_id = 0

    def recognize(self, p):
        """执行单个检测点识别"""
        self.mission(p)
        return True

    def auto_parking(self, target_x, target_y, target_yaw_deg):
        """
        调用已经调通的自动停车程序:
        auto_single_point_test.launch

        该程序内部会完成：
        1. 自动入口选择
        2. move_base 到入口
        3. yaw 对齐
        4. 入框
        5. 深入停车
        6. 退出框
        """
        rospy.logwarn(
            "开始自动停车: x=%.3f y=%.3f yaw=%.1f" %
            (target_x, target_y, target_yaw_deg)
        )

        # 保险：取消当前 move_base 目标，防止和停车程序抢 /cmd_vel
        self.cancel()
        rospy.sleep(0.3)

        cmd = (
            "roslaunch %s "
            "target_x:=%.3f "
            "target_y:=%.3f "
            "target_yaw:=%.1f"
        ) % (
            self.auto_parking_launch,
            target_x,
            target_y,
            target_yaw_deg
        )

        rospy.logwarn("执行自动停车命令: %s" % cmd)
        ret = os.system(cmd)
        rospy.logwarn("自动停车程序退出码: %s" % str(ret))

        rospy.sleep(0.5)

        if ret == 0:
            rospy.loginfo("自动停车程序执行完成")
            return True

        rospy.logwarn("自动停车程序异常退出")
        return False

    def go_to_task_positions(self):
        """
        按任务编号顺序自动停车。
        保持你的识别顺序不变。
        不再直接 self.goto(goals[task_id]),
        而是调用 auto_single_point_test.launch。
        """
        rospy.loginfo("开始按顺序前往任务位置: %s" % task_numbers)

        # 保留你原来的过渡点逻辑
        if self.go_transition_before_tasks:
            try:
                rospy.loginfo("先前往过渡点 goals[14]")
                self.goto(goals[14])
                rospy.sleep(0.5)
            except Exception as e:
                rospy.logwarn("前往过渡点 goals[14] 失败或不存在: %s" % str(e))

        for idx, task_id in enumerate(task_numbers):
            if 1 <= task_id <= 9:
                rospy.logwarn(
                    "======= 开始执行第%d个任务点: %d号 =======" %
                    (idx + 1, task_id)
                )

                target = goals[task_id]
                target_x = target[0]
                target_y = target[1]
                target_yaw = target[2]

                rospy.loginfo(
                    "任务点%d坐标: x=%.3f y=%.3f yaw=%.1f" %
                    (task_id, target_x, target_y, target_yaw)
                )

                ok = self.auto_parking(target_x, target_y, target_yaw)

                if ok:
                    tts_text = u"已到达任务点%d号" % task_id
                    self.tts_client(tts_text)
                    rospy.logwarn("任务点%d停车完成" % task_id)
                else:
                    tts_text = u"任务点%d号停车失败" % task_id
                    self.tts_client(tts_text)
                    rospy.logwarn("任务点%d停车失败，继续下一个任务" % task_id)

                rospy.sleep(1.0)
            else:
                rospy.logwarn("任务编号%s无效，跳过" % task_id)

    def start_mission_callback(self, msg):
        """接收到启动任务信号后的回调"""
        if msg.data == "start":
            rospy.loginfo("接收到语音唤醒的启动信号，开始执行任务！")

            # 防止二次启动时旧任务残留
            global task_numbers
            task_numbers = []

            global clue
            clue = 1

            # 执行所有检测点任务
            for i, p in enumerate(points):
                rospy.loginfo("\n=== 开始处理第%s个检测点 ===" % (i + 1))
                self.recognize(p)

            rospy.loginfo("\n=== 所有检测点处理完成 ===")
            rospy.loginfo("收集到的任务编号: %s" % task_numbers)

            # 按识别顺序自动停车
            self.go_to_task_positions()

            # 前往最终目标点 (使用自动停车策略，避免终点附近障碍物导致不敢进)
            try:
                target_final = goals[16]
                rospy.loginfo("前往最终目标点 goals[16]: x=%.3f y=%.3f yaw=%.1f" %
                              (target_final[0], target_final[1], target_final[2]))

                # 优先尝试自动停车 (入口选择 + 入框 + 障碍物停车接受)
                ok = self.auto_parking(target_final[0], target_final[1], target_final[2])

                if not ok:
                    # 自动停车失败则回退到 move_base 导航到终点
                    rospy.logwarn("自动停车未成功，回退到 move_base 导航到终点")
                    self.goto(target_final)

                # 终点微调动作
                self.end24()

                tts_text = u"已到达终点"
                self.tts_client(tts_text)

            except Exception as e:
                rospy.logerr("前往终点失败: %s" % str(e))

if __name__ == "__main__":
    rospy.init_node('navigation_demo', anonymous=True)
    rospy.loginfo("导航节点初始化成功！等待语音唤醒信号...")

    try:
        goalListX = rospy.get_param('~goalListX')
        goalListY = rospy.get_param('~goalListY')
        goalListYaw = rospy.get_param('~goalListYaw')

        x_list = [float(x.strip()) for x in goalListX.split(",") if x.strip()]
        y_list = [float(y.strip()) for y in goalListY.split(",") if y.strip()]
        yaw_list = [float(yaw.strip()) for y in goalListYaw.split(",") if yaw.strip()]

        goals = []
        for x, y, yaw in zip(x_list, y_list, yaw_list):
            goals.append([x, y, yaw])

        rospy.loginfo("成功加载点位数量: %d" % len(goals))

    except KeyError as e:
        rospy.logerr("未找到点位参数 %s, 请检查launch文件！" % e)
        sys.exit(1)
    except Exception as e:
        rospy.logerr("解析点位失败: %s" % e)
        sys.exit(1)

    # 初始化导航类
    navi = navigation_demo()

    # 订阅语音唤醒的启动话题
    rospy.Subscriber('/start_mission', String, navi.start_mission_callback)

    # 保持节点运行，等待启动信号
    rospy.spin()