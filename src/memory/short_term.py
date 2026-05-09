import os
import uuid
import aiosqlite
from src.logging_config import setup_logging

logger = setup_logging()

# ChromaDB 导入可能因 onnxruntime 在 Windows 上崩溃，设为可选
_chromadb_available = False
try:
    from chromadb import PersistentClient
    _chromadb_available = True
except Exception as e:
    logger.warning("ChromaDB 不可用，语义搜索将降级为 SQLite LIKE", error=str(e))


class ShortTermMemory:
    def __init__(self, sqlite_path: str = "data/memory.db", chroma_path: str = "data/chroma"):
        self.sqlite_path = sqlite_path
        self.chroma_path = chroma_path
        self.db = None
        self.collection = None

    async def initialize(self):
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        self.db = await aiosqlite.connect(self.sqlite_path)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.db.commit()

        if _chromadb_available:
            try:
                chroma = PersistentClient(path=self.chroma_path)
                try:
                    self.collection = chroma.get_or_create_collection("learnagent_memory")
                except Exception:
                    self.collection = chroma.create_collection("learnagent_memory")
                logger.info("ShortTermMemory ChromaDB 初始化完成")
            except Exception as e:
                logger.warning("ChromaDB 初始化失败，语义搜索不可用", error=str(e))

        logger.info("ShortTermMemory 初始化完成")

    async def save(self, content: str):
        await self.db.execute("INSERT INTO memories (content) VALUES (?)", (content,))
        await self.db.commit()
        if self.collection is not None:
            try:
                self.collection.add(documents=[content], ids=[str(uuid.uuid4())])
            except Exception as e:
                logger.warning("ChromaDB save 失败", error=str(e))
        logger.debug("memory saved", length=len(content))

    async def search(self, query: str, limit: int = 3) -> list[str]:
        if self.collection is not None:
            try:
                results = self.collection.query(query_texts=[query], n_results=limit)
                docs = results.get("documents", [[]])[0]
                return docs
            except Exception as e:
                logger.warning("ChromaDB search 失败", error=str(e))
        # 降级：SQLite LIKE 搜索
        cursor = await self.db.execute(
            "SELECT content FROM memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

    async def list_recent(self, limit: int = 10) -> list[str]:
        cursor = await self.db.execute(
            "SELECT content FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]
