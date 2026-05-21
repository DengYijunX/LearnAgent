---
name: review-progress
description: 复盘最近学习内容，检查掌握程度
when_to_use: 当用户说"复盘"、"回顾"、"总结"、"复习"时使用
allowed-tools:
  - search_memory
  - learning_todo_write
argument-hint: <topic>
---

请按以下流程帮用户复盘 $ARGUMENTS：

1. 回顾用户最近学习过的主题（从记忆中读取）。
2. 让用户自评每个主题的掌握程度。
3. 针对薄弱点，用费曼技巧让用户用自己的话解释。
4. 指出需要加强的概念。
5. 给出下一阶段的学习建议。
6. 用 learning_todo_write 更新学习计划。
7. 鼓励用户，肯定学习成果。
