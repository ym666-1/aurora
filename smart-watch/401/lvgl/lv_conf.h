#ifndef LV_CONF_H
#define LV_CONF_H

#if 1  // 必须开启

// ==================== 核心设置 ====================
#define LV_COLOR_DEPTH          16
#define LV_COLOR_16_SWAP        1
#define LV_DPI                  96

#define LV_TICK_CUSTOM          1
#define LV_TICK_CUSTOM_INCLUDE  "stm32f4xx_hal.h"
#define LV_TICK_CUSTOM_SYS_TIME_EXPR (HAL_GetTick())

// ==================== 【关键】内存开到最小 ====================
#define LV_MEM_SIZE             (1024 * 10)   // 👈 10KB RAM！绝对不爆

// ==================== 关闭所有能关的 ====================
#define LV_USE_DISP              1
#define LV_USE_OBJ               1
#define LV_USE_LABEL             1
#define LV_USE_ANIMATION         0
#define LV_USE_LOG               0
#define LV_USE_DEBUG             0
#define LV_USE_INDEV             1
#define LV_USE_TOUCH             1
#define LV_USE_GESTURE           1
#define LV_USE_GPU               0
#define LV_USE_FILESYSTEM        0
#define LV_USE_PERF_MONITOR      0
#define LV_USE_MEM_MONITOR       0
#define LV_USE_BAR               0
#define LV_USE_BTN               1
#define LV_USE_GROUP             0
#define LV_USE_SLIDER            0

// ==================== 字体只留最小 ====================
#define LV_FONT_MONTSERRAT_8  1
#define LV_FONT_MONTSERRAT_10 1
#define LV_FONT_MONTSERRAT_12 1
#define LV_FONT_MONTSERRAT_14 1
#define LV_FONT_MONTSERRAT_16 1
#define LV_FONT_MONTSERRAT_18 1
#define LV_FONT_MONTSERRAT_20 1
#define LV_FONT_MONTSERRAT_22 1
#define LV_FONT_MONTSERRAT_24 1
#define LV_FONT_MONTSERRAT_26 1
#define LV_FONT_MONTSERRAT_28 1
#define LV_FONT_MONTSERRAT_30 1
#define LV_FONT_MONTSERRAT_32 1
#define LV_FONT_MONTSERRAT_34 1
#define LV_FONT_MONTSERRAT_36 1
#define LV_FONT_MONTSERRAT_38 1
#define LV_FONT_MONTSERRAT_40 1
#define LV_FONT_MONTSERRAT_42 1
#define LV_FONT_MONTSERRAT_44 1
#define LV_FONT_MONTSERRAT_46 1
#define LV_FONT_MONTSERRAT_48 1
#define LV_FONT_DEFAULT          &lv_font_montserrat_24

#endif

#endif
