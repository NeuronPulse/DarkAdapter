# DarkAdapter 使用说明

## 项目简介
DarkAdapter是一个统一的AI服务适配器，提供OpenAI兼容格式的API接口，支持多种AI服务。

## 项目结构
```
DarkAdapter/
├── main.py                 # 主程序，提供OpenAI兼容API
├── start_server.py         # 启动脚本
├── test_darkadapter.py     # 测试脚本
├── adapters/               # 适配器目录
│   ├── base_adapter.py     # 适配器基类
│   └── adapter_baidu_qianfan.py  # 百度千帆适配器
├── docs/                   # 文档目录
│   └── ADAPTER_TEMPLATE.md # 适配器开发模板
└── requirements.txt        # 项目依赖
```

## 安装依赖
```bash
pip install httpx[http2] fastapi uvicorn
```

## 启动服务
```bash
# 使用启动脚本（自动寻找可用端口）
py start_server.py

# 或者使用主程序
py main.py --port 8080 --host 127.0.0.1
```

## API接口

### 1. 列出可用模型
```bash
curl http://127.0.0.1:5000/v1/models
```

### 2. 聊天完成（非流式）
```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "baidu-qianfan",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

### 3. 聊天完成（流式）
```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "baidu-qianfan",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": true
  }'
```

### 4. 健康检查
```bash
curl http://127.0.0.1:5000/health
```

## 测试适配器
```bash
# 测试单个适配器
py adapters\adapter_baidu_qianfan.py

# 测试整个系统
py test_darkadapter.py
```

## 添加新适配器

### 1. 创建适配器文件
在`adapters/`目录下创建`adapter_xxx.py`文件：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from base_adapter import BaseAdapter, ChatMessage
from typing import List, AsyncGenerator

ADAPTER_NAME = "your-adapter-name"

class Adapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        # 初始化配置
    
    async def send_message(self, messages: List[ChatMessage], **kwargs) -> str:
        # 实现非流式通信
        pass
    
    async def send_message_stream(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        # 实现流式通信
        pass
    
    def get_supported_models(self) -> List[str]:
        return ["your-model-name"]
```

### 2. 参考模板
查看`docs/ADAPTER_TEMPLATE.md`获取详细的开发指南。

## 注意事项

1. **端口冲突**：如果遇到端口权限问题，启动脚本会自动寻找可用端口
2. **API密钥**：百度千帆适配器已内置API密钥，如需更换请修改适配器文件
3. **网络连接**：确保网络连接正常，能够访问外部AI服务
4. **Windows防火墙**：可能需要允许Python通过防火墙

## 故障排除

### 端口绑定失败
- 使用启动脚本`start_server.py`自动寻找可用端口
- 检查是否有其他程序占用端口
- 尝试使用管理员权限运行

### 适配器加载失败
- 检查文件命名是否符合`adapter_*.py`格式
- 确保适配器类继承自`BaseAdapter`
- 检查`ADAPTER_NAME`变量是否正确设置