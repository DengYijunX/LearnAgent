"""Session 存储 —— JSONL 格式，每行一条记录，便于追加和恢复。

目录结构：
  {base_dir}/
    index.json          ← 会话元数据索引（id → {topic, intent, created_at, ...}）
    {session_id}.jsonl  ← 消息记录（每行一条 JSON）
"""

import json
import os
from datetime import datetime


class SessionStore:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    # ── 路径 ────────────────────────────────────────────────────────

    def _path(self, session_id: str) -> str:
        return os.path.join(self._base_dir, f"{session_id}.jsonl")

    def _index_path(self) -> str:
        return os.path.join(self._base_dir, "index.json")

    # ── 消息读写 ────────────────────────────────────────────────────

    def append_message(self, session_id: str, message: dict) -> None:
        with open(self._path(session_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")

    def get_messages(self, session_id: str) -> list[dict]:
        path = self._path(session_id)
        if not os.path.exists(path):
            return []
        messages = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return messages

    # ── 会话元数据持久化 ────────────────────────────────────────────

    def _load_index(self) -> dict:
        """加载会话元数据索引。"""
        path = self._index_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self, index: dict) -> None:
        with open(self._index_path(), "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def save_session_meta(self, session_id: str, meta: dict) -> None:
        """保存/更新单个会话的元数据。"""
        index = self._load_index()
        index[session_id] = {
            **index.get(session_id, {}),
            **meta,
            "updated_at": datetime.now().isoformat(),
        }
        self._save_index(index)

    def load_session_meta(self, session_id: str) -> dict | None:
        """加载单个会话的元数据。"""
        return self._load_index().get(session_id)

    def list_session_metas(self, *, skip_missing: bool = True) -> list[dict]:
        """列出所有会话元数据，按 updated_at 降序。

        skip_missing=True 时自动跳过 JSONL 文件已不存在的条目，
        并清理索引中的死条目。
        """
        index = self._load_index()
        stale = []
        metas = []
        for sid, meta in index.items():
            if skip_missing and not os.path.exists(self._path(sid)):
                stale.append(sid)
                continue
            metas.append({"id": sid, **meta})
        if stale:
            for sid in stale:
                index.pop(sid, None)
            self._save_index(index)
        metas.sort(key=lambda m: m.get("updated_at", ""), reverse=True)
        return metas

    def delete_session(self, session_id: str) -> None:
        """删除会话的元数据和消息文件。"""
        # 删除索引
        index = self._load_index()
        index.pop(session_id, None)
        self._save_index(index)
        # 删除消息文件
        try:
            os.remove(self._path(session_id))
        except OSError:
            pass

    def migrate_orphan_files(self) -> int:
        """扫描没有索引条目的 JSONL 文件，自动补全元数据。返回迁移数量。"""
        index = self._load_index()
        migrated = 0
        try:
            filenames = os.listdir(self._base_dir)
        except OSError:
            return 0

        for name in filenames:
            if not name.endswith(".jsonl"):
                continue
            sid = name[:-6]  # 去掉 .jsonl 后缀
            if sid in index:
                continue  # 已有索引，跳过

            # 从 JSONL 提取元数据
            messages = self.get_messages(sid)
            if not messages:
                # 空文件，直接补一个最小索引，以免下次重复扫描
                index[sid] = {
                    "topic": None,
                    "intent": "chat",
                    "created_at": datetime.now().isoformat(),
                    "permission_mode": "default",
                    "message_count": 0,
                    "first_message": "",
                    "todos": [],
                    "updated_at": datetime.now().isoformat(),
                }
                migrated += 1
                continue

            # 找第一条用户消息
            first_user = ""
            for m in messages:
                if m.get("role") == "user" and m.get("content"):
                    first_user = str(m["content"])[:100]
                    break

            # 找最后一条消息的时间戳
            last_ts = None
            for m in reversed(messages):
                ts = m.get("timestamp")
                if ts:
                    last_ts = ts
                    break

            # 用文件修改时间作为 fallback
            try:
                file_mtime = datetime.fromtimestamp(
                    os.path.getmtime(self._path(sid))
                ).isoformat()
            except OSError:
                file_mtime = datetime.now().isoformat()

            created_at = last_ts if last_ts else file_mtime
            updated_at = file_mtime

            # 从第一条用户消息猜测 topic（取前 30 个字符）
            topic = first_user[:30] if first_user else None

            index[sid] = {
                "topic": topic,
                "intent": "chat",
                "created_at": created_at,
                "permission_mode": "default",
                "message_count": len(messages),
                "first_message": first_user,
                "todos": [],
                "updated_at": updated_at,
            }
            migrated += 1

        if migrated:
            self._save_index(index)
        return migrated
