#ifndef __CST816D_H
#define __CST816D_H

#include "stm32f4xx_hal.h"

#define CST816D_ADDR        0x15

#define CST816D_GESTURE_NONE        0x00
#define CST816D_GESTURE_SWIPE_UP    0x01
#define CST816D_GESTURE_SWIPE_DOWN  0x02
#define CST816D_GESTURE_SWIPE_LEFT  0x03
#define CST816D_GESTURE_SWIPE_RIGHT 0x04
#define CST816D_GESTURE_SINGLE_CLICK 0x05
#define CST816D_GESTURE_DOUBLE_CLICK 0x0B
#define CST816D_GESTURE_LONG_PRESS  0x0C

typedef struct {
    uint8_t gesture;
    uint8_t touch_point;
    uint16_t x;
    uint16_t y;
    uint8_t pressed;
} CST816D_Touch_t;

uint8_t CST816D_Init(void);
uint8_t CST816D_ReadTouch(CST816D_Touch_t *touch);
uint8_t CST816D_GetGesture(void);
void CST816D_GetXY(uint16_t *x, uint16_t *y);
uint8_t CST816D_IsPressed(void);

#endif
