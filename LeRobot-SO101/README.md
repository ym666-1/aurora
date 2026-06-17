<h1 align="center">🤖 ArmGPT — 基于 VLA 模型的机械臂模仿学习系统</h1>

<p align="center">
  <b>Vision-Language-Action Manipulation System</b><br>
  端到端模仿学习 · 人类示教数据驱动 · 实机部署验证
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyTorch-2.0+-ee4c2c?logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/HuggingFace-LeRobot-ffcc00?logo=huggingface&logoColor=white" alt="LeRobot">
  <img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-SO--100%20%2B%20RealSense-orange" alt="Platform">
</p>

<p align="center">
  <a href="#项目简介">简介</a> •
  <a href="#系统架构">架构</a> •
  <a href="#技术栈">技术栈</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#项目结构">结构</a> •
  <a href="#致谢">致谢</a>
</p>

---

## 项目简介

传统机械臂控制依赖手工示教与规则编程，泛化能力差、难以应对多任务场景。本项目基于 HuggingFace LeRobot 框架，搭建了一套完整的**端到端模仿学习系统**，让机器人像大语言模型一样，从人类示范中直接学习操作技能。

**核心流程：**

```
遥操作示教 → 数据采集 → 策略训练 → 仿真评估 → 实机部署
```

### 亮点

- 🧠 **前沿策略集成**：支持 ACT、SmolVLA（0.45B 参数 VLA 基础模型）、Diffusion Policy 等多种 SOTA 模型
- 🤖 **真实硬件验证**：在 RealSense D435i + SO-100 低成本硬件上完成闭环部署
- 🏗️ **完整工程链路**：从数据采集到实机推理的全链路开发流程
- 📦 **模块化设计**：策略、硬件、训练配置解耦，可快速适配新任务

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      ArmGPT 系统架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   数据采集    │    │   策略训练    │    │   实机部署    │       │
│  │              │    │              │    │              │       │
│  │ RealSense    │    │ ACT          │    │ MuJoCo       │       │
│  │ D435i 相机   │───▶│ SmolVLA      │───▶│ 仿真评估     │       │
│  │ SO-100 Leader│    │ Diffusion    │    │              │       │
│  │ SO-100 Follower   │ Policy       │    │ Real Robot   │       │
│  └──────────────┘    └──────────────┘    │ Inference    │       │
│         │                   │            └──────────────┘       │
│         ▼                   ▼                  ▲                │
│  ┌──────────────┐    ┌──────────────┐          │                │
│  │ LeRobotDataset│    │ Accelerate   │          │                │
│  │ (Parquet+MP4)│    │ wandb 监控   │──────────┘                │
│  └──────────────┘    └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 模块 | 技术 |
|------|------|
| **策略模型** | ACT、SmolVLA（0.45B VLA）、Diffusion Policy、Pi0/Pi0.5、GR00T N1 |
| **深度学习** | PyTorch、HuggingFace Accelerate、Transformer、Diffusion Model |
| **数据采集** | RealSense D435i 深度相机、SO-100 Leader-Follower 遥操作臂 |
| **仿真评估** | MuJoCo、LIBERO、MetaWorld |
| **数据格式** | LeRobotDataset（Parquet + MP4）、HuggingFace Hub |
| **训练监控** | wandb、TensorBoard |
| **开发语言** | Python、C++ |

---

## 快速开始

### 环境安装

```bash
# 克隆仓库
git clone https://github.com/lelaj666/ROS-Robot-Portfolio.git
cd ArmGPT

# 创建虚拟环境
conda create -n armgpt python=3.10 -y
conda activate armgpt

# 安装依赖
pip install -e .
```

### 数据采集（遥操作）

```bash
# 启动 Leader-Follower 遥操作，采集示教数据
python -m lerobot.scripts.lerobot_control_robot \
  --robot.type=so100 \
  --control.type=teleoperate \
  --control.display_data=true
```

### 策略训练

```bash
# 使用 ACT 策略训练
lerobot-train \
  --policy=act \
  --dataset.repo_id=lelaj666/dataset \
  --output_dir=outputs/train/act

# 使用 SmolVLA 基础模型微调
lerobot-train \
  --policy=smolvla \
  --dataset.repo_id=lelaj666/dataset \
  --output_dir=outputs/train/smolvla
```

### 实机推理

```bash
# 将训练好的策略部署到实机
python -m lerobot.scripts.lerobot_control_robot \
  --robot.type=so100 \
  --control.type=record \
  --control.fps=30 \
  --policy.path=outputs/train/act/checkpoints/last/pretrained_model
```

---

## 项目结构

```
ArmGPT/
├── src/lerobot/
│   ├── cameras/            # 相机驱动（RealSense / OpenCV）
│   ├── common/             # 通用工具与设备接口
│   ├── configs/            # 训练/评估配置
│   ├── datasets/           # LeRobotDataset 数据处理
│   ├── envs/               # 仿真环境（LIBERO / MetaWorld）
│   ├── optim/              # 优化器与学习率调度
│   ├── policies/           # 策略模型
│   │   ├── act/            # ACT (Action Chunking Transformer)
│   │   ├── diffusion/      # Diffusion Policy
│   │   ├── smolvla/        # SmolVLA (0.45B VLA 基础模型)
│   │   ├── pi0/            # Pi0 (Physical Intelligence)
│   │   ├── pi05/           # Pi0.5
│   │   ├── groot/          # GR00T N1
│   │   └── sarm/           # SARM
│   ├── robot_devices/      # 机器人硬件驱动（SO-100 等）
│   └── scripts/            # 训练/评估/控制脚本
├── docs/                   # 文档
├── examples/               # 示例代码
└── benchmarks/             # 性能基准测试
```

---

## 支持的策略模型

| 模型 | 类型 | 说明 |
|------|------|------|
| **ACT** | 模仿学习 | Action Chunking with Transformers，时序动作分块预测 |
| **Diffusion Policy** | 模仿学习 | 基于去噪扩散过程建模多模态动作分布 |
| **SmolVLA** | VLA 基础模型 | 0.45B 参数视觉-语言-动作模型，支持语言指令驱动 |
| **Pi0 / Pi0.5** | VLA 基础模型 | Physical Intelligence 出品的通用操作策略 |
| **GR00T N1** | VLA 基础模型 | NVIDIA 机器人基础模型 |
| **SARM** | 模仿学习 | 自适应动作表示学习 |
| **VQ-BeT** | 模仿学习 | 向量量化行为 Transformer |

---

## 硬件配置

本系统基于以下低成本硬件平台搭建：

| 组件 | 型号 | 用途 |
|------|------|------|
| 机械臂 | SO-100 (Leader + Follower) | 遥操作示教 + 策略执行 |
| 深度相机 | Intel RealSense D435i | 视觉观测（RGB-D） |
| 计算平台 | NVIDIA GPU (CUDA) | 模型训练与推理 |

> 💡 SO-101 是 HuggingFace 推荐的开源低成本机械臂方案，全套硬件成本约 $200，适合个人研究与学习。

---

## 致谢

- [HuggingFace LeRobot](https://github.com/huggingface/lerobot) — 本项目基于 LeRobot 框架构建
- [Physical Intelligence](https://www.physicalintelligence.company/) — Pi0/Pi0.5 策略
- [NVIDIA GR00T](https://developer.nvidia.com/isaac/gr00t) — GR00T N1 机器人基础模型
- [ACT](https://real-stanford.github.io/act/) — Action Chunking with Transformers

---

## License

本项目基于 [Apache License 2.0](LICENSE) 开源。
