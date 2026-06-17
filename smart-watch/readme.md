# 基于 STM32 与 RTOS 的智能手表 GUI 开发

基于 STM32F401 + FreeRTOS + LVGL 的嵌入式智能手表系统，实现多任务实时调度、图形界面渲染与触摸手势交互。

---

## 📋 项目简介

本项目是一个嵌入式智能手表原型系统，采用 STM32F401 作为主控芯片，搭载 240×240 圆形 LCD 显示屏和电容触摸传感器，运行 FreeRTOS 实时操作系统，使用 LVGL 图形库构建用户界面。

系统支持：
- RTC 实时时钟显示
- 触摸按钮交互
- 左右滑动手势切换页面
- 多任务实时调度与资源保护

---

## 🛠️ 硬件平台

| 组件 | 型号 | 说明 |
|------|------|------|
| 主控芯片 | STM32F401 | ARM Cortex-M4, 84MHz |
| 显示屏 | GC9A01 | 240×240 圆形 LCD, SPI 接口 |
| 触摸传感器 | CST816D | 电容触摸, I2C 接口 |
| 时钟源 | RTC | LSI 32KHz 内部时钟 |

---

## 💻 软件架构

```
┌─────────────────────────────────────────────┐
│              应用层 (Application)            │
│    ┌─────────────┐      ┌─────────────┐     │
│    │  HomeTask   │      │  TaskLvgl   │     │
│    │ (主表盘任务) │      │ (屏幕刷新)   │     │
│    └──────┬──────┘      └──────┬──────┘     │
│           │   消息队列          │            │
│           ▼                    ▼            │
│    ┌─────────────────────────────────┐      │
│    │        LVGL 图形库 8.3.11       │      │
│    └─────────────────────────────────┘      │
├─────────────────────────────────────────────┤
│              驱动层 (Drivers)                │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│    │ GC9A01  │  │CST816D  │  │  RTC    │   │
│    │ LCD驱动 │  │触摸驱动  │  │时钟驱动  │   │
│    └────┬────┘  └────┬────┘  └────┬────┘   │
│         │            │            │         │
├─────────┼────────────┼────────────┼─────────┤
│         ▼            ▼            ▼         │
│    ┌─────────────────────────────────────┐  │
│    │         STM32 HAL 库               │  │
│    │   SPI  │  I2C  │  GPIO  │  RTC     │  │
│    └─────────────────────────────────────┘  │
├─────────────────────────────────────────────┤
│              RTOS 层 (FreeRTOS)             │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│    │任务调度  │  │消息队列  │  │互斥信号量│   │
│    └─────────┘  └─────────┘  └─────────┘   │
├─────────────────────────────────────────────┤
│              硬件层 (STM32F401)             │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│    │  SPI1   │  │  I2C1   │  │  RTC    │   │
│    └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────┘
```

---

## ⚙️ 技术栈

| 类别 | 技术 |
|------|------|
| MCU | STM32F401 (ARM Cortex-M4) |
| RTOS | FreeRTOS |
| GUI 库 | LVGL 8.3.11 |
| 开发工具 | STM32CubeMX + Keil MDK-ARM |
| 通信协议 | SPI (LCD) + I2C (触摸) |
| 时钟系统 | RTC 实时时钟 (LSI 32KHz) |

---

## 📁 项目结构

```
401/
├── Core/
│   ├── Inc/                    # 头文件
│   │   ├── main.h             # 主程序头文件
│   │   ├── lcd_gc9a01.h       # LCD 驱动头文件
│   │   ├── cst816d.h          # 触摸驱动头文件
│   │   ├── rtc_time.h         # RTC 时间获取头文件
│   │   └── usart.h            # 串口头文件
│   │
│   └── Src/                    # 源文件
│       ├── main.c             # 主程序 & LVGL 界面逻辑
│       ├── lcd_gc9a01.c       # GC9A01 LCD 驱动实现
│       ├── cst816d.c          # CST816D 触摸驱动实现
│       ├── rtc_time.c         # RTC 时间获取函数
│       └── usart.c            # 串口通信
│
├── Drivers/                    # STM32 HAL 库
│   ├── CMSIS/                 # ARM CMSIS 核心头文件
│   └── STM32F4xx_HAL_Driver/  # STM32 HAL 驱动库
│
├── lvgl/                       # LVGL 图形库
│   ├── src/                   # LVGL 源码
│   ├── lv_conf.h              # LVGL 配置文件
│   └── lvgl.h                 # LVGL 主头文件
│
├── MDK-ARM/                    # Keil 工程文件
│   └── 401.uvprojx           # Keil 工程文件
│
├── 401.ioc                     # CubeMX 工程文件
├── README.md                   # 项目说明文档
└── .gitignore                  # Git 忽略文件配置
```

---

## 🎯 功能特性

### 1. 多任务实时调度

系统基于 FreeRTOS 实现多任务架构：

| 任务名称 | 功能 | 优先级 |
|---------|------|--------|
| HomeTask | 主表盘任务，显示 RTC 时间 | 正常 |
| TaskLvgl | LVGL 屏幕刷新任务 | 正常 |
| 软件定时器 | 周期获取 RTC 时间 | - |

### 2. 任务间通信

```
┌──────────────┐    消息队列    ┌──────────────┐
│  软件定时器   │ ───────────► │   HomeTask   │
│ (500ms周期)  │  RTC时间数据  │ (主表盘显示)  │
└──────────────┘              └──────────────┘
```

- **消息队列 (MessageQueue)**: 软件定时器获取 RTC 时间后，通过队列发送到 HomeTask
- **互斥信号量 (Mutex)**: 保护 LVGL 屏幕资源，避免多任务并发刷新冲突

### 3. LVGL 图形界面

#### 第一屏 - 欢迎页
- 显示 "Smart Watch" 欢迎文字
- 提示 "Swipe left" 左滑切换

#### 第二屏 - 功能页
- 设备信息显示 (LVGL 版本、MCU 型号、LCD 型号)
- RTC 实时时钟显示 (格式: HH:MM:SS)
- 交互按钮 (点击计数)
- 提示 "Swipe right" 右滑返回

### 4. 触摸手势交互

- **左滑**: 从欢迎页切换到功能页
- **右滑**: 从功能页返回欢迎页
- **按钮点击**: 计数器累加并显示

---

## 🔧 核心代码解析

### 1. 主表盘任务 (HomeTask)

```c
void StartHomeTask(void *argument)
{
    lv_obj_t * scr_home = lv_scr_act();
    lv_obj_t * clock_label = lv_label_create(scr_home);
    lv_obj_set_style_text_font(clock_label, &lv_font_montserrat_24, 0);
    lv_label_set_text_fmt(clock_label, "TIME");
    lv_obj_align(clock_label, LV_ALIGN_CENTER, 0, -20);

    char cnt[32];
    for (;;)
    {
        // 从消息队列获取 RTC 时间数据
        osMessageQueueGet(rtcTimerQueueHandle, &cnt, 0, osWaitForever);
        // 更新时间显示
        lv_label_set_text_fmt(clock_label, cnt);
        osDelay(50);
    }
}
```

### 2. 软件定时器回调 (RtcTimer)

```c
void RtcTimer(void *argument)
{
    RTC_TimeTypeDef sTime;
    HAL_RTC_GetTime(&hrtc, &sTime, RTC_FORMAT_BIN);
    HAL_RTC_GetDate(&hrtc, (RTC_DateTypeDef*)0, RTC_FORMAT_BIN);

    char cnt[17];
    sprintf(cnt, "RTC TIME %02d:%02d:%02d",
            sTime.Hours, sTime.Minutes, sTime.Seconds);

    // 发送时间数据到消息队列
    osMessageQueuePut(rtcTimerQueueHandle, &cnt, 0, osWaitForever);
}
```

### 3. 屏幕刷新任务 (TaskLvgl)

```c
void StartTaskLvgl(void *argument)
{
    for (;;)
    {
        // 获取互斥信号量，保护 LVGL 资源
        osMutexAcquire(lvgl_mutex, osWaitForever);
        lv_task_handler();  // 处理 LVGL 任务
        osMutexRelease(lvgl_mutex);
        osDelay(10);
    }
}
```

### 4. 手势处理

```c
void gesture_handler(lv_event_t * e)
{
    lv_obj_t * screen = lv_event_get_current_target(e);
    lv_dir_t dir = lv_indev_get_gesture_dir(lv_indev_get_act());

    switch(dir) {
        case LV_DIR_LEFT:
            // 左滑切换到下一屏
            if(screen == scr_home)
                lv_scr_load_anim(scr_sec, LV_SCR_LOAD_ANIM_MOVE_LEFT, 300, 0, false);
            break;
        case LV_DIR_RIGHT:
            // 右滑返回上一屏
            if(screen == scr_sec)
                lv_scr_load_anim(scr_home, LV_SCR_LOAD_ANIM_MOVE_RIGHT, 300, 0, false);
            break;
    }
}
```

---

## 📊 LVGL 配置优化

针对 STM32F401 的资源限制，对 LVGL 进行了精简配置：

| 配置项 | 值 | 说明 |
|-------|-----|------|
| `LV_COLOR_DEPTH` | 16 | 16位色深 |
| `LV_MEM_SIZE` | 10KB | 内存池大小 |
| `LV_USE_ANIMATION` | 0 | 关闭动画 |
| `LV_USE_LOG` | 0 | 关闭日志 |
| `LV_USE_GPU` | 0 | 关闭 GPU |
| `LV_USE_FILESYSTEM` | 0 | 关闭文件系统 |

启用的组件：
- `LV_USE_BTN` - 按钮
- `LV_USE_LABEL` - 标签
- `LV_USE_TOUCH` - 触摸
- `LV_USE_GESTURE` - 手势

---

## 🔌 硬件引脚连接

### SPI1 (LCD 通信)

| 引脚 | 功能 | 说明 |
|------|------|------|
| PA5 | SPI1_SCK | SPI 时钟 |
| PA7 | SPI1_MOSI | SPI 数据 |
| PB4 | LCD_CS | 片选 |
| PB2 | LCD_DC | 数据/命令 |
| PB1 | LCD_RST | 复位 |
| PB8 | LCD_BL | 背光 |

### I2C (触摸通信)

| 引脚 | 功能 | 说明 |
|------|------|------|
| PB6 | I2C_SCL | 软件 I2C 时钟 |
| PB7 | I2C_SDA | 软件 I2C 数据 |

### RTC

| 时钟源 | 频率 | 说明 |
|-------|------|------|
| LSI | 32 KHz | 内部低速时钟 |

---

## 🚀 快速开始

### 环境要求

- Keil MDK-ARM 5.x
- STM32CubeMX
- ST-Link 调试器

### 编译步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/jiuky1/smart-watch-stm32.git
   cd smart-watch-stm32
   ```

2. **打开工程**
   - 使用 Keil MDK-ARM 打开 `MDK-ARM/401.uvprojx`

3. **编译**
   - 点击 Keil 中的 "Build" 按钮

4. **烧录**
   - 连接 ST-Link
   - 点击 "Download" 烧录到开发板

### CubeMX 配置

如需修改硬件配置，可打开 `401.ioc` 文件：

```bash
# 使用 CubeMX 打开
stm32cubemx 401.ioc
```

---

## 📈 系统性能

| 指标 | 值 |
|------|-----|
| 主频 | 84 MHz |
| RAM 使用 | ~30 KB |
| Flash 使用 | ~128 KB |
| LVGL 刷新率 | ~30 FPS |
| 任务切换周期 | 1 ms |

---

## 🔍 调试说明

### 串口调试

- **USART2**: 115200-8N1 (ST-Link 调试串口)
- **USART6**: 115200-8N1 (扩展串口)

### 调试输出

在 `main.c` 中使用 `debug_buf` 缓冲区输出调试信息：

```c
char debug_buf[128];
sprintf(debug_buf, "Touch: x=%d, y=%d\r\n", touch_data.x, touch_data.y);
HAL_UART_Transmit(&huart2, (uint8_t*)debug_buf, strlen(debug_buf), HAL_MAX_DELAY);
```

---

## 🐛 常见问题

### Q: LCD 屏幕不亮
**A:** 检查以下几点：
- 确认 PB8 (背光引脚) 已置高
- 检查 SPI 接线是否正确
- 确认 LCD 供电正常

### Q: 触摸无响应
**A:** 检查以下几点：
- 确认 I2C 地址正确 (0x15)
- 检查 PB6/PB7 接线
- 确认触摸芯片供电正常

### Q: 时间显示不更新
**A:** 检查以下几点：
- 确认 RTC 已初始化
- 检查 LSI 时钟是否正常
- 确认软件定时器已启动

---

## 📝 更新日志

### v1.0.0 (2026-06-14)
- 初始版本发布
- 实现基础 GUI 界面
- 支持 RTC 时间显示
- 支持触摸手势交互

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👨‍💻 作者

**鲁江龙** - [GitHub](https://github.com/jiuky1)

---

## 🙏 致谢

- [LVGL](https://lvgl.io/) - 嵌入式图形库
- [STM32CubeMX](https://www.st.com/en/development-tools/stm32cubemx.html) - STM32 配置工具
- [FreeRTOS](https://www.freertos.org/) - 实时操作系统

---

## 📞 联系方式

- Email: lelaj666@gmail.com
- GitHub: [lelaj666](https://github.com/jiuky1)
