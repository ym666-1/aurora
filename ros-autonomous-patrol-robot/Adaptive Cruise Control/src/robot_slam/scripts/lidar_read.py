#!/usr/bin/env python
# coding=utf-8
import rospy
import numpy as np
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
fontd = 0.0
pub = None
class LidarDataCapture:
    def __init__(self):
        global pub
        # 初始化ROS节点
        rospy.init_node('lidar_data_capture', anonymous=True)
        # 订阅激光雷达话题，通常为/scan
        rospy.Subscriber("/scan", LaserScan, self.scan_callback)
        # 数据存储列表
        self.lidar_data = []
        self.filtered_data = []
        # 截取参数设置
        self.min_range = 0.1            # 最小有效距离(米)
        self.max_range = 10.0           # 最大有效距离(米)
        self.filter_threshold = 450000  # 过滤阈值(可根据需要调整)
        # Publisher放在init_node之后
        pub = rospy.Publisher('cmd_vel', Twist, queue_size=10)
        rospy.loginfo("激光雷达数据截取节点已启动...")
    def scan_callback(self, scan):
        """激光雷达数据回调函数"""
        try:
            # 获取距离数据
            ranges = list(scan.ranges)
            num_readings = len(ranges)
            # 记录原始数据
            self.lidar_data = ranges
            # 数据截取和过滤
            filtered_ranges = self.filter_lidar_data(ranges)
            self.filtered_data = filtered_ranges
            # 显示处理结果
            rospy.loginfo("接收到 %d 个激光扫描读数", num_readings)
            rospy.loginfo("过滤后有效数据点: %d", len(filtered_ranges))
            # 显示障碍物距离
            if len(filtered_ranges) > 0:
                front_distance = filtered_ranges[len(filtered_ranges) // 2]
                rospy.loginfo("右侧障碍物距离: %.2f 米", front_distance)
                rospy.loginfo("左侧障碍物距离: %.2f 米", filtered_ranges[0])
                rospy.loginfo("前方障碍物距离: %.2f 米", filtered_ranges[270])
            vel_msg = Twist()
            # 设置线速度 (单位: m/s)
            rospy.loginfo("Z前方障碍物距离: %.2f 米", filtered_ranges[270])
            if filtered_ranges[270] < 0.30:
                vel_msg.linear.x = 0.0   # 前进方向速度
                vel_msg.linear.y = 0.0   # 横向平移速度
                vel_msg.linear.z = 0.0   # 垂直方向速度
                rospy.loginfo("停止")
            else:
                vel_msg.linear.x = 0.1   # 前进方向速度
                vel_msg.linear.y = 0.0   # 横向平移速度
                vel_msg.linear.z = 0.0   # 垂直方向速度
                rospy.loginfo("前进")
            pub.publish(vel_msg)
        except Exception as e:
            rospy.logerr("处理激光雷达数据时出错: %s", str(e))
    def filter_lidar_data(self, ranges):
        """过滤激光雷达数据"""
        filtered_data = []
        for distance in ranges:
            # 检查数据有效性
            if distance >= self.min_range and distance <= self.max_range:
                # 转换为整数格式（可选，便于某些计算）
                int_distance = int(float(distance) * 100)
                # 应用过滤阈值
                if int_distance <= self.filter_threshold:
                    filtered_data.append(distance)
                else:
                    filtered_data.append(0.0)  # 超出阈值的数据设为0
            else:
                filtered_data.append(0.0)  # 无效数据设为0
        return filtered_data
   
    def run(self):
        """主运行循环"""
        rate = rospy.Rate(10)  # 10Hz
        while not rospy.is_shutdown():
            # 可以在这里添加其他处理逻辑
            rate.sleep()
def main():
    try:
        lidar_capture = LidarDataCapture()
        # 设置ROS关闭时的回调
        rospy.on_shutdown(lidar_capture.save_data_to_file)
        # 开始运行
        lidar_capture.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("节点已关闭")
if __name__ == '__main__':
    main()
