#!/home/abot/anaconda3/envs/vlm/bin/python
# -*- coding: utf-8 -*-

class GlobalState:
    def __init__(self):
        self.topic_info = ""

    def set_topic_info(self, info):
        self.topic_info = info
        print(f"Topic info set to: {self.topic_info}")  # 添加调试信息

    def get_topic_info(self):
        print(f"Returning topic info: {self.topic_info}")  # 添加调试信息
        return self.topic_info

# 创建全局状态实例
global_state = GlobalState()




