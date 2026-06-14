# ChatBot API - 完整功能后端服务

基于 FastAPI + WebSocket + Redis + SQLAlchemy 的完整后端服务，支持：

- 🤖 实时 WebSocket 聊天和 AI 图像生成
- 🔗 完整的 REST API（用户、课程、作业管理等）
- 📊 分布式会话状态管理
- 🚀 高性能数据库连接
- 📈 Locust 性能测试套件

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │    REST API     │    │   Performance   │
│   聊天机器人      │    │   (8个模块)      │    │   Testing       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              FastAPI 主应用                      │
         └─────────────────────────────────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐
         │     Redis       │    │   SQL Server    │
         │   会话状态存储     │    │   业务数据存储     │
         └─────────────────┘    └─────────────────┘
```

## 📦 功能模块

### WebSocket 聊天机器人

- 实时对话功能（通义千问 LLM）
- AI 图像生成（万相 2.1）
- Redis 分布式会话管理
- 多 worker 支持

### REST API 模块

- **用户管理** (`/api/users/`) - 用户登录、信息管理
- **课程管理** (`/api/courses/`) - 课程创建、查询
- **作业管理** (`/api/homeworks/`) - 作业评价、管理
- **内容管理** (`/api/contents/`) - 课程内容目录
- **记录管理** (`/api/records/`) - 学习记录追踪
- **任务管理** (`/api/tasks/`) - 任务分配、查询
- **班级管理** (`/api/classes/`) - 班级创建、管理
- **平台功能** (`/api/platform/`) - AI 对话、文档处理

## 🚀 生产部署

部署到 Ubuntu 24.04 生产环境：

```bash
# 1. 设置环境变量
export DASHSCOPE_API_KEY=your_api_key
export DATABASE_URL=your_db_url  # 可选

# 2. 一键部署
./deploy.sh

# 3. 验证部署
curl http://your_server:8001/health
```

## 📊 性能测试

### 运行负载测试

```bash
# 安装Locust
pip install locust

# 运行性能测试
python run_test.py

# 或直接使用Locust
locust -f locustfile.py --host=http://your_server:8001

# 打开Locust Web界面
open http://localhost:8089
```

### 测试覆盖范围

#### API 接口 (14 个)

- ✅ 用户登录 (`GET /users/login`)
- ✅ 获取课程目录 (`GET /contents/get`)
- ✅ 获取课程 (`GET /courses/get`)
- ✅ 自由对话 (`POST /platform/chat`)
- ✅ 评价作业 (`POST /platform/evaluateHomework`)
- ✅ 获取作业 (`GET /tasks/get`)
- ✅ 添加记录 (`POST /records/add`)
- ✅ 创建课程 (`POST /courses/create`)
- ✅ 创建课程码 (`GET /classes/create`)

#### 测试场景 (4 个)

- ✅ 轻负载测试 (100 用户, 120 秒)
- ✅ 正常负载测试 (200 用户, 120 秒)
- ✅ 压力测试 (400 用户, 300 秒)
- ✅ 峰值负载测试 (500 用户, 600 秒)

## 📊 监控和维护

```bash
# 查看服务状态
docker compose ps

# 实时日志
docker compose logs -f

# 性能监控
docker stats

# 数据备份
docker compose exec redis redis-cli BGSAVE
```

## 🔧 开发工具

- **API 文档**: http://your_server:8001/docs
- **健康检查**: http://your_server:8001/health
- **Locust 测试界面**: http://localhost:8089

## 📝 API 端点总览

### WebSocket

- `ws://your_server:8001/ws/{session_id}` - 聊天机器人连接

### REST API

- `GET /` - 服务状态
- `GET /health` - 健康检查
- `GET /docs` - API 文档
- `GET /api/users/*` - 用户管理
- `GET /api/courses/*` - 课程管理
- `POST /api/platform/chat` - AI 对话
- `POST /api/platform/evaluateHomework` - 作业评价

完整 API 列表请访问: http://your_server:8001/docs

## ⚠️ 注意事项

1. **测试环境**: 建议在独立环境运行
2. **数据准备**: 确保数据库有测试用户数据
3. **AI 服务**: 注意 API 调用限制和成本
4. **资源监控**: 同时监控系统资源使用
5. **逐步加压**: 从小负载开始测试

## � M1 Pro 快速测试

### 一键测试脚本

```bash
# 1. 完整环境测试
./test_local.sh

# 2. 数据库和Redis连接测试
./test_connections.py

# 3. WebSocket聊天测试
./test_websocket_client.py
```

### 手动测试步骤

```bash
# 1. 安装依赖
brew install python@3.11 redis
brew services start redis

# 2. 设置环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
export DASHSCOPE_API_KEY=your_api_key

# 4. 启动应用
python main.py
```

## �🖥️ M1 Pro MacBook 本机测试指南

### 环境准备

1. **安装依赖**

```bash
# 安装Python 3.11+
brew install python@3.11

# 安装Redis
brew install redis

# 启动Redis服务
brew services start redis
```

2. **设置项目环境**

```bash
# 克隆并进入项目目录
cd /path/to/ChatbotApi

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

3. **配置环境变量**

```bash
# 创建.env文件
cat > .env << EOF
DASHSCOPE_API_KEY=your_dashscope_api_key
REDIS_URL=redis://localhost:6379
DATABASE_URL=mssql+pymssql://coding_data:Hello2023!@rm-bp10v29fkj305q3smfo.sqlserver.rds.aliyuncs.com:3433/chatbot_test?charset=utf8
EOF

# 或者直接导出环境变量
export DASHSCOPE_API_KEY=your_api_key
export REDIS_URL=redis://localhost:6379
```

### 本机测试步骤

#### 1. 基础功能测试

```bash
# 启动应用
python main.py

# 新开终端测试各功能
# 测试健康检查
curl http://localhost:8001/health

# 测试API文档
open http://localhost:8001/docs

# 测试状态页面
curl http://localhost:8001/
```

#### 2. WebSocket 聊天测试

```bash
# 安装WebSocket测试工具
npm install -g wscat

# 测试WebSocket连接
wscat -c ws://localhost:8001/ws/test_session

# 发送测试消息
{"role": "user", "content": "你好"}

# 测试图像生成
{"role": "user", "content": "生成一张猫咪的图片"}
```

#### 3. REST API 测试

```bash
# 测试用户登录
curl -X GET "http://localhost:8001/api/users/login" \
  -H "accept: application/json"

# 测试课程查询
curl -X GET "http://localhost:8001/api/courses/get" \
  -H "accept: application/json"

# 查看完整API文档
open http://localhost:8001/docs
```

#### 4. 性能测试

```bash
# 安装Locust（如未安装）
pip install locust

# 运行性能测试
python run_test.py

# 或直接使用Locust
locust -f locustfile.py --host=http://localhost:8001

# 打开Locust Web界面
open http://localhost:8089
```

#### 5. Redis 连接测试

```bash
# 检查Redis状态
redis-cli ping

# 查看Redis中的会话数据
redis-cli keys "websocket_session:*"

# 监控Redis操作
redis-cli monitor
```

### M1 Pro 特定优化

```bash
# 检查M1芯片优化状态
python -c "
import platform
print(f'架构: {platform.machine()}')
print(f'Python版本: {platform.python_version()}')

try:
    import uvloop
    print('✅ uvloop可用 (性能优化)')
except ImportError:
    print('⚠️ uvloop不可用')
"

# 性能监控
python -c "
import multiprocessing
import psutil
print(f'CPU核心数: {multiprocessing.cpu_count()}')
print(f'内存使用: {psutil.virtual_memory().percent}%')
"
```

## 🐳 Docker 本机测试

如果您想在 M1 Pro 上测试 Docker 部署：

```bash
# 确保Docker Desktop已安装并运行
docker --version
docker compose --version

# 构建并启动服务
docker compose up --build

# 测试容器化服务
curl http://localhost:8001/health

# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

## 🧪 完整测试流程

### 1. 单元测试

```bash
# 运行API模块测试
python -m pytest api/ -v

# 测试数据库连接
python -c "from db.database import engine; print('✅ 数据库连接成功' if engine else '❌ 数据库连接失败')"
```

### 2. 集成测试

```bash
# 启动服务
python main.py &

# 等待服务启动
sleep 5

# 运行集成测试
python -c "
import requests
import json

# 测试REST API
response = requests.get('http://localhost:8001/health')
print(f'健康检查: {response.status_code}')

# 测试WebSocket（需要websocket-client库）
# pip install websocket-client
import websocket
ws = websocket.create_connection('ws://localhost:8001/ws/test')
ws.send(json.dumps({'role': 'user', 'content': '测试消息'}))
result = ws.recv()
print(f'WebSocket响应: {result[:100]}...')
ws.close()

print('✅ 集成测试完成')
"
```

### 3. 负载测试

```bash
# 轻量级测试（100用户，60秒）
locust -f locustfile.py --host=http://localhost:8001 -u 100 -r 10 -t 60s --headless

# 查看测试报告
ls -la reports/
```

## 🛠️ 故障排查

### 常见问题

**M1 芯片兼容性问题**

```bash
# 如果某些包安装失败，使用Rosetta
arch -x86_64 pip install problematic_package
```

**Redis 连接问题**

```bash
# 检查Redis是否运行
brew services list | grep redis

# 重启Redis
brew services restart redis
```

**数据库连接问题**

```bash
# 测试数据库连接
python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
try:
    engine.execute('SELECT 1')
    print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"
```

**性能问题调试**

```bash
# 监控进程
top -pid $(pgrep -f "python main.py")

# 内存使用分析
python -c "
import tracemalloc
tracemalloc.start()
# 运行你的代码
current, peak = tracemalloc.get_traced_memory()
print(f'当前内存: {current / 1024 / 1024:.1f} MB')
print(f'峰值内存: {peak / 1024 / 1024:.1f} MB')
"
```

## 🚀 生产部署

部署到 Ubuntu 24.04 生产环境：

```bash
# 1. 设置环境变量
export DASHSCOPE_API_KEY=your_api_key
export DATABASE_URL=your_db_url  # 可选

# 2. 一键部署
./deploy.sh

# 3. 验证部署
curl http://your_server:8001/health
```

## 📊 监控和维护

```bash
# 查看服务状态
docker compose ps

# 实时日志
docker compose logs -f

# 性能监控
docker stats

# 数据备份
docker compose exec redis redis-cli BGSAVE
```

## 🔧 开发工具

- **API 文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health
- **Locust 测试界面**: http://localhost:8089
- **Redis 监控**: `redis-cli monitor`

---

## 📝 API 端点总览

### WebSocket

- `ws://localhost:8001/ws/{session_id}` - 聊天机器人连接

### REST API

- `GET /` - 服务状态
- `GET /health` - 健康检查
- `GET /docs` - API 文档
- `GET /api/users/*` - 用户管理
- `GET /api/courses/*` - 课程管理
- `POST /api/platform/chat` - AI 对话
- `POST /api/platform/evaluateHomework` - 作业评价

完整 API 列表请访问: http://localhost:8001/docs

- ✅ 峰值负载测试 (500 用户, 600 秒)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 API 服务

```bash
python3 main.py
```

### 3. 运行测试

#### Web 界面模式（推荐）

```bash
python run_test.py light_load local --web
# 访问 http://localhost:8089
```

#### 命令行模式

```bash
# 快速测试
python run_test.py light_load local

# 压力测试
python run_test.py stress_test local

# 直接使用locust
locust -f locustfile.py --host=http://后端IP:后端端口
```

## 📊 性能指标

### 目标指标

- **响应时间**: < 2 秒
- **成功率**: > 95%
- **并发支持**: 100+ 用户

### 监控重点

- 登录接口性能
- 对话流式响应
- 数据库查询性能
- AI 服务调用稳定性

## 🔧 自定义配置

### 修改测试数据

编辑 `locust_config.py` 中的：

- `TEST_USERS` - 测试用户数据
- `TEST_DATA` - 测试内容数据
- `API_WEIGHTS` - 接口调用权重

### 调整测试场景

修改 `TEST_SCENARIOS` 配置：

```python
"custom_test": {
    "users": 30,
    "spawn_rate": 3,
    "duration": "180s",
    "description": "自定义测试"
}
```

## ⚠️ 注意事项

1. **测试环境**: 建议在独立环境运行
2. **数据准备**: 确保数据库有测试用户数据
3. **AI 服务**: 注意 API 调用限制和成本
4. **资源监控**: 同时监控系统资源使用
5. **逐步加压**: 从小负载开始测试

## 🐛 故障排查

### 常见问题

- **登录失败**: 丢包导致无法正确访问登录 API
- **响应超时**: 检查 AI 服务连接

### 调试模式

```bash
locust -f locustfile.py --host=http://127.0.0.1:8000 --loglevel=DEBUG
```

## 📈 后续扩展

1. **集成 CI/CD**: 添加到持续集成流程
2. **监控告警**: 结合 Prometheus 等监控工具
3. **性能分析**: 集成 APM 工具进行深度分析
4. **自动化报告**: 生成性能趋势报告
5. **多环境测试**: 支持更多部署环境

---

测试套件已完整部署，可以开始进行性能测试！🎉
