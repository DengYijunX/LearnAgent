"""评估数据集：测试 query + 预期路由类型。"""

TEST_CASES = [
    {"query": "什么是RAG", "expected_route": "simple"},
    {"query": "解释向量数据库原理", "expected_route": "simple"},
    {"query": "Docker和Kubernetes的区别", "expected_route": "simple"},
    {"query": "帮我掌握FastAPI", "expected_route": "complex"},
    {"query": "我要学Redis", "expected_route": "complex"},
    {"query": "带我做一个小型agent项目", "expected_route": "complex"},
    {"query": "Python装饰器怎么用", "expected_route": "simple"},
    {"query": "LangGraph教程", "expected_route": "simple"},
    {"query": "教我学Rust，从零开始", "expected_route": "complex"},
    {"query": "什么是async/await", "expected_route": "simple"},
    {"query": "构建一个RAG系统", "expected_route": "complex"},
    {"query": "github copilot工作原理", "expected_route": "simple"},
]
