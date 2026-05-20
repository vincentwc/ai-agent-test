# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 LangGraph + LangChain 的 AI Agent 项目，支持多轮对话记忆和文件操作工具。

## 常用命令

```bash
# 安装依赖
uv add <package>

# 运行 agent
uv run python -m app.code_agent.agent.agent_chat

# 运行多会话聊天（基于文件存储历史）
uv run python -m app.code_agent.agent.multi_chat
```

## 依赖管理

- 使用 `uv` 管理 Python 依赖
- 依赖声明在 `pyproject.toml`
- `.env` 文件存储 BAILIAN_API_KEY 等敏感配置

## 核心架构

### Agent 实现

- `agent_chat.py`: 基于 `langgraph.checkpoint.redis.RedisSaver` 的持久化 Agent，支持多轮对话记忆通过 Redis 存储
- `multi_chat.py`: 基于 `RunnableWithMessageHistory` 的串行链式 Agent，使用 `FileChatMessageHistory` 存储对话历史

### LLM 模型

- `model/qwen.py`: 使用阿里云百炼 Qwen-Max，通过 `langchain_openai.ChatOpenAI` 接口调用

### 工具

- `tools/file_tools.py`: 基于 `FileManagementToolkit` 的文件操作工具集（读/写/列表等）
- `prompts/multi_chat_prompt.py`: 多轮对话提示词模板

### Redis Checkpoint

- `agent_chat.py` 使用 Redis 作为 LangGraph checkpointer 实现对话持久化
- Redis 连接: `redis://localhost:63380/0`
- Redis Stack 容器配置在 `/Users/vincent/developEnv/docker-compose/redis-stack/`
