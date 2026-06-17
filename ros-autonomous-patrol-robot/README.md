# 🤖 ROS 自主巡逻与射击机器人

> **Team GT117Z** — 基于 ROS 1 的自主巡逻与射击机器人系统，集成了 SLAM 建图、自主导航、视觉识别、语音交互与射击控制等功能。

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [硬件平台](#硬件平台)
- [软件依赖](#软件依赖)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [巡航模式](#巡航模式)
- [射击模式](#射击模式)
- [导航配置](#导航配置)
- [TF 坐标树](#tf-坐标树)

---

## 项目简介

本项目是一个完整的自主巡逻与射击机器人系统，包含两大核心模式：

- **巡航模式（cruise/）**：机器人自主巡逻，通过视觉大模型（VLM）识别数学题目线索，语音播报结果，并精准导航至目标点位。
- **射击模式（shoot/）**：机器人接收语音指令，自主导航至射击位置，通过 AR Tag 追踪对准目标并执行射击。

项目基于 **ROS 1 (catkin)** 构建，运行在 Ubuntu 18.04/20.04 上，使用麦克纳姆轮底盘实现全向移动。

---

## 功能特性

### 🗺️ SLAM 与导航
- 支持 **gmapping** 和 **Cartographer** 两种 SLAM 建图方案
- **AMCL** 定位 + **move_base** 自主导航
- **TEB / DWA** 局部路径规划器，支持全向移动
- LiDAR 精准泊车（基于开口检测与走廊分析）
- EKF 多传感器融合（轮式里程计 + IMU）

### 👁️ 视觉识别
- **VLM 视觉大模型**：调用字节跳动豆包模型进行数学题目识别
- **AR Tag 追踪**：基于 `ar_track_alvar` 的目标对准
- **目标检测**：find_object_2d + SuperPoint 特征匹配
- **颜色检测**：循线、火焰检测
- **人脸检测与识别**：HOG + SVM / Haar 级联分类器
- **多目标跟踪**：KCF + Kalman 滤波、Lucas-Kanade 光流

### 🎙️ 语音交互
- **语音唤醒**：Picovoice 热词检测（关键词 "start"）
- **语音识别**：科大讯飞 SDK
- **语音播报（TTS）**：字节跳动火山引擎 WebSocket API

### 🔫 射击控制
- 串口协议控制射击机构（8 字节指令，`0x55` 头）
- AR Tag 精准对准后射击（航向角阈值 0.025 rad）
- 支持旋转靶（1-5 号）和移动靶（6-8 号）
- 每个目标最多 3 次射击

---

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    语音唤醒 (Picovoice)                │
│                         ↓                            │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ 巡逻模式  │    │   射击模式    │    │  语音交互  │  │
│  │  cruise   │    │    shoot     │    │  TTS/ASR  │  │
│  └────┬─────┘    └──────┬───────┘    └───────────┘  │
│       ↓                  ↓                           │
│  ┌──────────────────────────────────────────────┐   │
│  │              核心任务调度 (robot_slam)           │   │
│  │        main.py / navigation_multi_goals       │   │
│  └──────────────────┬───────────────────────────┘   │
│                     ↓                                │
│  ┌──────────────────────────────────────────────┐   │
│  │            move_base 导航栈                     │   │
│  │    全局规划 (Dijkstra) + 局部规划 (TEB/DWA)     │   │
│  └──────────────────┬───────────────────────────┘   │
│                     ↓                                │
│  ┌──────────────────────────────────────────────┐   │
│  │            底层硬件驱动                          │   │
│  │  底盘驱动 | IMU | LiDAR | 摄像头 | 射击机构    │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 硬件平台

| 参数 | 规格 |
|------|------|
| 底盘尺寸 | 36 cm × 31 cm |
| 底盘重量 | ~0.735 kg |
| 驱动方式 | 四轮麦克纳姆轮（全向移动） |
| 最大线速度 | x: 0.65 m/s, y: 0.35 m/s |
| LiDAR | RPLidar（0.1-12 m, 360°, 5.5 Hz） |
| IMU | 板载 IMU（Madgwick 滤波） |
| 摄像头 | USB 摄像头（640×480, YUYV） |
| 底盘通信 | 串口 `/dev/abot`，921600 baud |
| 射击机构 | 串口 `/dev/shoot`，9600 baud |

---

## 软件依赖

### 系统环境
- **操作系统**：Ubuntu 18.04 / 20.04
- **ROS 版本**：ROS Melodic / Noetic
- **构建系统**：catkin

### ROS 依赖包
```
roscpp rospy std_msgs geometry_msgs nav_msgs sensor_msgs
actionlib actionlib_msgs move_base_msgs tf tf2_ros tf_conversions
move_base map_server amcl gmapping cartographer_ros
rplidar_ros usb_cam robot_pose_ekf imu_filter_madgwick
ar_track_alvar robot_state_publisher joint_state_publisher
gazebo_ros dynamic_reconfigure teb_local_planner
```

### Python 依赖
```bash
pip install openai cv2 numpy websockets asyncio pyserial picovoice
```

---

## 项目结构

```
ros-autonomous-patrol-robot/
│
├── cruise/                              # 🚗 巡航模式
│   ├── GT117Z.sh                        # 一键启动脚本
│   ├── config/                          # 导航参数配置
│   │   ├── costmap_common_params.yaml
│   │   ├── teb_local_planner_params.yaml
│   │   ├── dwa_local_planner_params.yaml
│   │   └── ...
│   ├── launch/                          # Launch 启动文件
│   │   ├── GameStart.launch             # 语音唤醒启动
│   │   ├── navigation.launch            # 导航栈启动
│   │   ├── gmapping.launch              # SLAM 建图
│   │   └── ...
│   ├── maps/                            # 已建地图
│   └── src/                             # ROS 功能包
│       ├── abot_base/                   # 底盘驱动（底盘、IMU、URDF、滤波）
│       ├── abot_find/                   # 2D 目标检测（SuperPoint）
│       ├── abot_vlm/                    # 视觉大模型服务（豆包 VLM）
│       ├── nav_command/                 # 自定义导航消息
│       ├── ocr_detect/                  # OCR 文字检测
│       ├── robot_slam/                  # 核心导航与任务逻辑
│       ├── track_tag/                   # AR Tag 追踪
│       └── TTS_audio/                   # 语音合成服务
│
└── shoot/                               # 🔫 射击模式
    ├── config/                          # 导航参数配置
    ├── launch/                          # Launch 启动文件
    ├── maps/                            # 已建地图
    └── src/                             # ROS 功能包
        ├── abot_base/                   # 底盘驱动
        ├── abot_find/                   # 目标检测
        ├── cam_track/                   # 摄像头追踪
        ├── color_pkg/                   # 颜色检测 / 循线 / 火焰检测
        ├── face_pkg/                    # 人脸检测与识别
        ├── imu_filter/                  # IMU 滤波器（Madgwick）
        ├── robot_slam/                  # 射击任务逻辑
        ├── robot_voice/                 # 科大讯飞语音 SDK
        ├── shoot_cmd/                   # 射击机构控制（C++）
        ├── track_tag/                   # AR Tag 追踪
        └── tracker_pkg/                 # 目标跟踪（KCF / Kalman / 光流）
```

---

## 快速开始

### 1. 克隆项目

```bash
cd ~/catkin_ws/src
git clone https://github.com/<your-username>/ros-autonomous-patrol-robot.git
```

### 2. 安装依赖

```bash
cd ~/catkin_ws
rosdep install --from-paths src --ignore-src -r -y
pip install openai numpy websockets pyserial
```

### 3. 编译

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### 4. 启动机器人底盘

```bash
roslaunch abot_bringup robot_with_imu.launch
```

### 5. 启动巡航模式

> 巡航模式通过一键脚本 `GT117Z.sh` 启动，自动打开多个终端标签页运行所有节点。

```bash
cd ~/catkin_ws/src/ros-autonomous-patrol-robot/cruise
bash GT117Z.sh
```

脚本自动依次启动以下节点：

| 终端标签 | 启动内容 | 说明 |
|---------|---------|------|
| 1 | `roscore` | ROS Master |
| 2 | `abot_bringup robot_with_imu.launch` | 底盘驱动 + IMU + EKF |
| 3 | `robot_slam navigation.launch` | 导航栈（AMCL + move_base） |
| 4 | `track_tag usb_cam_with_calibration.launch` | USB 摄像头驱动 |
| 5 | `track_tag ar_track_camera.launch` | AR Tag 检测 |
| 6 | `abot_vlm vlm_node.launch` | 视觉大模型服务 |
| 7 | `robot_slam multi_goal.launch` | 多目标导航 |
| 8 | `robot_slam view_nav.launch` | RViz 可视化 |
| 9 | `TTS_audio TTS.py` | 语音合成服务 |
| 10 | `robot_slam GameStart.launch` | 语音唤醒监听 |

### 6. 启动射击模式

> 射击模式通过一键脚本 `OB9EVL.sh` 启动，自动打开多个终端标签页运行所有节点。

```bash
cd ~/catkin_ws/src/ros-autonomous-patrol-robot/shoot
bash OB9EVL.sh
```

脚本自动依次启动以下节点：

| 终端标签 | 启动内容 | 说明 |
|---------|---------|------|
| 1 | `roscore` | ROS Master |
| 2 | `abot_bringup robot_with_imu.launch` | 底盘驱动 + IMU + EKF |
| 3 | `abot_bringup shoot.launch` | 射击机构驱动 |
| 4 | `robot_slam navigation.launch` | 导航栈（AMCL + move_base） |
| 5 | `track_tag usb_cam_with_calibration.launch` | USB 摄像头驱动 |
| 6 | `track_tag ar_track_camera.launch` | AR Tag 检测 |
| 7 | `find_object_2d find_object_2d.launch` | 2D 目标检测 |
| 8 | `robot_voice tts_subscribe` | 科大讯飞语音合成 |
| 9 | `robot_slam shoot_target.py` | 语音指令解析 |
| 10 | `robot_slam demo.py` | 主任务节点 |
| 11 | `robot_slam GameStart.launch` | 语音唤醒监听 |
| 12 | `robot_slam multi_goal.launch` | 多目标导航 |

---

## 巡航模式

### 任务流程

1. **语音唤醒** → Picovoice 检测热词 "start"，发布 `/start_mission` 信号
2. **线索探测** → 导航至 4 个检测点（编号 10-13）
3. **视觉识别** → 拍照并发送至豆包 VLM 识别数学题，结果（31-51）映射为任务 ID（1-9）
4. **语音播报** → TTS 朗读识别到的线索信息
5. **任务执行** → 根据线索导航至对应任务点位，LiDAR 精准泊车
6. **终点到达** → 航向角对齐 + 微调定位

### 自定义消息

| 消息/服务 | 类型 | 说明 |
|-----------|------|------|
| `NavCmd.msg` | `bool start_nav, float64 target_x/y, float64 target_yaw, string robot_id` | 导航目标指令 |
| `VisionResult.srv` | `string result → bool success` | 视觉识别结果 |
| `StringService.srv` | `string data → string result` | TTS 语音合成服务 |

---

## 射击模式

### 任务流程

1. **语音指令** → 解析中文语音，提取旋转靶（1-5）和移动靶（6-8）编号
2. **自主导航** → 通过 move_base 导航至射击位置
3. **目标对准** → AR Tag 追踪，航向角精对准（阈值 0.025 rad）
4. **执行射击** → 串口发送 8 字节射击指令，每靶最多 3 次
5. **切换目标** → 导航至下一个目标位置，重复对准与射击

### 射击串口协议

| 指令 | 字节序列 |
|------|---------|
| 射击 | `0x55 0x01 0x12 0x00 0x00 0x00 0x01 0x69` |
| 停止 | `0x55 0x01 0x11 0x00 0x00 0x00 0x01 0x68` |

---

## 导航配置

### 巡航模式（TEB 规划器）

| 参数 | 值 | 说明 |
|------|-----|------|
| 规划器 | TEB Local Planner | 支持全向移动 |
| 最大 x 速度 | 0.65 m/s | 前进/后退 |
| 最大 y 速度 | 0.35 m/s | 横移 |
| 控制器频率 | 15 Hz | |
| 规划器频率 | 3 Hz | |
| 代价地图分辨率 | 0.02 m | |
| 障碍物检测范围 | 3.0 m | |

### 射击模式（DWA 规划器）

| 参数 | 值 | 说明 |
|------|-----|------|
| 规划器 | DWA Local Planner | |
| 最大 x 速度 | 0.4 m/s | |
| 控制器频率 | 10 Hz | |

---

## TF 坐标树

```
map
 └── odom                    (AMCL / Cartographer)
      └── base_footprint     (robot_pose_ekf)
           └── base_link     (fixed)
                ├── laser_link    (前方 6cm, 上方 18cm)
                ├── camera_link   (前方 13cm, 上方 12.8cm)
                ├── imu_link      (前方 4cm)
                └── usb_cam       (上方 30cm, 旋转 90°)
```

---

## 许可证

本项目仅供学习与竞赛使用。
