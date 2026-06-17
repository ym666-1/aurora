# 硬件配置指南

## 所需硬件

| 组件 | 型号 | 数量 | 预算 |
|------|------|------|------|
| Leader 机械臂 | SO-100 | 1 | ~$100 |
| Follower 机械臂 | SO-100 | 1 | ~$100 |
| 深度相机 | Intel RealSense D435i | 1 | ~$250 |
| USB 串口线 | USB-C / Micro-USB | 2 | - |
| 固定支架 | 3D 打印 / 铝型材 | 1 | - |

## 连接拓扑

```
┌─────────────┐
│   PC (GPU)   │
│              │
│  USB1 ──────┼──── SO-100 Leader (舵机总线)
│  USB2 ──────┼──── SO-100 Follower (舵机总线)
│  USB3 ──────┼──── RealSense D435i
└─────────────┘
```

## 舵机配置

SO-100 使用 Feetech STS3215 总线舵机，6 自由度：

| 关节 | ID | 说明 |
|------|-----|------|
| Joint 1 | 1 | 底座旋转 |
| Joint 2 | 2 | 肩部俯仰 |
| Joint 3 | 3 | 肘部俯仰 |
| Joint 4 | 4 | 腕部旋转 |
| Joint 5 | 5 | 腕部俯仰 |
| Joint 6 | 6 | 夹爪开合 |

## 环境要求

- Ubuntu 22.04 / Windows 11
- Python 3.10+
- CUDA 11.8+（训练需要 GPU）
- librealsense2 SDK
