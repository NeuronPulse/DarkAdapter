#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DarkAdapter - 统一AI服务适配器
提供OpenAI兼容格式的API接口，支持多种AI服务
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator
from dataclasses import dataclass

import importlib.util
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 导入模型注册中心
from adapters.model_registry import registry

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据模型
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: int = None
    temperature: float = None
    stream: bool = False

class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int] = None

class AdapterManager:
    """适配器管理器"""
    
    def __init__(self):
        self.adapters = {}
        self.load_adapters()
    
    def load_adapters(self):
        """加载所有适配器"""
        adapters_dir = Path(__file__).parent / "adapters"
        if not adapters_dir.exists():
            return
            
        for adapter_file in adapters_dir.glob("adapter_*.py"):
            try:
                module_name = adapter_file.stem
                spec = importlib.util.spec_from_file_location(module_name, adapter_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 获取适配器实例
                adapter = module.Adapter()
                adapter_name = getattr(module, "ADAPTER_NAME", module_name.replace("adapter_", ""))
                self.adapters[adapter_name] = adapter
                
                logger.info(f"已加载适配器: {adapter_name}")
            except Exception as e:
                logger.error(f"加载适配器 {adapter_file.name} 失败: {e}")
    
    def get_adapter(self, model_name: str) -> Any:
        """获取指定模型的适配器"""
        adapter_name = registry.get_adapter_by_model(model_name)
        return self.adapters.get(adapter_name)
    
    def list_models(self) -> List[str]:
        """列出所有支持的模型"""
        models = []
        for name, adapter in self.adapters.items():
            try:
                supported = adapter.get_supported_models()
                models.extend(supported)
            except Exception:
                logger.warning(f"适配器 {name} 获取模型列表失败")
        return models

class DarkAdapter:
    """DarkAdapter主类 - 统一处理OpenAI格式包装"""
    
    def __init__(self):
        self.adapter_manager = AdapterManager()
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """处理聊天完成请求"""
        adapter = self.adapter_manager.get_adapter(request.model)
        if not adapter:
            raise HTTPException(status_code=404, detail=f"模型 {request.model} 未找到")
        
        try:
            # 转换消息格式为适配器所需的格式
            adapter_messages = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in request.messages
            ]
            
            # 调用适配器获取纯文本响应，传递完整的上下文
            response_text = await adapter.send_message(
                adapter_messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # 包装成OpenAI格式
            return ChatResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                object="chat.completion",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """处理流式聊天完成请求"""
        adapter = self.adapter_manager.get_adapter(request.model)
        if not adapter:
            raise HTTPException(status_code=404, detail=f"模型 {request.model} 未找到")
        
        try:
            # 转换消息格式为适配器所需的格式
            adapter_messages = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in request.messages
            ]
            
            # 生成唯一的响应ID
            response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            created = int(datetime.now().timestamp())
            
            # 发送开始响应
            yield f"data: {json.dumps({
                'id': response_id,
                'object': 'chat.completion.chunk',
                'created': created,
                'model': request.model,
                'choices': [{
                    'index': 0,
                    'delta': {'role': 'assistant'},
                    'finish_reason': None
                }]
            })}\n\n"
            
            # 调用适配器获取流式响应，传递完整的上下文
            async for chunk in adapter.send_message_stream(
                adapter_messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps({
                    'id': response_id,
                    'object': 'chat.completion.chunk',
                    'created': created,
                    'model': request.model,
                    'choices': [{
                        'index': 0,
                        'delta': {'content': chunk},
                        'finish_reason': None
                    }]
                })}\n\n"
            
            # 发送结束响应
            yield f"data: {json.dumps({
                'id': response_id,
                'object': 'chat.completion.chunk',
                'created': created,
                'model': request.model,
                'choices': [{
                    'index': 0,
                    'delta': {},
                    'finish_reason': 'stop'
                }]
            })}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

# FastAPI应用
app = FastAPI(title="DarkAdapter", description="统一AI服务适配器")
dark_adapter = DarkAdapter()

@app.get("/v1/models")
async def list_models():
    """列出所有可用模型"""
    return {
        "object": "list",
        "data": registry.get_all_models()
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """聊天完成"""
    if request.stream:
        return StreamingResponse(
            dark_adapter.chat_completion_stream(request),
            media_type="text/event-stream"
        )
    
    response = await dark_adapter.chat_completion(request)
    return response

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8088, help="端口号")
    parser.add_argument("--host", default="127.0.0.1", help="主机地址")
    args = parser.parse_args()
    
    try:
        uvicorn.run(app, host=args.host, port=args.port)
    except OSError as e:
        print(f"端口 {args.port} 被占用或权限不足，尝试使用 5000")
        uvicorn.run(app, host=args.host, port=5000)