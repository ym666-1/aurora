#include "cst816d.h"

#define CST816D_SDA_PIN   GPIO_PIN_7
#define CST816D_SDA_PORT  GPIOB
#define CST816D_SCL_PIN   GPIO_PIN_6
#define CST816D_SCL_PORT  GPIOB
#define CST816D_RST_PIN   GPIO_PIN_9
#define CST816D_RST_PORT  GPIOB
#define CST816D_INT_PIN   GPIO_PIN_10
#define CST816D_INT_PORT  GPIOB

#define CST816D_SDA_H()   HAL_GPIO_WritePin(CST816D_SDA_PORT, CST816D_SDA_PIN, GPIO_PIN_SET)
#define CST816D_SDA_L()   HAL_GPIO_WritePin(CST816D_SDA_PORT, CST816D_SDA_PIN, GPIO_PIN_RESET)
#define CST816D_SCL_H()   HAL_GPIO_WritePin(CST816D_SCL_PORT, CST816D_SCL_PIN, GPIO_PIN_SET)
#define CST816D_SCL_L()   HAL_GPIO_WritePin(CST816D_SCL_PORT, CST816D_SCL_PIN, GPIO_PIN_RESET)
#define CST816D_RST_H()   HAL_GPIO_WritePin(CST816D_RST_PORT, CST816D_RST_PIN, GPIO_PIN_SET)
#define CST816D_RST_L()   HAL_GPIO_WritePin(CST816D_RST_PORT, CST816D_RST_PIN, GPIO_PIN_RESET)
#define CST816D_INT_READ() HAL_GPIO_ReadPin(CST816D_INT_PORT, CST816D_INT_PIN)

#define CST816D_SDA_READ() HAL_GPIO_ReadPin(CST816D_SDA_PORT, CST816D_SDA_PIN)

static void CST816D_SDA_OUT(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = CST816D_SDA_PIN;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(CST816D_SDA_PORT, &GPIO_InitStruct);
}

static void CST816D_SDA_IN(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = CST816D_SDA_PIN;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(CST816D_SDA_PORT, &GPIO_InitStruct);
}

static void CST816D_I2C_Start(void)
{
    CST816D_SDA_OUT();
    CST816D_SDA_H();
    CST816D_SCL_H();
    HAL_Delay(1);
    CST816D_SDA_L();
    HAL_Delay(1);
    CST816D_SCL_L();
}

static void CST816D_I2C_Stop(void)
{
    CST816D_SDA_OUT();
    CST816D_SCL_L();
    CST816D_SDA_L();
    HAL_Delay(1);
    CST816D_SCL_H();
    HAL_Delay(1);
    CST816D_SDA_H();
    HAL_Delay(1);
}

static void CST816D_I2C_SendByte(uint8_t data)
{
    CST816D_SDA_OUT();
    CST816D_SCL_L();
    for(uint8_t i = 0; i < 8; i++)
    {
        if(data & 0x80)
            CST816D_SDA_H();
        else
            CST816D_SDA_L();
        data <<= 1;
        HAL_Delay(1);
        CST816D_SCL_H();
        HAL_Delay(1);
        CST816D_SCL_L();
        HAL_Delay(1);
    }
}

static uint8_t CST816D_I2C_ReadByte(void)
{
    uint8_t data = 0;
    CST816D_SDA_IN();
    for(uint8_t i = 0; i < 8; i++)
    {
        CST816D_SCL_L();
        HAL_Delay(1);
        CST816D_SCL_H();
        HAL_Delay(1);
        data <<= 1;
        if(CST816D_SDA_READ())
            data |= 0x01;
    }
    CST816D_SCL_L();
    return data;
}

static uint8_t CST816D_I2C_WaitAck(void)
{
    uint8_t ack;
    CST816D_SDA_IN();
    CST816D_SCL_L();
    HAL_Delay(1);
    CST816D_SCL_H();
    HAL_Delay(1);
    ack = CST816D_SDA_READ() ? 1 : 0;
    CST816D_SCL_L();
    HAL_Delay(1);
    return ack;
}

static void CST816D_I2C_SendAck(void)
{
    CST816D_SDA_OUT();
    CST816D_SDA_L();
    CST816D_SCL_L();
    HAL_Delay(1);
    CST816D_SCL_H();
    HAL_Delay(1);
    CST816D_SCL_L();
}

static void CST816D_I2C_SendNack(void)
{
    CST816D_SDA_OUT();
    CST816D_SDA_H();
    CST816D_SCL_L();
    HAL_Delay(1);
    CST816D_SCL_H();
    HAL_Delay(1);
    CST816D_SCL_L();
}

static uint8_t CST816D_WriteReg(uint8_t reg, uint8_t data)
{
    CST816D_I2C_Start();
    CST816D_I2C_SendByte((CST816D_ADDR << 1) | 0x00);
    if(CST816D_I2C_WaitAck()) return 1;
    CST816D_I2C_SendByte(reg);
    if(CST816D_I2C_WaitAck()) return 1;
    CST816D_I2C_SendByte(data);
    if(CST816D_I2C_WaitAck()) return 1;
    CST816D_I2C_Stop();
    return 0;
}

static uint8_t CST816D_ReadReg(uint8_t reg)
{
    uint8_t data;
    CST816D_I2C_Start();
    CST816D_I2C_SendByte((CST816D_ADDR << 1) | 0x00);
    CST816D_I2C_WaitAck();
    CST816D_I2C_SendByte(reg);
    CST816D_I2C_WaitAck();
    CST816D_I2C_Start();
    CST816D_I2C_SendByte((CST816D_ADDR << 1) | 0x01);
    CST816D_I2C_WaitAck();
    data = CST816D_I2C_ReadByte();
    CST816D_I2C_SendNack();
    CST816D_I2C_Stop();
    return data;
}

static void CST816D_ReadMultiReg(uint8_t reg, uint8_t *buf, uint8_t len)
{
    CST816D_I2C_Start();
    CST816D_I2C_SendByte((CST816D_ADDR << 1) | 0x00);
    CST816D_I2C_WaitAck();
    CST816D_I2C_SendByte(reg);
    CST816D_I2C_WaitAck();
    CST816D_I2C_Start();
    CST816D_I2C_SendByte((CST816D_ADDR << 1) | 0x01);
    CST816D_I2C_WaitAck();
    for(uint8_t i = 0; i < len - 1; i++)
    {
        buf[i] = CST816D_I2C_ReadByte();
        CST816D_I2C_SendAck();
    }
    buf[len - 1] = CST816D_I2C_ReadByte();
    CST816D_I2C_SendNack();
    CST816D_I2C_Stop();
}

static void CST816D_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;

    GPIO_InitStruct.Pin = CST816D_SCL_PIN;
    HAL_GPIO_Init(CST816D_SCL_PORT, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = CST816D_SDA_PIN;
    HAL_GPIO_Init(CST816D_SDA_PORT, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = CST816D_RST_PIN;
    HAL_GPIO_Init(CST816D_RST_PORT, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = CST816D_INT_PIN;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(CST816D_INT_PORT, &GPIO_InitStruct);

    CST816D_SCL_H();
    CST816D_SDA_H();
    CST816D_RST_H();
}

uint8_t CST816D_Init(void)
{
    CST816D_GPIO_Init();

    HAL_Delay(100);

    CST816D_RST_L();
    HAL_Delay(50);
    CST816D_RST_H();
    HAL_Delay(100);

    uint8_t chip_id = CST816D_ReadReg(0xA7);
    if(chip_id == 0x00 || chip_id == 0xFF)
    {
        return 1;
    }

    CST816D_WriteReg(0xFE, 0x00);
    HAL_Delay(5);

    CST816D_WriteReg(0xFA, 0x20);
    CST816D_WriteReg(0xFB, 0x00);
    CST816D_WriteReg(0xFC, 0x00);
    CST816D_WriteReg(0xFD, 0x00);
    CST816D_WriteReg(0xFE, 0x5A);

    CST816D_WriteReg(0xE4, 0x01);
    CST816D_WriteReg(0xE5, 0x01);
    CST816D_WriteReg(0xE6, 0x01);
    CST816D_WriteReg(0xE7, 0x01);

    CST816D_WriteReg(0xE0, 0x01);
    CST816D_WriteReg(0xE1, 0x01);
    CST816D_WriteReg(0xE2, 0x01);
    CST816D_WriteReg(0xE3, 0x01);

    CST816D_WriteReg(0xEC, 0x01);
    CST816D_WriteReg(0xED, 0x01);
    CST816D_WriteReg(0xEE, 0x01);
    CST816D_WriteReg(0xEF, 0x01);

    CST816D_WriteReg(0xFE, 0x01);

    return 0;
}

uint8_t CST816D_ReadTouch(CST816D_Touch_t *touch)
{
    uint8_t buf[6];

    CST816D_ReadMultiReg(0x01, buf, 6);

    touch->gesture = buf[0];
    touch->touch_point = buf[1];
    touch->x = ((uint16_t)(buf[2] & 0x0F) << 8) | buf[3];
    touch->y = ((uint16_t)(buf[4] & 0x0F) << 8) | buf[5];
    touch->pressed = (touch->touch_point > 0) ? 1 : 0;

    return touch->pressed;
}

uint8_t CST816D_GetGesture(void)
{
    return CST816D_ReadReg(0x01);
}

void CST816D_GetXY(uint16_t *x, uint16_t *y)
{
    uint8_t buf[4];
    CST816D_ReadMultiReg(0x03, buf, 4);
    *x = ((uint16_t)(buf[0] & 0x0F) << 8) | buf[1];
    *y = ((uint16_t)(buf[2] & 0x0F) << 8) | buf[3];
}

uint8_t CST816D_IsPressed(void)
{
    uint8_t touch_point = CST816D_ReadReg(0x02);
    return (touch_point > 0) ? 1 : 0;
}
