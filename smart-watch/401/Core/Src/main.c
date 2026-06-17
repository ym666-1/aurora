/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body - 裸机智能手表主程序
  * @description    : 基于 STM32F401 + GC9A01 LCD + LVGL 的嵌入式 GUI
  *                   主要功能：触摸控制、RTC 实时时钟显示、LVGL 图形界面
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "lcd_gc9a01.h"
#include "cst816d.h"
#include <stdio.h>
#include <string.h>
#include "lvgl.h"
#include "lv_port_disp.h"
#include "lv_port_indev.h"
#include "rtc_time.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
RTC_HandleTypeDef hrtc;

SPI_HandleTypeDef hspi1;

UART_HandleTypeDef huart2;
UART_HandleTypeDef huart6;

/* USER CODE BEGIN PV */
CST816D_Touch_t touch_data;      /* 触摸数据结构体 */
uint8_t touch_initialized = 0;   /* 触摸初始化标志：1=成功，0=失败 */
char debug_buf[128];              /* 调试缓冲区 */
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_USART6_UART_Init(void);
static void MX_SPI1_Init(void);
static void MX_RTC_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* ---- LVGL 全局对象 ---- */
lv_obj_t *scr_home;           /* 主页面 */
lv_obj_t *scr_sec;            /* 第二个页面 */
lv_obj_t *time_label;         /* RTC 时间标签 */

/**
  * @brief  按钮点击事件回调
  * @note   每次点击按钮，计数加1并更新标签文本
  */
static void btn_event_cb(lv_event_t * e)
{
    lv_event_code_t code = lv_event_get_code(e);
    lv_obj_t * btn = lv_event_get_target(e);
    if(code == LV_EVENT_CLICKED) {
        static uint8_t cnt = 0;
        cnt++;
        lv_obj_t * label = lv_obj_get_child(btn, 0);
        lv_label_set_text_fmt(label, "Button: %d", cnt);
    }
}

/**
  * @brief  手势滑动处理
  * @note   左右滑动在两个页面之间切换（带动画）
  */
void gesture_handler(lv_event_t * e)
{
    lv_obj_t * screen = lv_event_get_current_target(e);
    lv_dir_t dir = lv_indev_get_gesture_dir(lv_indev_get_act());
    switch(dir) {
        case LV_DIR_LEFT:
            if(screen == scr_home)
                lv_scr_load_anim(scr_sec, LV_SCR_LOAD_ANIM_MOVE_LEFT, 300, 0, false);
            else if(screen == scr_sec)
                lv_scr_load_anim(scr_home, LV_SCR_LOAD_ANIM_MOVE_LEFT, 300, 0, false);
            break;
        case LV_DIR_RIGHT:
            if(screen == scr_home)
                lv_scr_load_anim(scr_sec, LV_SCR_LOAD_ANIM_MOVE_RIGHT, 300, 0, false);
            else if(screen == scr_sec)
                lv_scr_load_anim(scr_home, LV_SCR_LOAD_ANIM_MOVE_RIGHT, 300, 0, false);
            break;
        default:
            break;
    }
}

/* USER CODE END 0 */

/**
  * @brief  应用程序入口
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  /* USER CODE END 1 */

  /* MCU 初始化 */
  HAL_Init();
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
  /* USER CODE END SysInit */

  /* 初始化外设（注意：I2C1 已移除，PB6/PB7 由 CST816D 软件 I2C 独占） */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  MX_USART6_UART_Init();
  MX_SPI1_Init();
  MX_RTC_Init();

  /* USER CODE BEGIN 2 */

  /* ---- LCD 背光使能 ---- */
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_8, GPIO_PIN_SET);

  /* ---- 初始化触摸芯片 ---- */
  if(CST816D_Init() == 0)
  {
      touch_initialized = 1;
      /* 触摸初始化成功：LED 闪烁 3 次 */
      for(int i = 0; i < 3; i++)
      {
          HAL_GPIO_WritePin(L1_GPIO_Port, L1_Pin, GPIO_PIN_SET);
          HAL_Delay(100);
          HAL_GPIO_WritePin(L1_GPIO_Port, L1_Pin, GPIO_PIN_RESET);
          HAL_Delay(100);
      }
  }
  else
  {
      touch_initialized = 0;
      /* 触摸初始化失败：LED 常亮 */
      HAL_GPIO_WritePin(L1_GPIO_Port, L1_Pin, GPIO_PIN_SET);
  }

  /* ---- LVGL 初始化 ---- */
  lv_init();
  lv_port_disp_init();
  lv_port_indev_init();

  /* ---- 创建第一屏（简洁首页，仅显示欢迎文字） ---- */
  scr_home = lv_scr_act();

  lv_obj_t *welcome_label = lv_label_create(scr_home);
  lv_label_set_text(welcome_label, "Smart Watch");
  lv_obj_align(welcome_label, LV_ALIGN_CENTER, 0, -20);
  lv_obj_set_style_text_font(welcome_label, &lv_font_montserrat_20, 0);

  lv_obj_t *hint_label = lv_label_create(scr_home);
  lv_label_set_text(hint_label, "Swipe left");
  lv_obj_align(hint_label, LV_ALIGN_CENTER, 0, 20);

  /* ---- 创建第二屏（功能页：设备信息 + 时钟 + 按钮） ---- */
  scr_sec = lv_obj_create(NULL);

  /* 设备信息 */
  lv_obj_t *info_label = lv_label_create(scr_sec);
  lv_label_set_text(info_label, "LVGL 8.3.11\nSTM32F401\nGC9A01 LCD");
  lv_obj_align(info_label, LV_ALIGN_TOP_MID, 0, 15);

  /* RTC 时间标签 */
  time_label = lv_label_create(scr_sec);
  lv_label_set_text(time_label, "RTC TIME\n--:--:--");
  lv_obj_align(time_label, LV_ALIGN_CENTER, 0, -20);
  lv_obj_set_style_text_font(time_label, &lv_font_montserrat_20, 0);

  /* 按钮 */
  lv_obj_t * btn = lv_btn_create(scr_sec);
  lv_obj_set_size(btn, 120, 50);
  lv_obj_align(btn, LV_ALIGN_CENTER, 0, 40);
  lv_obj_add_event_cb(btn, btn_event_cb, LV_EVENT_ALL, NULL);

  lv_obj_t * btn_label = lv_label_create(btn);
  lv_label_set_text(btn_label, "Click Me");
  lv_obj_center(btn_label);

  /* 返回提示 */
  lv_obj_t *back_hint = lv_label_create(scr_sec);
  lv_label_set_text(back_hint, "Swipe right");
  lv_obj_align(back_hint, LV_ALIGN_BOTTOM_MID, 0, -10);

  /* 注册手势事件 */
  lv_obj_add_event_cb(scr_home, gesture_handler, LV_EVENT_GESTURE, NULL);
  lv_obj_add_event_cb(scr_sec, gesture_handler, LV_EVENT_GESTURE, NULL);

  /* RTC 时间变量 */
  uint8_t hour = 0, min = 0, sec = 0;
  uint32_t last_time_update = 0;

  /* USER CODE END 2 */

  /* 主循环 */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
      /* 每 100ms 更新一次 RTC 时间显示（仅在第二屏时更新） */
      if(HAL_GetTick() - last_time_update > 100)
      {
          if(lv_scr_act() == scr_sec)
          {
              RTC_Get_CurrentTime(&hour, &min, &sec);
              lv_label_set_text_fmt(time_label, "RTC TIME\n%02d:%02d:%02d", hour, min, sec);
          }
          last_time_update = HAL_GetTick();
      }

      /* LVGL 任务处理 */
      lv_task_handler();

      /* 延时 10ms */
      HAL_Delay(10);
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief  系统时钟配置：HSI 16MHz，LSI 供 RTC
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE2);

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_LSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.LSIState = RCC_LSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) Error_Handler();

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK) Error_Handler();
}

/**
  * @brief  RTC 初始化：24小时制，LSI 时钟
  */
static void MX_RTC_Init(void)
{
  hrtc.Instance = RTC;
  hrtc.Init.HourFormat = RTC_HOURFORMAT_24;
  hrtc.Init.AsynchPrediv = 127;
  hrtc.Init.SynchPrediv = 255;
  hrtc.Init.OutPut = RTC_OUTPUT_DISABLE;
  hrtc.Init.OutPutPolarity = RTC_OUTPUT_POLARITY_HIGH;
  hrtc.Init.OutPutType = RTC_OUTPUT_TYPE_OPENDRAIN;
  if (HAL_RTC_Init(&hrtc) != HAL_OK) Error_Handler();
}

/**
  * @brief  SPI1 初始化：主模式，8位，最高波特率（LCD 通信）
  */
static void MX_SPI1_Init(void)
{
  hspi1.Instance = SPI1;
  hspi1.Init.Mode = SPI_MODE_MASTER;
  hspi1.Init.Direction = SPI_DIRECTION_2LINES;
  hspi1.Init.DataSize = SPI_DATASIZE_8BIT;
  hspi1.Init.CLKPolarity = SPI_POLARITY_LOW;
  hspi1.Init.CLKPhase = SPI_PHASE_1EDGE;
  hspi1.Init.NSS = SPI_NSS_SOFT;
  hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_2;
  hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
  hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
  hspi1.Init.CRCPolynomial = 10;
  if (HAL_SPI_Init(&hspi1) != HAL_OK) Error_Handler();
}

/**
  * @brief  USART2 初始化：115200-8N1（ST-Link 调试串口）
  */
static void MX_USART2_UART_Init(void)
{
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK) Error_Handler();
}

/**
  * @brief  USART6 初始化：115200-8N1（扩展串口）
  */
static void MX_USART6_UART_Init(void)
{
  huart6.Instance = USART6;
  huart6.Init.BaudRate = 115200;
  huart6.Init.WordLength = UART_WORDLENGTH_8B;
  huart6.Init.StopBits = UART_STOPBITS_1;
  huart6.Init.Parity = UART_PARITY_NONE;
  huart6.Init.Mode = UART_MODE_TX_RX;
  huart6.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart6.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart6) != HAL_OK) Error_Handler();
}

/**
  * @brief  GPIO 初始化：LED(L1)、背光、LCD 控制引脚
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();

  HAL_GPIO_WritePin(L1_GPIO_Port, L1_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_10|GPIO_PIN_4
                          |GPIO_PIN_8|GPIO_PIN_9, GPIO_PIN_RESET);

  /* LED (L1) */
  GPIO_InitStruct.Pin = L1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(L1_GPIO_Port, &GPIO_InitStruct);

  /* 背光/LCD 控制 (PB1/2/4/8/9/10) */
  GPIO_InitStruct.Pin = GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_10|GPIO_PIN_4
                          |GPIO_PIN_8|GPIO_PIN_9;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  if (htim->Instance == TIM1)
  {
    HAL_IncTick();
  }
}

void Error_Handler(void)
{
  __disable_irq();
  while (1) {}
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
}
#endif
