#!/bin/bash
# 通过 zcode CLI 提问，并把该会话同步进 ZCode 桌面端历史。
# 用法: zcode-ask.sh [-w 工作目录] [-m plan|edit|yolo] [-n] "问题"
#   -n  强制新会话；默认在同一工作目录内延续上一次会话（多轮追问）
set -o pipefail

# ZCode 应用路径：默认 macOS 安装位置，可用环境变量覆盖
ZCODE_APP="${ZCODE_APP:-/Applications/ZCode.app}"
CLI="${ZCODE_CLI:-$ZCODE_APP/Contents/Resources/glm/zcode.cjs}"
PROVIDER_CFG="${ZCODE_PROVIDER_CFG:-$ZCODE_APP/Contents/Resources/config/provider/zcode-builtin.json}"

HERE="$(cd "$(dirname "$0")" && pwd)"
CWD="$PWD"
MODE="plan"
NEW=0
PROMPT=""

while [ $# -gt 0 ]; do
  case "$1" in
    -w) CWD="$2"; shift 2 ;;
    -m) MODE="$2"; shift 2 ;;
    -n) NEW=1; shift ;;
    -h|--help) sed -n '2,4p' "$0"; exit 0 ;;
    *) PROMPT="$1"; shift ;;
  esac
done
[ -z "$PROMPT" ] && { echo "缺少问题内容"; exit 2; }

SID="NEW"
[ $NEW -eq 0 ] && SID="$(python3 "$HERE/_sync.py" prepare "$CWD")"
START_MS=$(python3 -c 'import time;print(int(time.time()*1000))')

ARGS=(-p "$PROMPT" --cwd "$CWD" --mode "$MODE")
[ "$SID" != "NEW" ] && ARGS+=(--resume "$SID")

OUT=$(mktemp)
ZCODE_BUILTIN_PROVIDER_CONFIG_FILE="$PROVIDER_CFG" node "$CLI" "${ARGS[@]}" > "$OUT" 2>&1
CODE=$?

# 去掉启动横幅，只留模型回答
grep -v '^ZCode Built-in' "$OUT"
rm -f "$OUT"

if [ $CODE -ne 0 ]; then
  echo "[zcode 退出码 $CODE，未同步桌面端索引]"
  exit $CODE
fi

python3 "$HERE/_sync.py" finish "$CWD" "$START_MS" "$MODE" "$SID"
