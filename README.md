### UV项目级包管理工具

1、创建项目

```bash
uv init ai-agent-test
```

2、安装依赖

```bash
# yaml依赖
uv add pyyaml
```

```bash
# langchain ollama
uv add langchain-ollama
```

### Redis Stack 配置

`agent_chat.py` 使用 Redis 作为 LangGraph checkpointer，需要 Redis Stack（带 RediSearch 模块）。

**Docker Compose 部署：**
```bash
cd /Users/vincent/developEnv/docker-compose/redis-stack
docker compose up -d
```

**常见问题：**

1. `unknown command 'FT._LIST'` - docker-compose 的 `command` 覆盖了默认启动脚本，导致 RediSearch 模块未加载。需在 `redis.conf` 中添加 `loadmodule` 配置：
   ```
   loadmodule /opt/redis-stack/lib/rediscompat.so
   loadmodule /opt/redis-stack/lib/redisearch.so MAXSEARCHRESULTS 10000 MAXAGGREGATERESULTS 10000
   loadmodule /opt/redis-stack/lib/redistimeseries.so
   loadmodule /opt/redis-stack/lib/rejson.so
   loadmodule /opt/redis-stack/lib/redisbloom.so
   loadmodule /opt/redis-stack/lib/redisgears.so v8-plugin-path /opt/redis-stack/lib/libredisgears_v8_plugin.so
   ```

2. 端口被占用：`redis://localhost:63380/0` 对应 Docker 容器端口 63380

