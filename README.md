# zcode-ask

一个 Skill：在 AI 编程 IDE（如 Trae）里，把问题转发给本机的 **ZCode CLI** 执行，回答回到当前对话，同时让这次问答出现在 **ZCode 桌面端的历史列表**里。

## 它解决什么问题

ZCode 的 CLI 和桌面端各自维护一套存储：

- CLI 侧有本地会话库，按工作目录记录会话；
- 桌面端历史读的是另一套任务索引库，只认特定 provider 且有创建时间戳的记录；
- 两者不共享数据，CLI 在终端里新建的会话**不会**自动出现在桌面端历史上。

本 Skill 在调用 CLI 之后，用同一个 session id 往桌面端索引库补一条记录，于是两边打通：额度走 ZCode、回答回到 IDE、历史留在桌面端。

## 安装

```bash
git clone <this-repo> ~/.trae-cn/skills/zcode-ask
chmod +x ~/.trae-cn/skills/zcode-ask/scripts/zcode-ask.sh
```

依赖：

- macOS + 已安装 ZCode 桌面端（CLI 随应用分发）
- `node`、`python3`
- ZCode 已登录：`zcode login`

## 使用

```bash
SKILL_DIR=~/.trae-cn/skills/zcode-ask
"$SKILL_DIR/scripts/zcode-ask.sh" "解释一下这段 SQL 为什么走不到索引"
"$SKILL_DIR/scripts/zcode-ask.sh" -w /abs/path/to/project -m plan "分析这个模块的耦合点"
"$SKILL_DIR/scripts/zcode-ask.sh" -n "换一个新会话重新问"
```

参数：

| 参数 | 说明 |
| --- | --- |
| `-w` | 工作目录（绝对路径），同时决定桌面端归到哪个项目下 |
| `-m` | 权限模式：`plan`（默认，只读）/ `edit` / `yolo` |
| `-n` | 强制新会话；默认在同一目录内延续上一次会话，支持多轮追问 |

重置某个目录的会话记忆：

```bash
python3 "$SKILL_DIR/scripts/_sync.py" reset /abs/path/to/project
```

## 流程

```
问题 → zcode -p（消耗账号额度、产生 session）
     → 用同一 session id 写入桌面端任务索引库
     → 回答文本回显到当前对话
```

关键点只有一个：**索引里的 task_id 必须与 CLI session id 完全一致**，否则桌面端点开是空会话。

## 已知限制

- **模型不可选**：单次问答模式没有切换模型的入口，实际模型由 CLI 登录的 provider 决定（脚本只做记录，不做设置）。
- **桌面端有列表缓存**：写入成功也可能需要重开 ZCode 才显示；判断方法是直接查索引库，记录在即成功。
- **依赖私有库结构**：直接写桌面端的 SQLite 属于非官方路径，ZCode 升级后字段变化可能导致同步失效——届时对照新结构改 `_sync.py` 的字段即可。
- **仅 macOS**：默认路径取自 macOS 应用包，其他平台可用 `ZCODE_APP` / `ZCODE_CLI` / `ZCODE_PROVIDER_CFG` 覆盖。

## 环境变量

| 变量 | 默认值 |
| --- | --- |
| `ZCODE_APP` | `/Applications/ZCode.app` |
| `ZCODE_CLI` | `$ZCODE_APP/Contents/Resources/glm/zcode.cjs` |
| `ZCODE_PROVIDER_CFG` | `$ZCODE_APP/Contents/Resources/config/provider/zcode-builtin.json` |

## 免责声明

本项目未使用任何官方接口，通过读写 ZCode 本地数据库实现历史同步。请自行评估风险，升级后如失效属预期内的兼容性问题。

## License

MIT
