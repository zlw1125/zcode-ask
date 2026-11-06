#!/usr/bin/env python3
"""zcode-ask 的辅助脚本：维护多轮会话状态、登记项目、把会话同步进 ZCode 桌面端索引。"""
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path

HOME = Path.home()
TASKS_DB = HOME / ".zcode/v2/tasks-index.sqlite"
SESS_DB = HOME / ".zcode/cli/db/db.sqlite"
STATE = HOME / ".zcode/state/zcode-ask.json"


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def prepare(cwd):
    """返回可续接的 session id；没有则输出 NEW。"""
    sid = load_state().get(cwd)
    if not sid:
        print("NEW")
        return
    con = sqlite3.connect(f"file:{SESS_DB}?mode=ro", uri=True)
    try:
        ok = con.execute("select 1 from session where id=? and directory=?", (sid, cwd)).fetchone()
    finally:
        con.close()
    print(sid if ok else "NEW")


def ensure_project(con, cwd):
    row = con.execute("select project_id from project_roots where root_path=?", (cwd,)).fetchone()
    if row:
        return row[0]
    pid = str(uuid.uuid4())
    now = int(__import__("time").time() * 1000)
    pos = con.execute("select coalesce(min(position),0)-1 from projects").fetchone()[0]
    con.execute(
        "insert into projects (project_id,host_id,name,name_overridden,position,pinned,deleted,created_at,updated_at)"
        " values (?,?,?,?,?,?,?,?,?)",
        (pid, "local", os.path.basename(cwd.rstrip("/")) or cwd, 0, pos, 0, 0, now, now),
    )
    con.execute(
        "insert into project_roots (project_id,root_path,position,is_primary) values (?,?,?,?)",
        (pid, cwd, 0, 1),
    )
    return pid


def finish(cwd, start_ms, mode, sid):
    s = sqlite3.connect(f"file:{SESS_DB}?mode=ro", uri=True)
    s.row_factory = sqlite3.Row
    if sid and sid != "NEW":
        row = s.execute(
            "select id,directory,title,trace_id,time_created,time_updated,last_outcome from session where id=?",
            (sid,),
        ).fetchone()
    else:
        row = s.execute(
            "select id,directory,title,trace_id,time_created,time_updated,last_outcome from session"
            " where directory=? and time_created>=? order by time_created desc limit 1",
            (cwd, start_ms),
        ).fetchone()
    if not row:
        print("[未找到本次会话，跳过同步]")
        return
    sess = dict(row)

    model = "unknown"
    try:
        r = s.execute(
            "select data from session_entry where session_id=? and data like '%modelSelection%' limit 1",
            (sess["id"],),
        ).fetchone()
        if r:
            ms = json.loads(r["data"])["modelSelection"]
            model = f"{ms.get('providerId','')}/{ms.get('modelId','')}"
    except Exception:
        pass
    s.close()

    t = sqlite3.connect(TASKS_DB, timeout=10)
    t.row_factory = sqlite3.Row
    pid = ensure_project(t, cwd)
    meta = {
        "taskId": sess["id"],
        "traceId": sess["trace_id"] or "",
        "title": sess["title"],
        "workspacePath": cwd,
        "mode": mode,
    }
    data = dict(
        workspace_key=cwd, workspace_path=cwd, workspace_identity=None, task_id=sess["id"],
        title=sess["title"], task_status="completed", provider="glm", mode=mode, model=model,
        created_at=sess["time_created"], updated_at=sess["time_updated"],
        last_unread_at=sess["time_created"], pinned=0, archived=0, deleted=0, title_overridden=0,
        meta_json=json.dumps(meta, ensure_ascii=False), searchable_text=sess["title"], host_id="local",
        root_path=cwd, project_id=pid, cli_title=sess["title"], cli_title_source="generated",
        cli_created_at=sess["time_created"], cli_updated_at=sess["time_updated"],
        cli_last_outcome=(sess["last_outcome"] or "completed"), cli_deleted=0, handoff_pending=0,
    )
    cols = ",".join(data)
    ph = ",".join("?" * len(data))
    t.execute(f"insert or replace into tasks ({cols}) values ({ph})", list(data.values()))
    t.commit()
    t.close()

    st = load_state()
    st[cwd] = sess["id"]
    save_state(st)
    print(f"[已同步桌面端] session={sess['id']} title={sess['title']} model={model}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prepare":
        prepare(sys.argv[2])
    elif cmd == "finish":
        finish(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "NEW")
    elif cmd == "reset":
        st = load_state()
        st.pop(sys.argv[2], None)
        save_state(st)
        print("已重置会话")
