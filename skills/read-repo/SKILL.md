---
name: read-repo
description: 阅读 GitHub 仓库并提取学习价值
when_to_use: 当用户输入 GitHub 仓库链接时使用
allowed-tools:
  - analyze_github_repo
  - search_web
  - read_url
  - learning_todo_write
argument-hint: <repo_url>
---

请按以下流程分析仓库 $ARGUMENTS：

1. 调用 analyze_github_repo 获取 README 和项目信息。
2. 如果 README 提到了关键概念或依赖，用 search_web 搜索补充资料。
3. 总结项目解决什么问题，适合什么场景。
4. 分析技术栈：语言、框架、关键依赖。
5. 拆解核心模块和它们的职责。
6. 提取 3-5 个可学习的设计点或工程实践。
7. 给出从看懂到能改的阅读顺序。
8. 建议一个可模仿的类似小项目。
9. 用 learning_todo_write 记录学习任务。
