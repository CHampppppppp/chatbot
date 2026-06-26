# 电脑博士资源推荐强制评分弹窗 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在「电脑博士」角色下，学生点击任意资源链接时弹出已有 1-5 星评分弹窗；评分提交后自动关闭弹窗；链接本身不被拦截，仍在新标签页打开；评分数据复用现有 `POST /records/add` 埋点。

**Architecture:** 在 `Chatbot/components/Chat.vue` 的 markdown-it 渲染阶段，根据 `currentRole === 'computerDoctor'` 给链接注入识别属性；在 `Chatbot/pages/index.vue` 通过事件委托捕获点击并弹出 `<dialog ref="ResourceRate">`；提交时复用 `handleRate` + `records(7, {...})`。后端无改动。

**Tech Stack:** Nuxt 3 / Vue 3, markdown-it, DaisyUI `<dialog>`, TypeScript (optional), existing FastAPI `POST /records/add`

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `Chatbot/components/Chat.vue` | Modify | 根据当前角色给 markdown 链接注入 `class` / `data-resource-role` |
| `Chatbot/pages/index.vue` | Modify | 事件委托识别电脑博士资源链接，控制 `ResourceRate` 弹窗开关与数据提交 |

---

## Task 1: 在 Chat.vue 中给电脑博士链接注入识别属性

**Files:**
- Modify: `Chatbot/components/Chat.vue:207-219`
- Modify: `Chatbot/components/Chat.vue:257-258`

### Step 1: 修改 `link_open` 渲染规则

在 `md.renderer.rules.link_open` 中，给电脑博士角色的链接追加 `class` 和 `data-resource-role`。

```js
// Chatbot/components/Chat.vue
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const hrefIndex = tokens[idx].attrIndex("href");
  if (hrefIndex >= 0) {
    const href = tokens[idx].attrs[hrefIndex][1];
    if (!/^https?:\/\//i.test(href) && !/^mailto:/i.test(href)) {
      tokens[idx].attrs[hrefIndex][1] = "#";
      tokens[idx].attrPush(["onclick", "return false;"]);
    }
    tokens[idx].attrPush(["target", "_blank"]);
    tokens[idx].attrPush(["rel", "noopener noreferrer"]);

    // 电脑博士角色下的资源链接增加识别标记
    if (env?.role === "computerDoctor") {
      tokens[idx].attrPush(["class", "resource-link"]);
      tokens[idx].attrPush(["data-resource-role", "computerDoctor"]);
    }
  }
  return defaultLinkOpenRender(tokens, idx, options, env, self);
};
```

### Step 2: 渲染时传入 `env`

修改 `formatAssistantMessage`，让 `md.render` 携带当前角色信息。

```js
// Chatbot/components/Chat.vue
function formatAssistantMessage(value) {
  let normalized = String(value || "");

  normalized = normalized.replace(
    /<a\b[^>]*\bhref=["'](https?:\/\/[^"']+)["'][^>]*>([^<]*)<\/a>/gi,
    (match, url, text) => `[${text || url}](${url})`
  );

  normalized = normalized.replace(
    /!\[(ResourceVideoUrl|ResourceTextbook)]\(([^)]+)\)/gi,
    (match, type, target) => {
      const label = type === "ResourceVideoUrl" ? "视频资源" : "教材资源";
      return `[${label}](${target})`;
    }
  );

  normalized = normalized.replace(/<[^>]+>/g, "");

  // 传入 env，让 link_open 规则知道当前角色
  return md.render(normalized, { role: props.currentRole });
}
```

### Step 3: 本地验证渲染输出

临时在浏览器控制台或 Vue Devtools 中检查电脑博士消息里的 `<a>` 是否带有：

```html
<a href="..." target="_blank" rel="noopener noreferrer" class="resource-link" data-resource-role="computerDoctor">...</a>
```

并确认切换到其他角色时没有这两个属性。

### Step 4: Commit

```bash
cd /Users/champ/Documents/chatbot

git add Chatbot/components/Chat.vue
git commit -m "feat(chat): mark computerDoctor resource links for rating popup"
```

---

## Task 2: 在 index.vue 中捕获点击并弹出评分弹窗

**Files:**
- Modify: `Chatbot/pages/index.vue:971-994`

### Step 1: 改造 `handleClickResourceVideo` 为通用资源链接点击处理

将原函数扩展为同时支持旧逻辑（`#resource_video`）和新逻辑（电脑博士 resource-link）。

```js
// Chatbot/pages/index.vue
function handleClickResourceVideo(e) {
  // 新逻辑：电脑博士角色下的资源链接
  const resourceLink = e.target.closest('a.resource-link[data-resource-role="computerDoctor"]');
  if (resourceLink && currentRole.value === "computerDoctor") {
    resourceVideoTimer = Date.now();
    resourceVideoUrl.value = resourceLink.href;
    resourceTextBook.value = "";
    isImgRate.value = false;

    if (!ResourceRate.value.classList.contains("hidden")) {
      ResourceRate.value.classList.add("hidden");
    }
    ResourceRate.value.classList.remove("hidden");
    ResourceRate.value.showModal();
    return;
  }

  // 保留旧逻辑：点击 id="resource_video" 的视频链接
  if (e.target.id === "resource_video") {
    resourceVideoTimer = Date.now();
    setTimeout(() => {
      hasClickResourceVideo.value = true;
    }, 50);

    resourceVideoUrl.value = e.target.href;
    if (!ResourceRate.value.classList.contains("hidden")) {
      ResourceRate.value.classList.add("hidden");
    }
  }
}
```

### Step 2: 保持 `handleRate` 不变，仅确保状态重置

当前实现已满足需求：

```js
async function handleRate(event) {
  event.preventDefault();
  ResourceRate.value.close();
  ResourceRate.value.classList.add("hidden");

  const type = isImgRate.value ? 9 : 7;
  await records(type, {
    name: "资源评分",
    videoUrl: resourceVideoUrl.value,
    text_book: resourceTextBook.value,
    rate: resourceRate.value,
    time: resourceVideoTimer,
  });

  isImgRate.value = false;
  resourceRate.value = 5;
}
```

无需修改。

### Step 3: 手动验证点击行为

启动本地开发环境：

```bash
cd /Users/champ/Documents/chatbot
./dev.sh
```

在电脑博士角色下发送一条会让 AI 返回链接的消息（例如“推荐一个 Python 学习网站”），点击链接后确认：

1. 链接在新标签页打开。
2. 原页面立即弹出「你觉得推荐的资源怎么样？」评分弹窗。
3. 弹窗无法通过点击外部关闭。
4. 选择 1-5 星并提交后弹窗自动关闭。
5. 切换到校园精灵等其他角色，点击链接不弹窗。

### Step 4: Commit

```bash
cd /Users/champ/Documents/chatbot

git add Chatbot/pages/index.vue
git commit -m "feat(chat): show resource rating popup for computerDoctor links"
```

---

## Task 3: 处理评分提交失败时的弹窗关闭

**Files:**
- Modify: `Chatbot/pages/index.vue:996-1014`

### Step 1: 给 `handleRate` 增加 try/finally

确保即使 `records` 接口失败也不会把用户卡在弹窗里。

```js
async function handleRate(event) {
  event.preventDefault();
  ResourceRate.value.close();
  ResourceRate.value.classList.add("hidden");

  const type = isImgRate.value ? 9 : 7;
  try {
    await records(type, {
      name: "资源评分",
      videoUrl: resourceVideoUrl.value,
      text_book: resourceTextBook.value,
      rate: resourceRate.value,
      time: resourceVideoTimer,
    });
  } catch (error) {
    console.error("资源评分提交失败:", error);
    // 可选：触发轻提示（若项目已有 toast 工具）
  } finally {
    isImgRate.value = false;
    resourceRate.value = 5;
  }
}
```

### Step 2: 本地模拟失败

可临时把 `records` 调用中的 URL 改错或断网，验证弹窗仍会关闭、页面不卡住。

### Step 3: Commit

```bash
cd /Users/champ/Documents/chatbot

git add Chatbot/pages/index.vue
git commit -m "fix(chat): ensure rating dialog closes even if submission fails"
```

---

## Self-Review

### Spec coverage

| 设计需求 | 对应任务 |
|---|---|
| 电脑博士角色链接注入识别标记 | Task 1 |
| 点击链接不拦截 URL，在新标签页打开 | Task 2（不调用 `preventDefault`） |
| 弹窗强制评分，无取消按钮 | Task 2（复用已有 `closedby="none"` dialog） |
| 1-5 星，默认 5 星 | Task 2（复用现有 `resourceRate = 5` 弹窗） |
| 提交后自动关闭弹窗 | Task 2 / Task 3（`ResourceRate.value.close()`） |
| 复用 `POST /records/add`，`type=7` | Task 2（`handleRate` 中 `isImgRate ? 9 : 7`） |
| 失败时弹窗也关闭 | Task 3 |
| 其他角色不弹窗 | Task 2（`currentRole.value === "computerDoctor"` 判断） |

### Placeholder scan

- 无 TBD / TODO。
- 所有代码块为可直接替换的完整代码。
- 命令和提交信息完整。

### Type consistency

- `props.currentRole` 在 `Chat.vue` 中为 `String` 类型，与 `"computerDoctor"` 字符串比较一致。
- `resourceVideoUrl` / `resourceTextBook` / `resourceRate` / `isImgRate` 复用 `index.vue` 已有变量，无新增命名冲突。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-26-computer-doctor-resource-rating-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
