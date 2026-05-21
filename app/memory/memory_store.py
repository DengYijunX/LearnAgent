"""长期记忆存储 —— Markdown + YAML frontmatter 格式。"""

import os
import yaml


class MemoryStore:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        safe = name.replace("/", "_").replace("\\", "_")
        return os.path.join(self._base_dir, f"{safe}.md")

    def save(self, name: str, memory_type: str, description: str, body: str) -> str:
        frontmatter = {
            "name": name,
            "description": description,
            "type": memory_type,
        }
        yaml_header = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
        content = f"---\n{yaml_header}\n---\n\n{body}"
        path = self._path(name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def find(self, name: str) -> dict | None:
        path = self._path(name)
        if not os.path.exists(path):
            return None
        return self._parse_file(path)

    def list_by_type(self, memory_type: str) -> list[dict]:
        results = []
        for filename in os.listdir(self._base_dir):
            if not filename.endswith(".md"):
                continue
            path = os.path.join(self._base_dir, filename)
            try:
                entry = self._parse_file(path)
                if entry and entry.get("type") == memory_type:
                    results.append(entry)
            except Exception:
                continue
        return results

    def _parse_file(self, path: str) -> dict | None:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        try:
            meta = yaml.safe_load(parts[1].strip())
        except yaml.YAMLError:
            return None
        if not isinstance(meta, dict):
            return None
        return {
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "type": meta.get("type", ""),
            "body": parts[2].strip(),
        }
