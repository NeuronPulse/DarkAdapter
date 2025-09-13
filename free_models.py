'''
在浏览器的控制台里抓取网页对话的流式传输数据（比如 AI 聊天消息的实时推送），通常可以通过以下几种方法实现：

方法 1：监听 fetch 或 XMLHttpRequest 请求
许多 AI 聊天网站（如 ChatGPT、Claude、Gemini 等）使用 fetch 或 XMLHttpRequest 进行流式传输（streaming）。你可以劫持这些请求来查看数据流。

示例代码（适用于 fetch 劫持）
复制
// 保存原始的 fetch 方法
const originalFetch = window.fetch;

// 劫持 fetch
window.fetch = async function (...args) {
  const response = await originalFetch.apply(this, args);
  
  // 如果是流式响应（content-type 可能包含 "stream" 或 "event-stream"）
  if (response.headers.get('content-type')?.includes('stream') || args[0].includes('chat')) {
    const clonedResponse = response.clone(); // 克隆 response，避免影响原数据
    
    // 读取流数据
    const reader = clonedResponse.body.getReader();
    const decoder = new TextDecoder();
    
    let result = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      result += chunk;
      console.log("Stream Chunk:", chunk); // 打印流数据
    }
    
    console.log("Full Stream Data:", result); // 完整数据
    return response; // 返回原 response，不影响网页运行
  }
  
  return response;
};

console.log("Fetch 劫持已启用，开始监听流式数据...");

适用场景：适用于大多数现代 AI 聊天网站（如 OpenAI ChatGPT）。

方法 2：监听 EventSource（SSE 服务器推送）
如果网站使用 Server-Sent Events (SSE) 进行流式传输（如 EventSource），可以监听 message 事件：

复制
// 保存原 EventSource
const originalEventSource = window.EventSource;

// 劫持 EventSource
window.EventSource = class extends originalEventSource {
  constructor(url, options) {
    super(url, options);
    
    this.addEventListener('message', (event) => {
      console.log("SSE Data:", event.data);
    });
    
    this.addEventListener('error', (err) => {
      console.error("SSE Error:", err);
    });
  }
};

console.log("EventSource 劫持已启用，开始监听 SSE 数据...");

适用场景：适用于使用 SSE 的网站（如某些 AI 聊天 API）。

方法 3：监听 WebSocket 数据
如果 AI 聊天使用 WebSocket 进行实时通信：

复制
// 保存原 WebSocket
const originalWebSocket = window.WebSocket;

// 劫持 WebSocket
window.WebSocket = class extends originalWebSocket {
  constructor(url, protocols) {
    super(url, protocols);
    
    this.addEventListener('message', (event) => {
      console.log("WebSocket Data:", event.data);
    });
    
    this.addEventListener('error', (err) => {
      console.error("WebSocket Error:", err);
    });
  }
};

console.log("WebSocket 劫持已启用，开始监听 WebSocket 数据...");

适用场景：适用于 WebSocket 实时通信的 AI 聊天（如某些 API）。

方法 4：直接查看浏览器的 Network 面板
如果不想劫持 API，可以直接：

打开 Chrome DevTools（F12 或 Ctrl+Shift+I）。
进入 Network 选项卡。
筛选 Fetch/XHR 或 WS（WebSocket）。
查看请求的 Response 或 Preview 面板，观察流式数据。
方法 5：使用 MutationObserver 监听 DOM 变化
如果 AI 聊天直接更新 DOM（而不是 API 流），可以监听 DOM 变化：

复制
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.addedNodes.length) {
      console.log("DOM 更新:", mutation.addedNodes);
    }
  });
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

console.log("DOM 监听已启用，开始观察聊天消息...");

适用场景：适用于前端直接渲染流式数据的网站。

总结
方法	适用场景	备注
劫持 fetch	适用于 fetch 流式传输	适用于 ChatGPT 类网站
劫持 EventSource	适用于 SSE 服务器推送	适用于某些 API
劫持 WebSocket	适用于 WebSocket 实时通信	适用于某些 AI 聊天
Network 面板	手动查看 API 请求	无需代码
MutationObserver	监听 DOM 变化	适用于前端渲染
你可以根据目标网站的具体实现方式选择合适的方法。
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度千帆 deepseek-r1 控制台交互 REPL
"""
import json, os, sys
import httpx

URL = "https://qianfan.baidubce.com/v2/chat/completions"
HEADERS = {
    "Authorization": "Bearer bce-v3/ALTAK-15DCDsnjzQ0mCNuO0j39Y/22731c5794cc1f0f2d81435ab7aab1aaf6709162",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
}

MESSAGES = [
    {"role": "system", "content": "你是一个智能助手。"}
]

def stream_chat():
    """一次对话，返回 (reasoning, reply) 并追加到 MESSAGES"""
    reasoning_acc, content_acc = "", ""
    body = {"model": "deepseek-r1", "stream": True, "messages": MESSAGES}

    with httpx.Client(http2=True) as client:
        with client.stream("POST", URL, headers=HEADERS, json=body, timeout=60) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                json_str = line[5:].strip()
                if json_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(json_str)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                if delta.get("reasoning_content"):
                    reasoning_acc += delta["reasoning_content"]
                    print(f"{delta['reasoning_content']}", end="", flush=True)
                if delta.get("content"):
                    content_acc += delta["content"]
                    print(delta["content"], end="", flush=True)
    print()
    MESSAGES.append({"role": "assistant", "content": reasoning_acc + content_acc})
    return reasoning_acc, content_acc

def main():
    global MESSAGES
    while True:
        try:
            user = input("Input:").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if user == "/raw":
            print(json.dumps(MESSAGES, ensure_ascii=False, indent=2))
            continue
        MESSAGES.append({"role": "user", "content": user})
        print("<thirnk>\n", end="", flush=True)
        reasoning, reply = stream_chat()
        if reply:
            print("\n<thirnk>\n", end="", flush=True)
        else:
            print("\n<think>\n", end="", flush=True)
            print(reasoning)

if __name__ == "__main__":
    main()
