# PM2 配置迁移 ✅

## Phases

1. ✅ 在项目根目录创建 `ecosystem.config.cjs`
   - ✅ 起草配置文件内容（前后端两个 app entry，参考用户提供的模板风格）
   - ✅ 验证内容正确（前后端路径、命令、日志路径合理）
2. ✅ 调整日志目录并验证
   - ✅ 确认根目录 `logs/` 已存在（已有 backend-err/out.log 和 frontend-err/out.log）
   - ✅ 检验日志路径可写（已有内容证明）
3. ✅ 处理旧的 `Chatbot/ecosystem.config.cjs`
   - ✅ 在文件头部添加注释说明已废弃，引导使用根目录版本（文件在会话前已从磁盘删除，git 表现为 `deleted`）
4. ✅ 更新 `AGENTS.md`
   - ✅ 在「本地开发」小节补充 PM2 启动/停止/日志查看方式
