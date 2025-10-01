#!/usr/bin/env python3
"""
日志系统配置
统一的日志管理
"""

import logging
import os
from datetime import datetime
from pathlib import Path


class LoggerSetup:
    """日志配置器"""

    @staticmethod
    def setup(name="make_video", level=logging.INFO, log_to_file=True):
        """
        配置日志系统

        Args:
            name: 日志记录器名称
            level: 日志级别
            log_to_file: 是否输出到文件

        Returns:
            logger实例
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # 避免重复添加handler
        if logger.handlers:
            return logger

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 文件输出
        if log_to_file:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # 按日期创建日志文件
            log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger


# 便捷函数
def get_logger(name="make_video"):
    """获取logger实例"""
    return LoggerSetup.setup(name)


# 全局logger
logger = get_logger()
