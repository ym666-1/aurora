/*
 * rtc_time.c
 *
 *  Created on: 2026年4月25日
 *      Author: Administrator
 */
#include "main.h"
#include "rtc_time.h"
extern RTC_HandleTypeDef hrtc;

void RTC_Get_CurrentTime(uint8_t *hour, uint8_t *min, uint8_t *sec)
{
    RTC_TimeTypeDef sTime;
    HAL_RTC_GetTime(&hrtc, &sTime, RTC_FORMAT_BIN);
    HAL_RTC_GetDate(&hrtc, (RTC_DateTypeDef*)0, RTC_FORMAT_BIN); // 必须读，否则时间不更新

    *hour = sTime.Hours;
    *min  = sTime.Minutes;
    *sec  = sTime.Seconds;
}

