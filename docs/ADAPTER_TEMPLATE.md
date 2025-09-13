# 适配器开发模板

## 概述

本模板用于创建新的AI服务适配器，通过浏览器劫持技术获取各种在线AI聊天服务的响应。

## 适配器命名规范

- 文件名: `adapter_<服务名>.py`
- 适配器标识: `ADAPTER_NAME = "<服务名>"`
- 类名: `Adapter` (继承自BaseAdapter)

## 适配器结构

### 必需组件

1. **适配器标识**
   ```python
   ADAPTER_NAME = "your-service-name"
   ```

2. **Adapter类**
   ```python
   from .base_adapter import BaseAdapter, ChatRequest
   
   class Adapter(BaseAdapter):
       def __init__(self):
           super().__init__()
           # 初始化配置
   ```

### 必需方法

#### 1. 非流式聊天
```python
async def chat(self, request: ChatRequest) -> str:
    """处理非流式聊天请求"""
    # 实现获取响应的逻辑
    content = await self._get_response(request)
    return self.format_response(content, request.model)
```

#### 2. 流式聊天
```python
async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
    """处理流式聊天请求"""
    # 实现获取流式响应的逻辑
    async for chunk in self._get_stream_response(request):
        yield self.format_stream_chunk(chunk, request.model)
```

#### 3. 获取支持的模型
```python
def get_supported_models(self) -> List[str]:
    """返回该适配器支持的模型列表"""
    return ["model1", "model2", "model3"]
```

### 可选方法

#### 验证凭据
```python
async def validate_credentials(self) -> bool:
    """验证服务凭据是否有效"""
    # 实现凭据验证逻辑
    return True
```

## 浏览器劫持实现指南

### 1. 分析目标网站

#### 步骤
1. 打开目标网站，登录账号
2. 打开浏览器开发者工具 (F12)
3. 切换到Network标签
4. 发送一条测试消息
5. 观察网络请求

#### 需要记录的信息
- API端点URL
- 请求头 (特别是Authorization)
- 请求体格式
- 响应格式

### 2. 获取认证信息

#### Cookie方法
```python
# 从浏览器获取cookie
self.session_token = "从浏览器复制的token"
```

#### Bearer Token方法
```python
# 从浏览器获取Bearer token
self.auth_token = "从浏览器复制的token"
```

### 3. 请求构造

#### 标准HTTP请求
```python
import httpx

async def _make_request(self, prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {self.auth_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0..."
    }
    
    payload = {
        "prompt": prompt,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.service.com/chat",
            json=payload,
            headers=headers
        )
        return response.json()["choices"][0]["text"]
```

#### WebSocket方法
```python
import websockets

async def _websocket_chat(self, prompt: str) -> AsyncGenerator[str, None]:
    uri = "wss://service.com/ws"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"prompt": prompt}))
        async for message in websocket:
            data = json.loads(message)
            yield data["content"]
```

### 4. 响应解析

#### JSON响应
```python
def _parse_response(self, response: dict) -> str:
    """解析JSON响应"""
    return response.get("choices", [{}])[0].get("text", "")
```

#### SSE流式响应
```python
async def _parse_sse_response(self, response):
    """解析SSE流式响应"""
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            data = json.loads(line[6:])
            yield data["choices"][0]["delta"].get("content", "")
```

## 错误处理

### 标准错误响应
```python
from fastapi import HTTPException

async def chat(self, request: ChatRequest) -> str:
    try:
        content = await self._get_response(request)
        return self.format_response(content, request.model)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 重试机制
```python
import asyncio

async def _get_response_with_retry(self, request: ChatRequest, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await self._get_response(request)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

## 测试适配器

### 单元测试模板
```python
import pytest
from adapters.adapter_yourservice import Adapter

@pytest.mark.asyncio
async def test_chat():
    adapter = Adapter()
    request = ChatRequest(
        model="your-model",
        messages=[{"role": "user", "content": "Hello"}]
    )
    response = await adapter.chat(request)
    assert len(response) > 0
```

### 集成测试
```python
# tests/test_yourservice.py
import requests

response = requests.post("http://localhost:8000/v1/chat/completions", json={
    "model": "your-service-name",
    "messages": [{"role": "user", "content": "Hello"}]
})
print(response.json())
```

## 文档要求

### README.md
每个适配器都应该有对应的文档文件：

```markdown
# <服务名>适配器

## 支持的模型
- model1
- model2

## 使用方法

### 获取认证信息
1. 打开网站...
2. 复制token...

### 配置适配器
```python
adapter = Adapter()
adapter.set_credentials("your-token")
```

## API端点
- 聊天: POST /api/chat
- 流式: GET /api/chat/stream

## 注意事项
- 需要登录账号
- 有频率限制
```

## 最佳实践

1. **安全性**
   - 不要在代码中硬编码敏感信息
   - 使用环境变量存储token
   - 实现token刷新机制

2. **性能**
   - 使用连接池
   - 实现缓存机制
   - 设置合理的超时时间

3. **可靠性**
   - 实现重试机制
   - 添加错误日志
   - 处理网络异常

4. **兼容性**
   - 遵循OpenAI API格式
   - 支持多种响应格式
   - 处理不同版本API