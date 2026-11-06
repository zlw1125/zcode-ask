---
name: zcode-ask
description: 用本机 ZCode CLI 提问，并把这个会话同步进 ZCode 桌面端历史。当用户说“用 zcode 问一下”“让 zcode 分析/看一下”“换成 zcode 的模型回答”“用 zcode 额度跑”等，需要把问题转发给 ZCode 而不是自己回答时使用。
---

# ZCode 提问

把问题转发给本机 ZCode CLI 执行，结果回显到当前终端对话，同时在 ZCode 桌面端历史中生成一条可点开的会话。

## 何时使用

- 用户明确要求「用 zcode 问」「让 zcode 看看」「用 zcode 的额度」
- 用户希望回答出现在 ZCode 桌面端历史里
- 用户想对比 zcode 与当前模型对同一问题的结论

不适用：普通编码、需要宿主 IDE 自身工具链（MCP、浏览器、文件编辑）的任务。

## 用法

```bash
SKILL_DIR=~/.trae-cn/skills/zcode-ask
"$SKILL_DIR/scripts/zcode-ask.sh" [-w 工作目录] [-m plan|edit|yolo] [-n] "问题"
```

- `-w` 工作目录，默认当前目录。**必须用绝对路径**，它同时决定桌面端归到哪个项目下
- `-m` 权限模式，默认 `plan`（只读）。需要它改文件才用 `edit`/`yolo`
- `-n` 强制开新会话；默认在同一工作目录内延续上一次会话，实现多轮追问
- 重置某个目录的会话：`python3 "$SKILL_DIR/scripts/_sync.py" reset <工作目录>`

## 执行要点

1. 问题要完整自包含。CLI 是独立进程，看不到宿主对话的上下文；多轮追问依赖 `--resume` 延续同一 zcode 会话。
2. 脚本会自动完成三件事：调 `zcode -p` 提问、登记工作目录为 ZCode 项目、把 session 写入桌面端任务索引库。
3. 退出码非 0 时脚本不会同步索引，此时把错误原样反馈给用户，不要重试。
4. 桌面端历史刷新有缓存，新条目可能需要重开 ZCode 才显示——属于正常现象。

## 返回给用户

把 CLI 输出的回答原文转述（可整理格式，但不要改结论），并说明会话已同步到桌面端哪个项目下。若用户后续追问，默认沿用同一会话继续。

## 限制

- 单次问答模式（`-p`）没有模型切换入口，实际模型由 CLI 登录的 provider 决定，脚本只做记录
- 依赖 ZCode 已登录（OAuth 凭证在 `~/.zcode/v2/credentials.json`），凭证失效需重新 `zcode login`
- 直接写桌面端私有库属于非官方路径，ZCode 升级后字段结构变化可能导致同步失效，届时重跑一次验证即可
