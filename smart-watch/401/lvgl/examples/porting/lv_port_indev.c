/**
 * @file lv_port_indev.c
 * @brief LVGL 输入设备移植层 - 仅保留触摸屏
 */

#if 1

#include "lv_port_indev.h"
#include "../../lvgl.h"
#include "cst816d.h"
#include "main.h"
#include <stdio.h>

extern UART_HandleTypeDef huart2;   /* 调试串口 */

/* 触摸输入设备全局句柄 */
lv_indev_t * indev_touchpad;

/* 触摸读取回调：由 LVGL 每帧调用 */
static void touchpad_read(lv_indev_drv_t * indev_drv, lv_indev_data_t * data)
{
    static lv_coord_t last_x = 0;
    static lv_coord_t last_y = 0;
    static uint32_t dbg_cnt = 0;    /* 调试计数器：每 100 次打印一次 */

    CST816D_Touch_t touch_data;
    if(CST816D_ReadTouch(&touch_data))
    {
        last_x = touch_data.x;
        last_y = touch_data.y;
        data->point.x = last_x;
        data->point.y = last_y;
        data->state = LV_INDEV_STATE_PR;

        /* 调试：触摸时 LED 亮起 */
        HAL_GPIO_WritePin(L1_GPIO_Port, L1_Pin, GPIO_PIN_SET);

        /* 调试：每 50 次读取打印一次坐标到 UART */
        if(++dbg_cnt % 50 == 0)
        {
            char buf[64];
            int len = sprintf(buf, "TOUCH: x=%d y=%d g=%d\r\n",
                              touch_data.x, touch_data.y, touch_data.gesture);
            HAL_UART_Transmit(&huart2, (uint8_t*)buf, len, 100);
        }
    }
    else
    {
        data->point.x = last_x;
        data->point.y = last_y;
        data->state = LV_INDEV_STATE_REL;

        /* 调试：释放时 LED 熄灭 */
        HAL_GPIO_WritePin(L1_GPIO_Port, L1_Pin, GPIO_PIN_RESET);
    }
}

/* 输入设备初始化：仅注册触摸屏 */
void lv_port_indev_init(void)
{
    static lv_indev_drv_t indev_drv;

    lv_indev_drv_init(&indev_drv);
    indev_drv.type = LV_INDEV_TYPE_POINTER;  /* 指针类设备（触摸） */
    indev_drv.read_cb = touchpad_read;
    indev_touchpad = lv_indev_drv_register(&indev_drv);
}

#else
typedef int keep_pedantic_happy;
#endif
