#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
强化版比赛开始检测节点
修复问题：参数/start未被正确设置
'''

import rospy
import os
import sys
import signal
import time
import subprocess
import decoder
from std_msgs.msg import String

class EnhancedGameStartDetector:
    def __init__(self):
        # 初始化ROS节点（禁用匿名模式以便调试）
        rospy.init_node('game_start_detector', anonymous=False)
        
        rospy.loginfo("\n=== 强化版比赛开始检测节点启动 ===\n")
        
        # 关键路径配置
        self.resources = {
            'model': '/home/abot/340406/src/robot_slam/resources/models/startGame.pmdl',
            'audio': '/home/abot/340406/src/robot_slam/resources/startGame.wav',
            'resource': '/home/abot/340406/src/robot_slam/resources/common.res'
        }
        
        # 增强的文件检查
        if not self._validate_resources():
            rospy.logerr("关键资源文件验证失败！")
            sys.exit(1)
            
        # 强制初始化参数服务器
        self._init_parameters()
        
        # 信号处理增强
        self._init_signal_handlers()
        
        # 音频系统初始化
        self._init_audio_system()
        
        # ROS通信设置
        self.pub = rospy.Publisher('/game_start', String, queue_size=10, latch=True)
        
    def _validate_resources(self):
        """增强型资源验证"""
        valid = True
        for name, path in self.resources.items():
            try:
                if not os.path.exists(path):
                    rospy.logerr(f"[资源错误] {name} 不存在: {path}")
                    valid = False
                elif not os.access(path, os.R_OK):
                    rospy.logerr(f"[权限错误] {name} 不可读: {path}")
                    valid = False
                else:
                    rospy.loginfo(f"[资源验证] {name} 有效: {path}")
            except Exception as e:
                rospy.logerr(f"[验证异常] 检查 {name} 时出错: {str(e)}")
                valid = False
        return valid
    
    def _init_parameters(self):
        """参数服务器初始化"""
        try:
            # 删除可能存在的旧参数
            if rospy.has_param('/start'):
                rospy.delete_param('/start')
            
            # 设置初始参数（带超时保护）
            rospy.set_param('/start', False)
            rospy.loginfo("[参数初始化] /start = False")
            
            # 验证参数设置
            if not rospy.has_param('/start'):
                rospy.logerr("[参数错误] 无法设置/start参数！")
                raise RuntimeError("Parameter server error")
        except Exception as e:
            rospy.logerr(f"[参数异常] 初始化失败: {str(e)}")
            raise
    
    def _init_signal_handlers(self):
        """信号处理初始化"""
        self.termination_requested = False
        signal.signal(signal.SIGINT, self._handle_termination)
        signal.signal(signal.SIGTERM, self._handle_termination)
        rospy.on_shutdown(self._handle_shutdown)
    
    def _init_audio_system(self):
        """音频系统初始化"""
        # 设置音频环境变量
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['PULSE_PROP'] = 'media.role=event'
        
        # 测试音频播放
        if not self._test_audio_playback():
            rospy.logwarn("[音频警告] 初始音频测试失败，将继续运行但可能无声音")
    
    def _test_audio_playback(self):
        """测试音频播放功能"""
        try:
            rospy.loginfo("[音频测试] 正在测试音频播放...")
            result = subprocess.call(
                ['aplay', '-q', self.resources['audio']],
                stderr=subprocess.DEVNULL
            )
            if result == 0:
                rospy.loginfo("[音频测试] 播放测试成功")
                return True
        except Exception as e:
            rospy.logwarn(f"[音频测试] 播放失败: {str(e)}")
        return False
    
    def _handle_termination(self, signum, frame):
        """处理终止信号"""
        rospy.loginfo(f"\n接收到终止信号({signum})，正在关闭...")
        self.termination_requested = True
    
    def _handle_shutdown(self):
        """ROS节点关闭处理"""
        rospy.loginfo("ROS节点关闭中...")
        self.termination_requested = True
    
    def _should_terminate(self):
        """检查是否应该终止"""
        return self.termination_requested or rospy.is_shutdown()
    
    def _trigger_start(self):
        """触发比赛开始逻辑"""
        try:
            rospy.loginfo("\n=== 检测到'比赛开始'语音命令 ===\n")
            
            # 1. 播放音频反馈
            self._play_audio_feedback()
            
            # 2. 设置ROS参数（带重试机制）
            self._set_parameter_with_retry()
            
            # 3. 发布ROS消息
            self._publish_start_event()
            
            # 4. 添加防抖延迟
            time.sleep(2.5)
            
        except Exception as e:
            rospy.logerr(f"[触发错误] 处理失败: {str(e)}")
    
    def _play_audio_feedback(self):
        """播放音频反馈（带备用方案）"""
        max_attempts = 2
        for attempt in range(1, max_attempts+1):
            try:
                if attempt == 1:
                    # 尝试直接系统调用
                    result = subprocess.call(
                        ['aplay', '-q', self.resources['audio']],
                        stderr=subprocess.DEVNULL
                    )
                    if result == 0:
                        return
                else:
                    # 回退到decoder播放
                    decoder.play_audio_file(self.resources['audio'])
                    return
            except Exception as e:
                if attempt == max_attempts:
                    rospy.logwarn(f"[音频播放] 最终尝试失败: {str(e)}")
    
    def _set_parameter_with_retry(self):
        """带重试机制的参数设置"""
        max_attempts = 3
        for attempt in range(1, max_attempts+1):
            try:
                rospy.set_param('/start', True)
                
                # 验证参数是否设置成功
                if rospy.get_param('/start') == True:
                    rospy.loginfo(f"[参数设置] 成功 (尝试 {attempt}/{max_attempts})")
                    return
                
                time.sleep(0.1)  # 短暂延迟后重试
            except Exception as e:
                if attempt == max_attempts:
                    rospy.logerr(f"[参数错误] 最终设置失败: {str(e)}")
                else:
                    rospy.logwarn(f"[参数警告] 尝试 {attempt} 失败: {str(e)}")
    
    def _publish_start_event(self):
        """发布比赛开始事件"""
        try:
            msg = String()
            msg.data = "game_start"
            self.pub.publish(msg)
            rospy.loginfo("[消息发布] 已发送比赛开始事件")
        except Exception as e:
            rospy.logerr(f"[发布错误] 无法发送消息: {str(e)}")
    
    def run(self):
        """主运行循环"""
        try:
            rospy.loginfo("\n=== 正在初始化语音检测器 ===\n")
            
            # 初始化检测器（带灵敏度调节）
            sensitivity = rospy.get_param('~sensitivity', 0.65)
            rospy.loginfo(f"使用检测灵敏度: {sensitivity}")
            
            self.detector = decoder.HotwordDetector(
                self.resources['model'],
                resource=self.resources['resource'],
                sensitivity=sensitivity,
                audio_gain=1.3
            )
            
            rospy.loginfo("\n=== 准备就绪，等待'比赛开始'语音 ===\n")
            rospy.loginfo("当前参数状态: /start = " + 
                         str(rospy.get_param('/start', '未设置')))
            
            # 主检测循环
            self.detector.start(
                detected_callback=self._trigger_start,
                interrupt_check=self._should_terminate,
                sleep_time=0.02
            )
            
            # 保持节点运行
            while not self._should_terminate() and not rospy.is_shutdown():
                time.sleep(0.1)
                
        except Exception as e:
            rospy.logerr(f"\n=== 主循环错误 ===\n{str(e)}")
        finally:
            self._cleanup()
            rospy.loginfo("\n=== 节点已安全停止 ===\n")
    
    def _cleanup(self):
        """资源清理"""
        try:
            if hasattr(self, 'detector') and self.detector:
                self.detector.terminate()
                rospy.loginfo("[资源清理] 检测器已终止")
        except Exception as e:
            rospy.logerr(f"[清理错误] 资源释放失败: {str(e)}")

if __name__ == '__main__':
    try:
        detector = EnhancedGameStartDetector()
        detector.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("ROS中断请求")
    except Exception as e:
        rospy.logerr(f"\n=== 致命错误 ===\n{str(e)}")
        sys.exit(1)
