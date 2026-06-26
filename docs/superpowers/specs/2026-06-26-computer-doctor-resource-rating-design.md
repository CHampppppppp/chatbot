# 电脑博士资源推荐强制评分弹窗设计

## 背景

在「电脑博士」角色中，AI 会向学生推荐学习资源（视频、教材、网页链接等）。目前这些资源以普通 markdown 链接形式展示，点击后直接在新标签页打开，缺少学生对资源质量的反馈通道。

## 目标

学生在「电脑博士」角色下点击任意资源链接时，页面弹出 1-5 星评分弹窗，强制学生对当前点击的资源进行评分；评分提交后弹窗自动关闭。链接本身的打开行为不被拦截，仍在新标签页正常打开。

## 已确认的需求

| 问题 | 确认结果 |
|---|---|
| 评分后是否打开链接 | 不做 URL 拦截，链接正常在新标签页打开，原页面保留弹窗 |
| 评分范围 | 1-5 星，默认 5 星 |
| 触发范围 | 「电脑博士」角色下的所有资源链接 |
| 数据保存 | 复用现有 `POST /records/add`，`type=7` 资源评分埋点 |
| 弹窗行为 | 弹窗无取消/关闭按钮，`closedby="none"`，必须评分后才能关闭 |

## 架构与数据流

1. 学生在「电脑博士」角色下点击聊天记录中的任意 `<a>` 链接。
2. `Chatbot/components/Chat.vue` 在 `markdown-it` 渲染阶段，根据当前角色 `currentRole === 'computerDoctor'` 给链接注入 `class="resource-link" data-resource-role="computerDoctor"`。
3. `Chatbot/pages/index.vue` 在聊天容器上监听点击，通过 `e.target.closest('.resource-link[data-resource-role="computerDoctor"]')` 识别目标。
4. 命中后弹出已有 `<dialog ref="ResourceRate">` 评分弹窗；不调用 `e.preventDefault()`，链接按原样在新标签页打开。
5. 用户选择 1-5 星并提交，调用 `records(7, {...})`（`POST /records/add`，`type=7`），成功后自动关闭弹窗。

## 组件改动

### Chatbot/components/Chat.vue

- 在 `formatAssistantMessage` 调用 `md.render(normalized)` 时，传入 `{ role: currentRole.value }` 作为 `env`。
- 在 `md.renderer.rules.link_open` 里追加：

```js
if (env?.role === 'computerDoctor') {
  tokens[idx].attrPush(['class', 'resource-link']);
  tokens[idx].attrPush(['data-resource-role', 'computerDoctor']);
}
```

- 保持现有 `target="_blank" rel="noopener noreferrer"` 不变。

### Chatbot/pages/index.vue

- 在聊天容器点击处理中（复用或扩展 `handleClickResourceVideo`）：
  - 通过 `closest` 查找带 `.resource-link[data-resource-role="computerDoctor"]` 的 `<a>`。
  - 若命中：
    - 不调用 `e.preventDefault()`。
    - 记录 `resourceVideoUrl.value = link.href`。
    - 设置 `isImgRate.value = false`。
    - 调用 `ResourceRate.value.showModal()` 显示弹窗。
- `handleRate` 提交评分后：
  - 调用 `ResourceRate.value.close()` 自动关闭弹窗。
  - 重置 `resourceRate.value = 5`、`isImgRate.value = false`。
  - 不主动打开链接（链接已由浏览器默认行为在新标签页打开）。

## 后端接口

复用现有 `POST /records/add`（`ChatbotApi/api/records.py`），`type=7` 表示资源评分。

提交的 `meta` 示例：

```json
{
  "name": "资源评分",
  "videoUrl": "https://example.com/resource",
  "text_book": "",
  "rate": 5,
  "time": 0
}
```

后端无需新增接口或表结构。

## 错误处理

- 若 `records(7, ...)` 请求失败：
  - 仍然关闭弹窗，避免阻塞用户。
  - 可选：通过统一 toast / 轻提示显示「评分提交失败，请重试」。
- 若点击时未能识别链接：
  - 保持默认链接行为，不弹窗。
- 弹窗关闭后重置状态，避免影响下次评分。

## 测试与边界情况

1. 电脑博士消息里的普通 markdown 链接、`<a>` HTML 标签转换后的链接都能正确触发弹窗。
2. 切换到其他角色（校园精灵、灵感超人等）时，点击链接不弹窗。
3. 连续点击多个资源链接时，每次都能正确记录不同 URL 并弹出评分。
4. 用户未改选星数直接提交，默认按 5 星记录。
5. 网络异常时弹窗关闭，页面不卡住。
6. `processResource` 替换后的裸 URL 仍能被 markdown-it 渲染成带识别 class 的链接。
7. 聊天消息滚动或重新渲染后，事件委托仍然有效。

## 实现计划下一步

本设计确认后，使用 `writing-plans` skill 生成详细实施步骤。
