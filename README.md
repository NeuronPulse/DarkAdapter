# DarkAdapter

一个统一的AI服务适配器，提供OpenAI兼容格式的API接口，支持多种AI服务。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
# 自动寻找可用端口启动
py start_server.py

# 或者手动指定端口
py main.py --port 8080 --host 127.0.0.1
```

### 3. 测试API
```bash
curl http://127.0.0.1:5000/v1/models
```

## ✨ 功能特点

- **统一接口**: 提供OpenAI兼容的API格式
- **多服务支持**: 支持百度千帆、ChatGPT、Claude等多种AI服务
- **流式响应**: 支持实时流式输出
- **易于扩展**: 简单的适配器开发模式
- **零配置**: 内置常用AI服务的配置

## 📁 项目结构

```
DarkAdapter/
├── main.py                 # 主程序，提供OpenAI兼容API
├── start_server.py         # 自动启动脚本
├── test_darkadapter.py     # 测试脚本
├── adapters/               # 适配器目录
│   ├── base_adapter.py     # 适配器基类
│   └── adapter_baidu_qianfan.py  # 百度千帆适配器
├── docs/                   # 文档目录
│   └── ADAPTER_TEMPLATE.md # 适配器开发指南
├── USAGE.md               # 详细使用说明
└── requirements.txt        # 项目依赖
```

## 🔧 支持的适配器

- ✅ **baidu-qianfan**: 百度千帆（deepseek-r1模型）
- 🔄 **adapter_chatgpt.py**: ChatGPT适配器（模板）
- 🔄 **adapter_claude.py**: Claude适配器（模板）

## 📝 添加新适配器

1. 创建适配器文件：`adapters/adapter_xxx.py`
2. 继承`BaseAdapter`类
3. 实现`send_message`和`send_message_stream`方法
4. 参考`docs/ADAPTER_TEMPLATE.md`获取详细指南

## 🎯 使用示例

### Python客户端
```python
import httpx

# 列出模型
response = httpx.get("http://127.0.0.1:5000/v1/models")
print(response.json())

# 聊天完成
response = httpx.post(
    "http://127.0.0.1:5000/v1/chat/completions",
    json={
        "model": "baidu-qianfan",
        "messages": [{"role": "user", "content": "你好"}]
    }
)
print(response.json())
```

### JavaScript客户端
```javascript
const response = await fetch('http://127.0.0.1:5000/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        model: 'baidu-qianfan',
        messages: [{ role: 'user', content: '你好' }]
    })
});
const data = await response.json();
console.log(data);
```

## 📖 文档

- [详细使用说明](USAGE.md)
- [适配器开发指南](docs/ADAPTER_TEMPLATE.md)

## 🤝 贡献

欢迎提交新的适配器！请遵循以下步骤：
1. Fork本项目
2. 创建适配器文件
3. 测试适配器功能
4. 提交Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
