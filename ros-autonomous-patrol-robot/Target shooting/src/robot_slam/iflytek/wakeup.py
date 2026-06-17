#!/usr/bin/env python
'''
讯飞语音唤醒模块
'''
import threading
import time
from iflytek_sdk import WakeupSDK  # 假设讯飞提供了Python SDK

class Wakeup:
    def __init__(self, appid):
        self.appid = appid
        self.sdk = WakeupSDK(appid=self.appid)
        self.callback = None
        self._running = False
        self.thread = None

    def set_callback(self, callback):
        """设置唤醒回调函数"""
        self.callback = callback

    def start(self):
        """启动语音唤醒"""
        self._running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        """内部运行函数"""
        self.sdk.start()
        while self._running:
            if self.sdk.check_wakeup():  # 检测是否唤醒
                if self.callback is not None:
                    self.callback()
            time.sleep(0.01)

    def stop(self):
        """停止语音唤醒"""
        self._running = False
        if self.thread is not None:
            self.thread.join()
        self.sdk.stop()
