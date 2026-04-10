#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import time
import random
from functools import wraps


def retry(max_attempts=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator


def random_delay(min_seconds=1, max_seconds=3):
    """随机延迟，避免请求过快"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def clean_text(text):
    """清理文本内容"""
    if not text:
        return ''
    return ' '.join(text.split()).strip()
