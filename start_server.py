#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DarkAdapter服务器启动脚本
自动寻找可用端口启动服务器
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
import socket
from main import app


def find_free_port(start_port=5000):
    """查找可用端口"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


if __name__ == "__main__":
    port = find_free_port(5000)
    if port:
        print(f"找到可用端口: {port}")
        print(f"服务器将在 http://127.0.0.1:{port} 启动")
        print("API文档: http://127.0.0.1:{port}/docs")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        print("未找到可用端口")