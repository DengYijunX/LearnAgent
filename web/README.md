# LearnAgent Web 前端

Vue 3 + TypeScript + Vite + Tailwind CSS 构建的 LearnAgent Web 界面。

## 技术栈

- **Vue 3** — Composition API + `<script setup>`
- **TypeScript** — 类型安全
- **Vite** — 开发与构建
- **Tailwind CSS** — 原子化样式
- **Pinia** — 状态管理
- **WebSocket** — 实时对话通道
- **marked + highlight.js** — Markdown 渲染 + 代码高亮
- **lucide-vue-next** — 图标库

## 开发

```bash
npm install
npm run dev        # http://localhost:5173
```

后端需同时运行：

```bash
python -m app.server --reload   # http://127.0.0.1:8000
```

## 构建

```bash
npm run build      # 输出到 dist/
```

生产模式下 FastAPI 会自动 serve `web/dist/` 静态文件，无需单独部署前端。

## 项目结构

```
src/
├── main.ts                      # 入口
├── App.vue                      # 根布局
├── api/                         # HTTP + WebSocket 客户端
│   ├── client.ts                #   REST API 封装
│   └── ws.ts                    #   WebSocket 连接管理
├── stores/                      # Pinia 状态
│   ├── session.ts               #   会话列表 / 当前会话
│   ├── chat.ts                  #   消息 / 权限 / 连接状态
│   └── context.ts               #   学习上下文（主题/计划/状态/记忆）
├── composables/                 # 组合式函数
│   ├── useWebSocket.ts          #   WebSocket 生命周期
│   └── useContextPanel.ts       #   上下文面板数据加载
├── components/
│   ├── chat/                    # 对话相关
│   │   ├── ChatPanel.vue        #   对话面板容器
│   │   ├── MessageList.vue      #   消息列表（自动滚动）
│   │   ├── MessageBubble.vue    #   单条消息气泡
│   │   ├── ChatInput.vue        #   输入框 + 发送
│   │   └── ToolCallCard.vue     #   工具调用卡片
│   ├── context/                 # 学习上下文面板
│   │   ├── LearningContextPanel.vue  # 面板容器
│   │   ├── CurrentTopicCard.vue      # 当前学习主题
│   │   ├── LearningPlanCard.vue      # 学习计划 / 任务
│   │   ├── RuntimeStatusCard.vue     # 运行中进程
│   │   ├── MemorySummaryCard.vue     # 长期记忆摘要
│   │   └── SystemStatusCard.vue      # 系统状态
│   ├── layout/                  # 布局
│   │   ├── AppSidebar.vue       #   侧边栏（会话列表）
│   │   └── AppHeader.vue        #   顶栏
│   └── common/                  # 通用组件
│       ├── PermissionModal.vue  #   权限确认弹窗
│       ├── ConfirmDialog.vue    #   确认对话框
│       ├── ToastViewport.vue    #   Toast 通知
│       └── StatusBadge.vue      #   状态标签
├── types/                       # TypeScript 类型
└── utils/                       # 工具函数
    └── markdown.ts              #   Markdown 渲染 + 安全过滤
```
