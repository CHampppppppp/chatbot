# AGENTS.md

## 项目概况

这是一个前后端分离的校园智能体项目。

- `Chatbot/`: Nuxt 3 前端，默认开发地址当前为 `http://localhost:3005/app1`。
- `ChatbotApi/`: FastAPI 后端，默认开发地址当前为 `http://localhost:8001`。
- `dev.sh`: 本地一键启动脚本，会启动 Redis、后端和前端。

## 目录约定

- 前端页面放在 `Chatbot/pages/`。
- 前端组件放在 `Chatbot/components/`。
- 前端请求封装放在 `Chatbot/api/` 或 `Chatbot/plugins/`。
- 前端跨页面状态和流程逻辑放在 `Chatbot/composables/`。
- 前端路由守卫放在 `Chatbot/middleware/`。
- 后端路由实现放在 `ChatbotApi/api/`。
- 后端路由聚合放在 `ChatbotApi/router/`。
- 后端配置放在 `ChatbotApi/common/config.py`，但密钥值必须来自环境变量。
- 后端数据库连接和模型放在 `ChatbotApi/db/`。
- 后端第三方 AI 服务封装放在 `ChatbotApi/utils/`。
- 后端配置与鉴权回归测试放在 `ChatbotApi/tests/`，文件以 `test_*.py` 命名；测试不得依赖真实数据库、Redis 或第三方服务。

不要把临时脚本、调试输出、测试上传文件散放到根目录。需要临时验证时优先使用系统临时目录，完成后清理。

## 环境变量与密钥

- 禁止把密钥、token、密码、生产数据库连接串写入代码。
- 禁止把 `.env` 内容打印到日志或回复里。
- 修改 `.env`、密钥、token、CI/CD 配置前必须先询问用户。
- 新增配置时优先使用环境变量，并在文档中说明变量名、用途和默认行为。
- IP + HTTP 部署可通过 `CORS_ALLOWED_ORIGINS` 配置前端来源，Cookie 默认使用 `secure=false` 和 `samesite=lax`；切换 HTTPS 时必须显式设置 `COOKIE_SECURE=true`，跨站 Cookie 还需设置 `COOKIE_SAMESITE=none`。
- dev/prod 行为必须显式区分，不允许让本地开发默认跳生产 SSO 或生产域名。

## 本地开发

优先使用根目录脚本启动：

```bash
./dev.sh
```

手动启动前端：

```bash
cd Chatbot
pnpm dev
```

手动启动后端：

```bash
cd ChatbotApi
source venv/bin/activate
ENV=dev uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

当前前端配置包含 `app.baseURL = "/app1"`，所以本地访问路径通常是：

```text
http://localhost:3005/app1
```

如果登录守卫因为缺少课程路径而跳授权页，可以在浏览器控制台临时设置：

```js
localStorage.setItem("base_path", "app1")
```

这只是开发绕过手段。正式修复应改配置和鉴权流程，不要继续扩大硬编码路径。

## 数据库切换与迁移

后端同时支持 **云 SQL Server** 和 **本地 MySQL**，通过 `DATABASE_URL` 单变量切换。


## 代码约束

- 遵守现有框架：前端用 Nuxt 3/Vue 3，后端用 FastAPI/SQLAlchemy。
- 不为了让代码跑起来注释掉报错或吞掉异常，要找根因。
- 不新增全局依赖；需要安装新的全局依赖前必须先询问用户。
- 新增项目依赖前说明用途，并优先选择项目内依赖。
- 不做无关重构，不格式化无关文件。
- 不删除文件、目录或 git 历史，除非用户明确要求。
- 不执行 `git push`、`git rebase`、`git reset --hard`、强制推送。
- 不做数据库 schema 变更或数据迁移，除非用户确认。
- 不发布、不部署到生产、不执行公开发布操作，除非用户确认。

## 前端注意事项

- 不要在开发环境写死生产域名、生产 SSO 地址或 `/app1` 以外的新部署路径。
- 路由跳转优先使用 Nuxt 路由 API；只有跳外部站点时才使用 `window.location`。
- AI 返回内容、用户输入、后端返回 HTML 不得直接 `v-html` 渲染，必须先消毒或改为安全渲染。
- Axios/Fetch 错误处理必须避免重复触发全局错误事件。
- 登录、授权、SSO、课程选择相关逻辑要集中收敛，避免多个文件各自拼 URL。

## 后端注意事项

- `SECRET_KEY`、SSO app key/secret、AI provider key、数据库连接串必须来自环境变量。
- 鉴权依赖统一走 `common/security.py`，不要在业务接口里重复解析 token。
- 管理员接口必须有明确权限判断，不能只校验登录态。
- Cookie 的 `secure`、`samesite` 要区分 dev/prod。
- 不要用 `print` 打业务日志、用户身份、SSO 响应或异常详情；使用 logger，并避免泄漏敏感信息。
- Redis、数据库、第三方 AI 服务异常要返回稳定错误结构。

## 维度评分触发规则

- 只有带 RAG 的聊天角色（`校园精灵 /chat`、`电脑博士 /computerDoctor`）会在单轮 SSE 响应结束后自动触发维度评分。
- 其他角色（灵感超人、智能画家、文化达人、妙语奇兵）不触发单轮评分。
- 前端通过会话接口在页面生命周期内累计对话，用户退出或关闭页面时批量评分：
  - `POST /platform/session/start` 开始会话
  - `POST /platform/session/{session_id}/message` 追加消息
  - `POST /platform/session/{session_id}/end` 结束会话并后台评分

## 沟通约定
- 结论先行，再给理由。
- 需求模糊时先按最合理路径推进，并说明假设。
- 大改动前先给方案，用户确认后再动手。
- 每次实现完整的小单元改动后都要自动commit，方便rollback。
