/*
 * redirectprintf.c
 *
 *  Created on: 2026年4月17日
 *      Author: Administrator
 */

#include "stdio.h"
#include "string.h"
#include "stm32f4xx_hal.h"

extern UART_HandleTypeDef huart6;


char* ESP_SendCmd(uint8_t *cmd, uint16_t timeout);


/*
#if defined(__ICCARM__) || defined(__CC_ARM) || defined(__GNUC__)
  //With GCC, small printf (option LD Linker->Libraries->Small printf set to 'Yes') calls __io_putchar()
  #define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
  PUTCHAR_PROTOTYPE
  {
    HAL_UART_Transmit(&huart2, (uint8_t *)&ch, 1, 0xFFFF);//用作wifi通信
    return ch;
  }

  int _write(int file, char *ptr, int len) {
    int DataIdx;
    for (DataIdx = 0; DataIdx < len; DataIdx++) {
    	__io_putchar(*ptr++);
    }
    return len;
  }

#else
  #define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)
#endif
*/


  /*
  #define  configDebugPrintf   1
  #if   (1 == configDebugPrintf)
      //#define  Debug_printf(fmt,args...)   printf(fmt"----[file name = %s  line num = %d]"" ",__FILE__,__LINE__,##args)
  	#define  Debug_printf(fmt,args...)   printf(fmt"""",##args)
  #else
      #define  Debug_printf(fmt,args...)
  #endif
  */
#define RX_BUF_SIZE 512
uint8_t rx_buf[RX_BUF_SIZE];
uint8_t rx_byte;
uint16_t rx_cnt = 0;
volatile uint8_t rx_callback_flag = 0;
volatile uint8_t rx_error_flag = 0;
// WiFi 状态
uint8_t wifi_connected = 0;
char ip_addr[32] = {0};
char rssi[16] = {0};
char wifi_name[32] = {0};

void ESP_CheckWiFiStatus(void)
{
    char *p;

    // 1. 查询 WiFi 连接状态
    char *resp = ESP_SendCmd("BT+CWJAP?\r\n", (uint16_t)1000);

    // 判断是否连接
    if(strstr(resp, "No AP") != NULL)
    {
        wifi_connected = 0;
        ip_addr[0] = 0;
        rssi[0] = 0;
        return;
    }

    if(strstr(resp, "WIFI GOT IP") != NULL || strstr(resp, "+CWJAP:") != NULL)
    {
        wifi_connected = 1;
    }

    // 2. 获取 IP 地址
    resp = ESP_SendCmd("AT+CIFSR\r\n", 1000);
    if((p = strstr(resp, "STAIP")) != NULL)
    {
        sscanf(p + 7, "%[^\"]", ip_addr);
    }

    // 3. 获取信号强度 RSSI
    resp = ESP_SendCmd("AT+CWJAP?\r\n", 1000);
    if((p = strstr(resp, "+CWJAP:")) != NULL)
    {
        int comma_cnt = 0;
        while(*p != '\0' && comma_cnt < 3)
        {
            if(*p == ',') comma_cnt++;
            p++;
        }
        if(comma_cnt == 3)
        {
            int i = 0;
            while(*p != '\0' && *p != '\r' && *p != '\n' && i < 15)
            {
                rssi[i++] = *p++;
            }
            rssi[i] = '\0';
        }
    }
}

void initUsart(void){
	HAL_StatusTypeDef status = HAL_UART_Receive_IT(&huart6, &rx_byte, 1);
	if(status != HAL_OK)
	{
		rx_error_flag = 1;
	}
}

char* ESP_SendCmd(uint8_t *cmd, uint16_t timeout)
{
    uint32_t start_tick = HAL_GetTick();

    memset(rx_buf, 0, RX_BUF_SIZE);
    rx_cnt = 0;

    HAL_UART_Transmit(&huart6, cmd, strlen((char*)cmd), 100);

    while((HAL_GetTick() - start_tick) < timeout)
    {
        if(rx_cnt > 0)
        {
            if(strstr((char*)rx_buf, "OK") != NULL) break;
            if(strstr((char*)rx_buf, "ERROR") != NULL) break;
            if(strstr((char*)rx_buf, "ready") != NULL) break;
            if(strstr((char*)rx_buf, "WIFI GOT IP") != NULL) break;
            if(strstr((char*)rx_buf, "No AP") != NULL) break;
        }
    }

    rx_buf[rx_cnt] = '\0';

    return (char*)rx_buf;
}

void ESP_Init(void)
{
    char* resp = ESP_SendCmd((uint8_t*)"AT\r\n", 1000);
    //resp = ESP_SendCmd((uint8_t*)"AT+CWJAP=\"HUAWEI-E105YI\",\"ganxinyu32701\"\r\n", 5000);
    while(1){
    	resp = ESP_SendCmd((uint8_t*)"AT+CWQAP\r\n", 5000);
    	printf("12232");
    	resp = ESP_SendCmd((uint8_t*)"AT+CWJAP=\"2NF\",\"3010800249\"\r\n", 5000);
    	printf("12232");
    }
    /*resp = ESP_SendCmd((uint8_t*)"AT+GMR\r\n", 500);
    ESP_SendCmd((uint8_t*)"ATE0\r\n", 500);
    ESP_SendCmd((uint8_t*)"AT+CWMODE=1\r\n", 1000);

    resp = ESP_SendCmd((uint8_t*)"AT+CWJAP=\"HUAWEI-E105YI\",\"ganxinyu32701\"\r\n", 5000);
    if(strstr(resp, "OK") != NULL || strstr(resp, "GOT IP") != NULL)
    {
        wifi_connected = 1;
    }
    else
    {
        wifi_connected = 0;
    }
    ESP_CheckWiFiStatus();*/
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART2)
    {
        rx_callback_flag = 1;
        if(rx_cnt < RX_BUF_SIZE - 1)
        {
            rx_buf[rx_cnt++] = rx_byte;
        }
        else
        {
            rx_buf[RX_BUF_SIZE - 1] = '\0';
        }
        HAL_StatusTypeDef status = HAL_UART_Receive_IT(&huart6, &rx_byte, 1);
        if(status != HAL_OK)
        {
            rx_error_flag = 2;
        }
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART2)
    {
        rx_error_flag = 3;
        HAL_UART_Receive_IT(&huart6, &rx_byte, 1);
    }
}

/*void USART2_IRQHandler(void) {
	if (UART_GetITStatus(USART2, UART_IT_RXNE) != RESET) {
		char data = USART_ReceiveData(USART2);
		// 处理接收到的数据
	}
}*/
