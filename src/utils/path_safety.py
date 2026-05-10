import os
from pathlib import Path


def safe_path(base_dir: str | Path, relative_path: str) -> Path:
    """校验路径不穿越 base_dir。防御 ../、绝对路径、软链接跳出。"""
    base = Path(base_dir).resolve()
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    target = (base / relative_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"路径穿越检测: {relative_path} 超出 {base}")
    return target


def safe_write(path: Path, content: str):
    """Atomic write：先写 .tmp → os.replace → 目标文件。"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
