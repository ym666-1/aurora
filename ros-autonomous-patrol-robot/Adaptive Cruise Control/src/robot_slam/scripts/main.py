#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''
Copyright (c) [Zachary]
本代码受版权法保护，未经授权禁止任何形式的复制、分发、修改等使用行为。
Author:Zachary
'''
# =============== 导入依赖库/ROS消息 ===============
import rospy
import actionlib
from actionlib_msgs.msg import *
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseWithCovarianceStamped
from tf.transformations import quaternion_from_euler
import tf
from math import pi
import math
from std_msgs.msg import String, Int32
from sensor_msgs.msg import LaserScan
from ar_track_alvar_msgs.msg import AlvarMarkers
from geometry_msgs.msg import Twist
from geometry_msgs.msg import Point
import sys
import dynamic_reconfigure.client
from std_srvs.srv import Trigger, TriggerRequest
from TTS_audio.srv import StringService, StringServiceRequest


def normalize_angle(a):
    """将角度归一化到 [-pi, pi]"""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


# =============== 全局变量定义 ===============
time_val = 1
find_id = 0
id = 0
clue = 1
points = [10, 11, 12, 13]
task_numbers = []
point_audio = {
    12: "/home/abot/GT117Z/src/robot_slam/mp3/01.mp3",
    13: "/home/abot/GT117Z/src/robot_slam/mp3/02.mp3",
    14: "/home/abot/GT117Z/src/robot_slam/mp3/03.mp3",
    15: "/home/abot/GT117Z/src/robot_slam/mp3/04.mp3"
}

# =============== 核心导航类定义 ===============
class navigation_demo:
    def __init__(self):
        self.set_pose_pub = rospy.Publisher('/initialpose', PoseWithCovarianceStamped, queue_size=5)
        self.arrive_pub = rospy.Publisher('/voiceWords', String, queue_size=10)
        # AR/物体检测订阅
        self.find_sub = rospy.Subscriber('/object_position', Point, self.find_cb)
        self.ar_sub = rospy.Subscriber('/ar_pose_marker', AlvarMarkers, self.ar_cb)

        self.move_base = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        self.move_base.wait_for_server(rospy.Duration(60))
        self.pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1000)

        # =============== 激光雷达精准停靠 ===============
        self.latest_scan = None
        self.scan_sub = rospy.Subscriber(
            "/scan_filtered", LaserScan,
            self.scan_cb, queue_size=1
        )
        self.tf_listener = tf.TransformListener()
        self.map_frame = "map"
        self.base_frame = "base_footprint"

        # yaw 对齐参数
        self.kp_yaw = 1.5
        self.max_align_wz = 0.8
        self.yaw_tolerance = 0.08

        # ===============================================
        self.enable_task_id_31_to_39_mapping = rospy.get_param(
            "~enable_task_id_31_to_39_mapping",
            True
        )
        self.go_transition_before_tasks = rospy.get_param(
            "~go_transition_before_tasks",
            True
        )

        self.go_transition_after_detection = rospy.get_param(
            "~go_transition_after_detection",
            True
        )

        rospy.loginfo("等待视觉大模型检测服务 /fruit_detection 可用...")
        rospy.wait_for_service('/fruit_detection', timeout=20)
        self.fruit_detection_service = rospy.ServiceProxy('/fruit_detection', Trigger)
        rospy.loginfo("视觉大模型检测服务连接成功!")

        rospy.loginfo("等待TTS服务 /tts_service 可用...")
        rospy.wait_for_service('tts_service', timeout=20)
        self.tts_service = rospy.ServiceProxy('tts_service', StringService)
        rospy.loginfo("TTS服务连接成功!")

    def tts_client(self, text):
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
        global time_val
        time_val = 1
        msg = Twist()
        msg.linear.x = -0.25
        msg.linear.y = 0.0
        msg.angular.z = 0.0
        while time_val <= 13 and not rospy.is_shutdown():
            self.pub.publish(msg)
            rospy.sleep(0.1)
            time_val += 1
        self.stop_robot()

    def end13(self):
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
        time1 = 0
        msg = Twist()
        msg.angular.z = 1.0
        while time1 <= 8 and not rospy.is_shutdown():
            self.pub.publish(msg)
            rospy.sleep(0.1)
            time1 += 1
        self.stop_robot()

    def right(self):
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

    # =============== 激光雷达辅助方法 ===============
    def scan_cb(self, msg):
        """激光雷达数据回调"""
        self.latest_scan = msg

    def get_sector_min_range(self, deg_min, deg_max):
        """获取指定扇区内的最小距离（米）"""
        if self.latest_scan is None:
            return float('inf')
        msg = self.latest_scan
        if msg.angle_increment == 0.0:
            return float('inf')
        a0 = math.radians(min(deg_min, deg_max))
        a1 = math.radians(max(deg_min, deg_max))
        rmin = float('inf')
        for i, r in enumerate(msg.ranges):
            if math.isnan(r) or math.isinf(r):
                continue
            a = msg.angle_min + i * msg.angle_increment
            if a0 <= a <= a1:
                if r < rmin:
                    rmin = r
        return rmin

    def lookup_robot_pose(self):
        """TF查询机器人当前位姿 (x, y, yaw) map 坐标系"""
        try:
            self.tf_listener.waitForTransform(
                self.map_frame, self.base_frame,
                rospy.Time(0), rospy.Duration(0.3)
            )
            trans, rot = self.tf_listener.lookupTransform(
                self.map_frame, self.base_frame, rospy.Time(0)
            )
            _, _, yaw = tf.transformations.euler_from_quaternion(rot)
            return trans[0], trans[1], yaw
        except Exception as e:
            rospy.logwarn_throttle(1.0, "TF lookup failed: %s" % e)
            return None

    def align_yaw(self, target_yaw):
        """旋转机器人到目标朝向"""
        rate = rospy.Rate(20)
        start_time = rospy.Time.now()
        timeout = 8.0
        stable_count = 0
        required_stable = 3

        while not rospy.is_shutdown():
            pose = self.lookup_robot_pose()
            if pose is None:
                self.stop_robot()
                rate.sleep()
                continue

            _, _, yaw = pose
            err = normalize_angle(target_yaw - yaw)
            elapsed = (rospy.Time.now() - start_time).to_sec()

            if elapsed > timeout:
                rospy.logwarn("yaw对齐超时 err=%.3f" % err)
                self.stop_robot()
                return abs(err) < 0.25

            if abs(err) < self.yaw_tolerance:
                stable_count += 1
                self.stop_robot()
                if stable_count >= required_stable:
                    return True
                rate.sleep()
                continue

            stable_count = 0
            cmd = Twist()
            cmd.angular.z = max(-self.max_align_wz,
                                min(self.max_align_wz, self.kp_yaw * err))

            if abs(cmd.angular.z) < 0.015:
                cmd.angular.z = 0.0

            self.pub.publish(cmd)
            rate.sleep()

        return False

    # ===============================================

    def ar_cb(self, data):
        global id
        if len(data.markers) > 0:
            id = data.markers[0].id
        else:
            id = 0

    def find_cb(self, data):
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
        rospy.loginfo("导航完成! status=%s result=%s" % (status, result))
        self.arrive_pub.publish("arrived to target point")

    def _active_cb(self):
        rospy.loginfo("[Navi] 导航已激活")

    def _feedback_cb(self, feedback):
        pass

    def goto(self, p):
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
        self.move_base.cancel_all_goals()
        return True

    # =============== 激光雷达精准停靠 ===============
    def lidar_precision_park(self, target_x, target_y,
                             approach_speed=0.08,
                             stop_distance=0.15,
                             timeout=12.0):
        """
        激光雷达精准停靠:
        - 朝目标点 (target_x, target_y) 方向缓慢前进
        - 检测前方障碍物距离 < stop_distance 时停车
        - 到达目标附近后旋转对齐 yaw
        - 超时 timeout 秒后强制停车
        返回 True=成功停靠, False=超时
        """
        rospy.logwarn("开始精准停靠: 目标(%.3f, %.3f) 速度=%.3f 停止距离=%.2fm 超时=%.1fs" %
                      (target_x, target_y, approach_speed, stop_distance, timeout))
        start_time = rospy.Time.now()
        rate = rospy.Rate(20)

        no_progress_count = 0
        last_dist = None

        while not rospy.is_shutdown():
            elapsed = (rospy.Time.now() - start_time).to_sec()
            if elapsed > timeout:
                rospy.logwarn("精准停靠超时(%.1fs)，强制停车" % timeout)
                self.stop_robot()
                return False

            # 获取机器人位姿
            pose = self.lookup_robot_pose()
            if pose is None:
                self.stop_robot()
                rate.sleep()
                continue

            rx, ry, ryaw = pose
            dx = target_x - rx
            dy = target_y - ry
            dist = math.sqrt(dx * dx + dy * dy)

            # 已到达目标
            if dist < 0.02:
                rospy.logwarn("已到达目标点附近，停车")
                self.stop_robot()
                return True

            # 读取雷达关键扇区
            front = self.get_sector_min_range(-15, 15)
            left_front = self.get_sector_min_range(15, 55)
            right_front = self.get_sector_min_range(-55, -15)
            left_side = self.get_sector_min_range(55, 125)
            right_side = self.get_sector_min_range(-125, -55)
            nearest = min(front, left_front, right_front, left_side, right_side)

            rospy.loginfo_throttle(0.3,
                "精准停靠: dist=%.3f front=%.3f nearest=%.3f" %
                (dist, front, nearest))

            # 紧急停止: 任何方向太近
            if nearest < 0.10:
                rospy.logwarn("紧急停车: 距离障碍物仅 %.3fm" % nearest)
                self.stop_robot()
                return True

            # 前端障碍物停车
            if front <= stop_distance:
                rospy.logwarn("前端障碍物 %.3fm <= %.2fm，停车" % (front, stop_distance))
                self.stop_robot()
                # 如果距目标较远也接受，避免撞到东西还继续走
                return True

            # 计算 map frame 下朝目标的速度
            if dist > 0.01:
                vx_map = approach_speed * (dx / dist)
                vy_map = approach_speed * (dy / dist)
            else:
                vx_map = 0.0
                vy_map = 0.0

            # 转换为 base frame 速度
            cos_yaw = math.cos(ryaw)
            sin_yaw = math.sin(ryaw)
            cmd = Twist()
            cmd.linear.x = cos_yaw * vx_map + sin_yaw * vy_map
            cmd.linear.y = -sin_yaw * vx_map + cos_yaw * vy_map
            cmd.angular.z = 0.0

            # 近障碍物减速
            slow_threshold = 0.40
            if front < slow_threshold:
                speed_scale = max(0.15, (front - stop_distance) /
                                  (slow_threshold - stop_distance))
                cmd.linear.x *= speed_scale
                cmd.linear.y *= speed_scale

            # 侧向防碰撞
            if cmd.linear.y > 0 and (left_front < 0.18 or left_side < 0.18):
                cmd.linear.y = 0.0
            if cmd.linear.y < 0 and (right_front < 0.18 or right_side < 0.18):
                cmd.linear.y = 0.0

            # 死区
            if abs(cmd.linear.x) < 0.005:
                cmd.linear.x = 0.0
            if abs(cmd.linear.y) < 0.005:
                cmd.linear.y = 0.0

            # 无进展检测
            if elapsed > 2.0 and last_dist is not None:
                progress = last_dist - dist
                if abs(progress) < 0.003:
                    no_progress_count += 1
                else:
                    no_progress_count = 0
                if no_progress_count >= 40:
                    rospy.logwarn("精准停靠无进展(%.3f)，接受当前位置" % dist)
                    self.stop_robot()
                    return True
            last_dist = dist

            self.pub.publish(cmd)
            rate.sleep()

        return False

    def normalize_task_id(self, task_id):
        if 1 <= task_id <= 9:
            return task_id
        return task_id

    def mission(self, point):
        global clue, id, find_id
        id = 0
        find_id = 0
        rospy.sleep(0.1)
        rospy.loginfo("导航到检测点 → 目标点索引%s" % point)
        self.goto(goals[point])
        detect_result = self.call_fruit_detection_service()
        rospy.loginfo("当前检测点%s原始结果: '%s'" % (point, detect_result))

        if detect_result != "无":
            try:
                import re
                numbers = re.findall(r'\d+', detect_result)

                if numbers:
                    task_id = int(numbers[0])

                    if 1 <= task_id <= 9:
                        task_numbers.append(task_id)
                        rospy.loginfo("收集到任务编号: '%s' -> %d" % (detect_result, task_id))
                        tts_text = u"已检测第%d条线索为%d号" % (clue, task_id)
                        self.tts_client(tts_text)
                        clue += 1
                    else:
                        rospy.logwarn("任务编号超出1-9范围: %d" % task_id)
                else:
                    rospy.logwarn("未在识别结果中找到数字: '%s'" % detect_result)

            except Exception as e:
                rospy.logwarn("检测结果处理失败: '%s' -> 错误: %s" % (detect_result, str(e)))

        id = 0
        find_id = 0

    def recognize(self, p):
        self.mission(p)
        return True

    def go_to_task_positions(self):
        rospy.loginfo("开始按顺序前往任务位置: %s" % task_numbers)
        if self.go_transition_before_tasks:
            try:
                rospy.loginfo("先前往过渡点 goals[14]")
                self.goto(goals[14])
                rospy.sleep(0.5)
            except Exception as e:
                rospy.logwarn("前往过渡点 goals[14] 失败或不存在: %s" % str(e))
        for idx, task_id in enumerate(task_numbers):
            if 1 <= task_id <= 9:
                rospy.logwarn("======= 开始执行第%d个任务点: %d号 =======" % (idx + 1, task_id))
                target = goals[task_id]
                rospy.loginfo("任务点%d坐标: x=%.3f y=%.3f yaw=%.1f" %
                              (task_id, target[0], target[1], target[2]))

                rospy.loginfo("任务点%d: 使用move_base导航到目标坐标" % task_id)
                self.goto(target)

                # 无论move_base是否成功，都尝试精准停靠逼近目标点
                rospy.loginfo("任务点%d: 执行激光精确停靠" % task_id)
                self.lidar_precision_park(target[0], target[1],
                                          approach_speed=0.08,
                                          stop_distance=0.15,
                                          timeout=12.0)
                tts_text = u"已到达任务点%d号" % task_id
                self.tts_client(tts_text)
                rospy.logwarn("任务点%d到达完成" % task_id)
                rospy.sleep(1.0)
            else:
                rospy.logwarn("任务编号%s无效，跳过" % task_id)

    def start_mission_callback(self, msg):
        if msg.data == "start":
            # 验证语音唤醒信号来源是否真实
            # 防止latch残留或无关节点误发
            if not rospy.get_param('/start', False):
                rospy.logwarn("接收到未经验证的启动信号 (缺少 /start 参数)，忽略！")
                return

            rospy.loginfo("接收到语音唤醒的启动信号，开始执行任务！")
            global task_numbers
            task_numbers = []
            global clue
            clue = 1
            for i, p in enumerate(points):
                rospy.loginfo("\n=== 开始处理第%s个检测点 ===" % (i + 1))
                self.recognize(p)
            rospy.loginfo("\n=== 所有检测点处理完成 ===")
            rospy.loginfo("收集到的任务编号: %s" % task_numbers)

            # 根据开关决定是否在收集完线索后前往中间点14
            if self.go_transition_after_detection:
                try:
                    rospy.loginfo("经过中间点14 (过渡点)")
                    self.goto(goals[14])
                    rospy.sleep(0.5)
                except Exception as e:
                    rospy.logwarn("前往中间点14失败: %s" % str(e))

            self.go_to_task_positions()
            # 前往最终目标点
            try:
                target_final = goals[16]
                rospy.loginfo("前往最终目标点 goals[16]: x=%.3f y=%.3f yaw=%.1f" %
                              (target_final[0], target_final[1], target_final[2]))
                self.goto(target_final)
                # 激光精准停靠到终点
                rospy.loginfo("最终点: 激光精准停靠")
                self.lidar_precision_park(target_final[0], target_final[1],
                                          approach_speed=0.06,
                                          stop_distance=0.18,
                                          timeout=15.0)
                # 最终 yaw 对齐
                rospy.loginfo("最终点: yaw对齐")
                final_yaw_rad = math.radians(target_final[2])
                self.align_yaw(final_yaw_rad)
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

        if isinstance(goalListX, list) and isinstance(goalListY, list) and isinstance(goalListYaw, list):
            x_list = [float(x) for x in goalListX]
            y_list = [float(y) for y in goalListY]
            yaw_list = [float(yaw) for yaw in goalListYaw]

            goals = []
            for x, y, yaw in zip(x_list, y_list, yaw_list):
                goals.append([x, y, yaw])
            rospy.loginfo("成功加载点位数量: %d" % len(goals))
        else:
            rospy.logerr("参数格式错误，期望列表类型")
            sys.exit(1)

    except KeyError as e:
        rospy.logerr("未找到点位参数 %s, 请检查launch文件！" % e)
        sys.exit(1)
    except Exception as e:
        rospy.logerr("解析点位失败: %s" % e)
        sys.exit(1)

    navi = navigation_demo()

    # 等待一小段时间让系统稳定，同时避免因旧latch消息残留导致的误启动
    # 确保 roscore 和所有节点完全就绪后再订阅启动信号
    rospy.sleep(2.0)
    rospy.loginfo("系统就绪，开始监听语音唤醒启动信号...")
    rospy.Subscriber('/start_mission', String, navi.start_mission_callback)
    rospy.spin()

