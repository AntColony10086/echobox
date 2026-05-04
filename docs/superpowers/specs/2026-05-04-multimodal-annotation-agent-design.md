---
title: 多模态智能标注 Agent 平台 —— 设计文档
date: 2026-05-04
status: approved
authors: ant
---

# 多模态智能标注 Agent 平台 —— 设计文档

## 1. 概述

本文档定义一个面向研究课题的**智能图像标注平台**的 v1 设计。平台基于 LangGraph 编排的 Agent 工作流完成对话式数据集 setup（扫描、整理、切分、标签、格式），并在 Web UI 中以 GECO2（基于 SAM2 的 exemplar-based 检测）为推理引擎，让用户通过"画一框出多框"的交互完成 bbox 标注。所有能力同时通过 MCP 协议暴露，供其他课题/agent 复用。

平台目标 OSS 开源发布，强调代码整洁、第一性原理、笔记本可跑。

### 1.1 解决的核心痛点

- **标注成本高**：用户每张图只需画一个示例框，GECO2 自动产出该类的所有相似框，人工只做 accept / 微调
- **零样本能力弱**：v1 暂不正面解决（不引入 Qwen-VL）；架构留好接口供后续接入

### 1.2 非目标（v1 显式不做）

- 像素级 mask / polygon 标注（GECO2 返回 bbox，v1 只画 bbox）
- 视频标注、3D 点云、关键点
- 多用户协作 / 权限管理
- 生产级部署（Docker、K8s、负载均衡）—— OSS 用户自部署
- Qwen-VL 集成（架构留位，v2 加）
- 撤销/重做（v2）
- 主动学习采样建议（v2）

## 2. 关键设计决策（来自 brainstorming）

| # | 决策 | 选项 | 理由 |
|---|---|---|---|
| Q1 | 输出格式 | Agent 自然语言决定（COCO/YOLO/VOC/LS-JSON 全支持） | 课题需求多样 |
| Q2 | 主入口 | Web UI 优先；MCP + CLI 次要 | 强人机交互 |
| Q3 | 模型部署 | exemplar 检测器后端可换（默认 GECO2/SAM2 本地）；VLM 槽位空 | 笔记本可跑；为 v2 留位 |
| Q4 | Agent 拓扑 | Planner + Critic 工具调用循环（LangGraph） | 灵活、可扩 |
| Q5 | MCP 范围 | 简单封装平台能力，不过度设计消费方层级 | 聚焦工程目标 |
| Q6 | 标注 UI | 自研（不包裹 Label Studio） | 包裹 LS 集成成本反而更高 |
| Q7 | (废止) | LS 取消 | 同 Q6 |
| Q8 | (废止) | LS 集成模式取消 | 同 Q6 |
| Q9 | GECO2 接口 | 单类 exemplar；多类靠工程层循环调用 | GECO2 仓库本身限制 |
| Q10 | Qwen-VL 角色 | v1 全不要，v2 再加 | 简化 |
| Q11 | Setup UI | 结构化卡片 + 聊天侧栏 | 一目了然 + 自然语言改 |
| Q12 | LLM 提供方 | OpenAI 兼容接口，默认 DashScope qwen-plus | 国内课题 0 摩擦 |
| Q13 | 标签集编辑 | Phase 2 可加，不可改/删 | 实用 + 数据安全 |
| Arch | 进程拓扑 | 三进程切分（app + ml_backend + mcp_server）+ 前端 | 职责清晰 |
| Deploy | 部署 | 不用 Docker，honcho 直跑本地进程 | 研究环境零摩擦 |

GECO2 仓库：<https://github.com/jerpelhan/GECO2.git>（PyTorch + SAM2 backbone，单类 exemplar 检测/计数）。

## 3. 系统架构

### 3.1 进程拓扑（4 个进程 + 浏览器）

```
┌──────────────────────────────────────────────────────────────┐
│ 用户浏览器                                                    │
│  ├─ /setup     卡片 + 聊天侧栏（Phase 1）                    │
│  └─ /annotate  bbox 标注画布（Phase 2）                      │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
   ┌─────────────────────────────────────────┐
   │  app (FastAPI)         port 8000        │
   │  ├─ LangGraph chat agent                │
   │  ├─ setup 编排                          │
   │  ├─ 标注持久化（SQLite + SQLAlchemy）    │
   │  ├─ REST API（前端 / mcp_server 调用）   │
   │  ├─ DashScope 客户端                    │
   │  └─ ml_backend HTTP 客户端              │
   └─────────────┬───────────────────────────┘
                 │ HTTP /predict_similar
                 ▼
   ┌─────────────────────────────────────────┐
   │  ml_backend (FastAPI + GPU)  port 9090  │
   │  ├─ GECO2 模型加载（启动一次）           │
   │  └─ POST /predict_similar               │
   └─────────────────────────────────────────┘

   ┌─────────────────────────────────────────┐
   │  mcp_server (MCP stdio/SSE)             │
   │  3 工具: start_project / search / export│
   │  反向调 app HTTP                         │
   └─────────────────────────────────────────┘

   ┌─────────────────────────────────────────┐
   │  web (Vite dev server)  port 5173       │
   │  React + react-konva                    │
   └─────────────────────────────────────────┘
```

### 3.2 仓库结构

```
label/
├── README.md                  # 英文 quick start + 架构图
├── README_zh.md               # 中文同步
├── LICENSE                    # Apache-2.0
├── pyproject.toml             # uv workspace 根
├── uv.lock
├── Procfile                   # honcho 起 4 进程
├── Makefile                   # setup / dev / app / ml / mcp / web / test
├── .env.example
│
├── packages/
│   ├── app/
│   │   └── src/echobox_app/
│   │       ├── main.py
│   │       ├── api/
│   │       │   ├── projects.py
│   │       │   ├── images.py
│   │       │   ├── annotations.py
│   │       │   ├── chat.py             # SSE
│   │       │   └── exports.py
│   │       ├── agent/
│   │       │   ├── graph.py            # LangGraph 图定义
│   │       │   ├── state.py            # AgentState dataclass
│   │       │   └── nodes.py            # planner / critic / tool_executor
│   │       ├── tools/
│   │       │   ├── filesystem.py       # scan_folder, organize_images
│   │       │   ├── splits.py           # propose_split
│   │       │   ├── labels.py           # propose_labels (启发式)
│   │       │   └── project.py          # set_export_format, finalize_setup
│   │       ├── ml_client/              # ml_backend HTTP 薄封装
│   │       ├── llm/                    # OpenAI 兼容 LLM 工厂
│   │       ├── db/
│   │       │   ├── models.py           # SQLAlchemy
│   │       │   ├── session.py
│   │       │   └── migrations/         # Alembic
│   │       ├── domain/                 # 业务 dataclass
│   │       ├── exporters/
│   │       │   ├── coco.py
│   │       │   ├── yolo.py
│   │       │   ├── voc.py
│   │       │   └── ls_json.py
│   │       ├── errors.py
│   │       └── config.py
│   │
│   ├── ml_backend/
│   │   └── src/echobox_ml/
│   │       ├── main.py                 # FastAPI: POST /predict_similar
│   │       ├── geco2_runner.py         # 模型加载 + 推理
│   │       ├── geco2_vendor/           # GECO2 仓库 vendored 或 git submodule
│   │       ├── schemas.py              # Pydantic 请求/响应
│   │       ├── errors.py
│   │       └── config.py
│   │
│   └── mcp_server/
│       └── src/echobox_mcp/
│           ├── server.py               # MCP server 入口
│           ├── client.py               # 调 app 的 HTTP 客户端
│           ├── tools/
│           │   ├── start_project.py
│           │   ├── search_annotations.py
│           │   └── export_dataset.py
│           └── config.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── eslint.config.js
│   ├── prettier.config.js
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   ├── SetupPage.tsx
│       │   └── AnnotatePage.tsx
│       ├── components/
│       │   ├── cards/
│       │   │   ├── FolderCard.tsx
│       │   │   ├── ImageInventoryCard.tsx
│       │   │   ├── SplitCard.tsx
│       │   │   ├── LabelsCard.tsx
│       │   │   └── FormatCard.tsx
│       │   ├── ChatPanel.tsx
│       │   ├── canvas/
│       │   │   ├── ImageCanvas.tsx     # react-konva
│       │   │   ├── BBoxLayer.tsx
│       │   │   ├── BBoxItem.tsx
│       │   │   └── ExemplarTool.tsx
│       │   ├── annotate/
│       │   │   ├── ClassPicker.tsx
│       │   │   ├── ImageList.tsx
│       │   │   ├── Toolbar.tsx
│       │   │   └── SaveIndicator.tsx
│       │   └── ui/
│       ├── api/
│       ├── hooks/
│       └── types/
│
├── docs/
│   ├── architecture.md
│   ├── development.md
│   ├── api.md
│   ├── extending.md
│   ├── superpowers/specs/
│   └── images/
│
├── tests/
│   ├── app/
│   ├── ml_backend/
│   ├── mcp_server/
│   ├── e2e/
│   └── fixtures/
│       ├── images/
│       ├── llm_responses/
│       └── geco2_outputs/
│
├── scripts/
│   ├── setup.sh
│   ├── dev.sh
│   ├── stop.sh
│   └── download_geco2_weights.sh
│
├── .editorconfig
├── .gitignore
├── .gitattributes
├── .pre-commit-config.yaml
└── .github/workflows/
    ├── ci.yml
    ├── e2e.yml
    └── release.yml
```

### 3.3 Procfile

```
app:    uv run --package echobox-app uvicorn echobox_app.main:app --port 8000 --reload
ml:     uv run --package echobox-ml uvicorn echobox_ml.main:app --port 9090
mcp:    uv run --package echobox-mcp echobox-mcp serve
web:    npm --prefix frontend run dev
```

### 3.4 设计原则

- 单一职责：每包一进程一职责，独立 `pyproject.toml`，独立可发布
- uv workspace 管理 3 个 Python 包，共享 `uv.lock`
- 进程间靠 HTTP，不共享 Python 内存
- DB 单点：只 `app` 持久化；其他进程无状态
- 配置走 `.env` + Pydantic Settings；环境变量是事实唯一来源
- 拷贝不移动用户源数据；workspace 在 `.data/` 下，gitignored

## 4. Phase 1：对话式 Setup

### 4.1 AgentState

```python
@dataclass
class AgentState:
    project_id: str
    messages: list[Message]
    folder_path: str | None
    inventory: ImageInventory | None
    canonical_images: list[Image]
    splits: SplitConfig | None
    labels: list[str]
    export_format: Literal["coco","yolo","voc","ls_json"] | None
    status: Literal["draft","ready","annotating"]
    last_critic_errors: list[str]
```

每字段 1:1 对应一张前端卡片。

### 4.2 LangGraph 拓扑

```
   START
     │
     ▼
  ┌──────────┐    tool_call    ┌──────────────────┐
  │ planner  │ ──────────────▶ │  tool_executor   │
  │  (LLM)   │ ◀────────────── │  (mutate state)  │
  └────┬─────┘   tool_result   └──────────────────┘
       │
       │ finalize_request
       ▼
  ┌──────────┐    fail (errors)
  │  critic  │ ─────────────────────┐
  └────┬─────┘                       │
       │ ok                          ▼
       ▼                         (back to planner)
   END (status="ready")
```

- **Planner**：LLM function-calling，决定回 chat / 调工具 / 请求 finalize
- **Tool Executor**：跑工具，结果作为 ToolMessage 入 messages，回 planner
- **Critic**：仅 finalize 前跑，校验失败把错误以 system message 返 planner

### 4.3 工具列表（7 个）

| 工具 | 签名 | 作用 |
|---|---|---|
| `scan_folder` | `(path: str) -> ScanResult` | 递归扫，PIL 验证；返回有效/无效/格式分布/采样 |
| `organize_images` | `() -> OrganizeResult` | 拷贝有效图到 `<project>/data/image/00001.ext`，写 `mapping.json` |
| `propose_split` | `(train, val, test, seed) -> SplitResult` | 确定性切分，写 `splits` |
| `set_labels` | `(labels: list[str]) -> None` | 设标签，去重，校验 |
| `propose_labels` | `() -> list[str]` | 启发式：源是 `<class>/...` 子目录则建议；否则空，让 planner 问 |
| `set_export_format` | `(fmt) -> None` | 锁定导出格式 |
| `finalize_setup` | `() -> FinalizeResult` | 触发 critic；通过则 status=ready |

### 4.4 Critic 校验规则

1. `inventory.valid_count > 0`
2. `canonical_images` 已生成
3. `splits` 比例 ≈ 1.0；每张图都有归属
4. `labels` 非空，全部 `^[a-zA-Z0-9_\-]+$`
5. `export_format` 已选

### 4.5 用户与 Agent 的两条交互通路

**通路 A —— 聊天面板（agent-mediated）**
```
ChatPanel 输入 → POST /api/projects/{pid}/chat
  → append messages → 跑 LangGraph 一轮
  → SSE 推 (planner_thought / tool_call / tool_result / reply / state_update)
  → 前端 chat 滚动 + 卡片热刷
```

**通路 B —— 卡片直改（无 LLM 旁路）**
```
SplitCard 滑块改 → PATCH /api/projects/{pid}/splits
  → 直接改 state.splits
  → append SystemMessage "用户手动改 splits 为 70/15/15"
  → SSE 推 state_update（不调 LLM）
```

后续 chat 触发时 planner 会看到 SystemMessage，知道用户改过。

### 4.6 REST API（app → 前端）

```
POST   /api/projects                          创建 project
                                              body: {source_folder, name?, initial_labels?,
                                                     train_val_test?, export_format?}
GET    /api/projects/{pid}                    完整 AgentState
POST   /api/projects/{pid}/chat               SSE 流式
PATCH  /api/projects/{pid}/folder             手动设文件夹（触发 scan）
PATCH  /api/projects/{pid}/splits             手动改比例
POST   /api/projects/{pid}/labels             加单个标签 body: {name, color?}
DELETE /api/projects/{pid}/labels/{name}      删标签（仅 status=draft 允许；
                                              ready/annotating 返回 403）
PATCH  /api/projects/{pid}/format             手动选格式
POST   /api/projects/{pid}/finalize           点"开始标注"
```

### 4.7 Phase 1 → Phase 2 边界

`finalize` 通过 →
- DB Project.status 置 `READY`
- 不再追加 chat 消息（chat_messages 表里 Phase 1 全程已实时落库；finalize 后只读不写）
- 前端跳转 `/annotate?project_id=...`
- AnnotatePage 重拉项目数据

## 5. Phase 2：交互式标注

### 5.1 三栏布局

- **左 220px**：缩略图列表 + 每图标注计数 + 总进度（train/val/test 已标 / 总）
- **中央自适应**：react-konva 画布 + 上一张/下一张
- **右 280px**：当前类别选择 / 模式切换 / 操作按钮 / 保存指示

### 5.2 单图标注循环

```
状态 0 (Empty)
  打开图 N → GET /api/images/{id}/annotations → 渲染历史 bbox
  ↓
状态 1 (PickClass)
  右侧选当前类别（或加新类别）
  ↓
状态 2 (DrawExemplar)
  模式切到"画 exemplar"，鼠标拖出框
  POST /api/projects/{pid}/images/{iid}/predict-similar
    body: {label_id, exemplar_bbox}
  ↓
状态 3 (Pending Review)
  ml_backend 返回候选 bbox → DB 写入 source="geco2_pending"
  SSE 推前端 → 渲染虚线
  ↓
状态 4 (Adjust)
  对每个虚线 bbox：
    点击 → 选中
    A 键 → 接受 → PUT, source="geco2_accepted" → 实线
    Del → DELETE
    拖角/中心 → debounce 300ms PUT → source="user_edited"
  也可"全部接受"批量 PATCH
  ↓
状态 5 (Save Confirmed)
  每次成功 → SaveIndicator 显示 "已保存"
  ↓
回状态 1（标下一类）或翻页
```

### 5.3 视觉约定

- 实线 bbox = `source ∈ {user, geco2_accepted}`
- 虚线 bbox = `source = geco2_pending`
- 不同颜色 = 不同 label（HSL 等距分配，存 `Label.color`）
- 低 score（<0.5）颜色淡化提示用户重点审核

### 5.4 ml_backend HTTP 契约

```
POST /predict_similar  (port 9090)

请求：
{
  "image_path": "/abs/path/.data/projects/7/data/image/00012.jpg",
  "exemplar_bbox": [120, 340, 280, 460],
  "max_predictions": 200,
  "score_threshold": 0.25
}

响应（200）：
{
  "predictions": [
    {"bbox": [125, 100, 240, 200], "score": 0.94}
  ],
  "exemplar_count": 1,
  "image_size": [1920, 1080],
  "elapsed_ms": 1247
}

错误（4xx/5xx）：
{
  "error": "model_not_loaded"|"invalid_bbox"|"image_not_found"|"inference_failed",
  "detail": "...",
  "elapsed_ms": 12
}
```

要点：
- 文件路径而非字节流（同机文件共享）
- 像素坐标统一全栈
- ml_backend 启动时一次性加载 GECO2，每请求无状态
- 设备自检：`cuda → mps → cpu`

### 5.5 REST API（前端 → app，Phase 2）

```
GET    /api/projects/{pid}/images                          列表 + 进度统计
GET    /api/images/{iid}                                   单图详情
GET    /api/images/{iid}/annotations                       该图全部 bbox
POST   /api/projects/{pid}/images/{iid}/predict-similar    body: {label_id, exemplar_bbox}
PUT    /api/annotations/{aid}                              body: {x1,y1,x2,y2?, label_id?,
                                                                  source?, version}
PATCH  /api/projects/{pid}/images/{iid}/annotations/bulk   body: {action: "accept_all"|"reject_all"}
DELETE /api/annotations/{aid}
POST   /api/projects/{pid}/labels                          加新标签 body: {name, color?}
```

### 5.6 错误与边界

| 情况 | 处理 |
|---|---|
| GECO2 超时（>30s） | 前端 toast；候选不入 DB；可重试 |
| GECO2 返回 0 个 | toast "未找到相似目标"；进入"选择/编辑"模式 |
| ml_backend 挂 | app 重试 1 次；连续失败 503；前端禁用 GECO2 按钮 |
| 用户重画 exemplar | 删该图 source=pending 的全部，写新一批 |
| 拖动很快 | debounce 300ms PUT |
| 多 tab 同图 | 乐观锁 version；409 时前端拉最新 |

### 5.7 键盘快捷键

```
A         接受当前选中
D / Del   删除当前选中
E         切换"画 exemplar"
V         切换"选择/编辑"
1..9      切换类别（按 Label 顺序）
← / →     上一张 / 下一张
```

撤销/重做 v2 实现。

## 6. 数据模型

### 6.1 磁盘布局

```
.data/
├── projects.db                # SQLite，所有 project 共用
└── projects/
    └── {project_id}/
        ├── project.json       # 元数据快照
        ├── data/
        │   ├── image/
        │   │   ├── 00001.jpg
        │   │   └── ...
        │   ├── mapping.json   # canonical → 源路径
        │   └── splits.json    # canonical → train/val/test
        ├── exports/
        │   └── 2026-05-04T10-00-coco/
        └── chat/
            └── history.jsonl  # 聊天 append-only 备份
```

### 6.2 完整 DB Schema

#### `projects`
| 列 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | PK |
| name | TEXT | NOT NULL |
| workspace_path | TEXT | NOT NULL |
| source_folder | TEXT | NOT NULL |
| status | TEXT | CHECK in ('draft','ready','annotating','exported') |
| export_format | TEXT | NULL |
| train_ratio | REAL | DEFAULT 0.7 |
| val_ratio | REAL | DEFAULT 0.15 |
| test_ratio | REAL | DEFAULT 0.15 |
| split_seed | INTEGER | DEFAULT 42 |
| created_at, updated_at | DATETIME | NOT NULL |

#### `images`
| 列 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | PK |
| project_id | INTEGER | FK projects.id ON DELETE CASCADE |
| filename | TEXT | NOT NULL |
| abs_path | TEXT | NOT NULL |
| width, height | INTEGER | NOT NULL |
| split | TEXT | CHECK in ('train','val','test') |
| index_in_project | INTEGER | NOT NULL |
| source_path | TEXT | NOT NULL |
| created_at | DATETIME | NOT NULL |

索引：`(project_id, index_in_project)`、`(project_id, split)`

#### `labels`
| 列 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | PK |
| project_id | INTEGER | FK ON DELETE CASCADE |
| name | TEXT | NOT NULL |
| color | TEXT | NOT NULL |
| created_at | DATETIME | NOT NULL |

唯一：`(project_id, name)`

#### `annotations`
| 列 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | PK |
| image_id | INTEGER | FK images.id ON DELETE CASCADE |
| label_id | INTEGER | FK labels.id ON DELETE RESTRICT |
| x1, y1, x2, y2 | INTEGER | NOT NULL |
| score | REAL | NULL |
| source | TEXT | CHECK in ('user','geco2_pending','geco2_accepted','user_edited') |
| version | INTEGER | DEFAULT 1 |
| created_at, updated_at | DATETIME | NOT NULL |

索引：`image_id`、`label_id`

#### `chat_messages`
| 列 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | PK |
| project_id | INTEGER | FK ON DELETE CASCADE |
| role | TEXT | CHECK in ('user','assistant','tool','system') |
| content | TEXT | NOT NULL |
| tool_call_id | TEXT | NULL |
| tool_name | TEXT | NULL |
| metadata_json | TEXT | NULL |
| created_at | DATETIME | NOT NULL |

索引：`(project_id, created_at)`

#### `prediction_runs`
| 列 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | PK |
| project_id, image_id, label_id | INTEGER | FK |
| exemplar_x1, y1, x2, y2 | INTEGER | NOT NULL |
| n_predictions | INTEGER | NOT NULL |
| elapsed_ms | INTEGER | NOT NULL |
| error | TEXT | NULL |
| created_at | DATETIME | NOT NULL |

索引：`(project_id, created_at)`

### 6.3 文件 Schema

#### `mapping.json`
```json
{
  "version": 1,
  "created_at": "ISO-8601",
  "entries": [
    {"canonical": "00001.jpg", "source": "/orig/path/img1.jpg",
     "sha256": "...", "bytes": 245678}
  ]
}
```

#### `splits.json`
```json
{
  "version": 1,
  "seed": 42,
  "ratios": {"train": 0.7, "val": 0.15, "test": 0.15},
  "assignments": {"00001.jpg": "train", ...}
}
```

#### `project.json`
```json
{
  "id": 7,
  "name": "cracks-20260504",
  "source_folder": "/orig/folder",
  "status": "annotating",
  "labels": [{"name": "crack", "color": "#e63946"}],
  "export_format": "coco",
  "splits": {"train": 0.7, "val": 0.15, "test": 0.15, "seed": 42},
  "image_count": 247,
  "created_at": "...",
  "updated_at": "..."
}
```

### 6.4 导出格式

#### COCO（默认）
```
exports/{ts}-coco/
├── train.json     # 标准 COCO instances JSON
├── val.json
├── test.json
└── images/        # symlink to ../../data/image/
```

#### YOLO
```
exports/{ts}-yolo/
├── classes.txt
├── train/{images, labels}/
├── val/...
└── test/...
```

bbox 转归一化 `cx cy w h`，类别用 label index。

#### VOC
```
exports/{ts}-voc/
├── ImageSets/Main/{train,val,test}.txt
├── JPEGImages/
├── Annotations/{*.xml}
└── labels.txt
```

#### ls_json
```
exports/{ts}-ls_json/
├── train.json
├── val.json
└── test.json
```

仅导出 `source != geco2_pending` 的标注。

### 6.5 Migrations

Alembic 管理。`make db-upgrade` 跑 `alembic upgrade head`；首次起服务自动跑 head。

## 7. MCP 服务器

### 7.1 进程定位

`mcp_server` 是给外部 agent 的薄包装，不持有状态，所有请求转 HTTP 调 `app`。

启动：`uv run echobox-mcp serve --transport stdio`（或 `--transport sse --port 9100`）

Claude Desktop 配置示例：
```json
{
  "mcpServers": {
    "echobox": {
      "command": "uv",
      "args": ["run", "--package", "echobox-mcp", "echobox-mcp", "serve"],
      "env": {"ECHOBOX_APP_URL": "http://localhost:8000"}
    }
  }
}
```

### 7.2 工具 1：`start_annotation_project`

```python
@tool
def start_annotation_project(
    folder: str,
    name: str | None = None,
    initial_labels: list[str] | None = None,
    train_val_test: tuple[float, float, float] = (0.7, 0.15, 0.15),
    export_format: Literal["coco","yolo","voc","ls_json"] = "coco",
) -> StartProjectResult:
    """创建标注项目；返回 setup URL，让人在浏览器完成对话式 setup。"""
```

返回：
```json
{
  "project_id": 7,
  "name": "cracks-20260504",
  "setup_url": "http://localhost:5173/setup?project_id=7",
  "status": "draft",
  "image_count_pending_scan": null,
  "message": "..."
}
```

错误：`folder_not_found` / `folder_empty` / `folder_not_readable` / `app_unreachable`。

设计取舍：不做"全自动 setup"模式，因为 setup 本质是人机对话；命令行 agent 不应替人做决定。可选参数预填卡片，最终仍需人在浏览器点开始。

### 7.3 工具 2：`search_annotations`

```python
@tool
def search_annotations(
    project_id: int,
    label: str | None = None,
    source: Literal["user","geco2_accepted","user_edited","any"] = "any",
    split: Literal["train","val","test","any"] = "any",
    min_score: float | None = None,
    image_filename_glob: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> SearchAnnotationsResult:
    """检索标注，返回 annotation + 所属图上下文。"""
```

返回包含：`total`、`returned`、`items`、`facets`（按 label/split/source 聚合）。

### 7.4 工具 3：`export_dataset`

```python
@tool
def export_dataset(
    project_id: int,
    format: Literal["coco","yolo","voc","ls_json"] | None = None,
    include_pending: bool = False,
    splits: list[Literal["train","val","test"]] | None = None,
) -> ExportDatasetResult:
    """触发导出。"""
```

返回：`export_id`、`format`、`output_dir`、`files`、`stats`、`elapsed_ms`。

错误：`project_not_found` / `project_not_ready` / `format_unsupported` / `no_annotations`。

### 7.5 实现要点

- 工具 schema 用 Pydantic → JSON Schema 自动生成
- `AppClient` 是 `httpx.AsyncClient` 薄封装，统一超时与错误转换
- 错误返回 MCP `isError=True` 的 ToolResult，content 为结构化 JSON
- mcp_server 自身不重试

### 7.6 安全（v1）

- 仅本地：bind 127.0.0.1，无认证
- 多机部署：README 给"加 nginx + token 反代"指引

## 8. 横切关注点

### 8.1 配置

Pydantic Settings 分层：defaults → `.env` → 环境变量。每包独立 `config.py`。`.env.example` 含必填项；启动时 fail-fast。

关键配置：
- `ECHOBOX_APP_LLM_API_KEY`（必填）
- `ECHOBOX_APP_LLM_BASE_URL`（默认 DashScope）
- `ECHOBOX_APP_LLM_MODEL`（默认 `qwen-plus`）
- `ECHOBOX_ML_GECO2_WEIGHTS`（GECO2 权重路径）
- `ECHOBOX_ML_DEVICE`（`auto`/`cuda`/`mps`/`cpu`）

### 8.2 错误处理

类型化异常：
```python
class ArisError(Exception):
    code: str
    http_status: int
```

子类：`ProjectNotFound`、`MLBackendUnavailable`、`ValidationError` 等。FastAPI 全局 handler 转统一信封：
```json
{"error": {"code": "...", "message": "...", "detail": {...}}}
```

外部依赖处理：
| 依赖 | 重试 | 超时 | 失败行为 |
|---|---|---|---|
| LLM | 1 次指数退避 | 60s | `LLMUnavailable`，前端 chat 提示 |
| ml_backend | 1 次 | 30s | `MLBackendUnavailable`，前端禁 GECO2 |
| filesystem | 不重试 | n/a | 直接抛 |
| DB | 不重试 | n/a | SQLAlchemy 抛，handler 转 500 |

LangGraph 内部：tool 抛 `ArisError` → executor 转 `ToolMessage(error=...)` → planner 决定下一步。

### 8.3 日志

- `structlog`：dev pretty，prod JSON
- Request ID 中间件，跨服务通过 `X-Request-ID` 传递
- LangGraph 轨迹直接落 `chat_messages` 表
- v1 不引入 OpenTelemetry

### 8.4 测试策略

```
       ┌─────────┐
       │   E2E   │  2-3 Playwright 用例
       └─────────┘
      ┌──────────┐
      │Integration│  ~20 pytest（app + 真 DB + mock 外部）
      └──────────┘
   ┌────────────────┐
   │     Unit       │  80% 行覆盖
   └────────────────┘
```

- Unit：tools / exporters / domain / db.models
- Integration：FastAPI TestClient + 临时 SQLite + monkeypatch LLM/ml_client；LLM 用录回放 fixture
- E2E：Playwright，ml_backend stub 出固定 bbox（不依赖 GPU）
- Fixture：12 张小图 + 录制的 LLM 响应 + 录制的 GECO2 输出
- Coverage 目标：80% 总，关键模块 90%+

### 8.5 OSS Hygiene

根目录文件：
- `LICENSE`（Apache-2.0）
- `README.md` 英文 + `README_zh.md` 中文（同步）
- `CONTRIBUTING.md`、`CODE_OF_CONDUCT.md`（Contributor Covenant 2.1）
- `SECURITY.md`、`CHANGELOG.md`（Keep a Changelog）
- `.editorconfig`、`.gitignore`、`.gitattributes`、`.pre-commit-config.yaml`

代码风格：
- Python：`ruff format` + `ruff check` + `mypy --strict`，行宽 100
- TS：`prettier` + `eslint`（`@typescript-eslint/recommended`），行宽 100
- Pre-commit：format + lint + type（fast）

CI：
```
.github/workflows/
├── ci.yml          push/PR：lint + type + unit + integration（无 GPU）
├── e2e.yml         手动：Playwright
└── release.yml     tag：构建 wheels + 前端产物 → GitHub Release
```

矩阵：Python 3.11 + 3.12，Ubuntu + macOS。

版本：SemVer；`v0.x.x` 至接口稳定后进 `v1.0.0`；`setuptools-scm` 从 git tag 自动版本。

文档：
```
docs/
├── architecture.md
├── development.md
├── api.md
├── extending.md
├── superpowers/specs/
└── images/
```

发布前 checklist：
- [ ] LICENSE 头在所有 .py 第一行
- [ ] README 跑通"copy-paste 5 命令起整套"
- [ ] 不带 `.env`、token、模型权重
- [ ] `.data/` 完全 gitignored
- [ ] `make test` 全绿
- [ ] 一张架构图 + 一段 demo GIF（README 头部）

### 8.6 安全（v1）

- 默认 bind `127.0.0.1`
- API key 仅从 env 读，`SecretStr` 自动 mask
- 用户上传路径 normalize + 限制在 `data_dir` 子树（防 path traversal）
- Pydantic 校验全部 API 入参
- SQLAlchemy 全参数化，禁 raw SQL 拼接
- 不收集 telemetry

## 9. 未决问题与未来工作

v2 候选（按优先级）：
1. Qwen-VL 集成（解决"零样本能力弱"）：自动建议标签、Phase 2 候选 bbox 提示
2. 撤销/重做（命令模式 + 内存历史）
3. mask / polygon 标注（GECO2 输出 mask + 自研 polygon 编辑）
4. 主动学习采样建议（基于 GECO2 score 分布）
5. 多用户 / 权限（OIDC）
6. 视频帧标注

v1 范围内已知小问题（不阻塞发布）：
- Windows symlink 兼容性：导出时若 symlink 失败，fallback 到拷贝
- 大数据集（>10k 图）的 ImageList 性能：v1 全量加载；v2 改虚拟滚动

## 10. 附：完整 Phase 1 对话样本

```
用户：我想标注这个文件夹 /Users/me/datasets/cracks
agent[planner]：调 scan_folder("/Users/me/datasets/cracks")
agent[tool_executor]：返回 247 张有效图，3 张坏图，源是 source/{positive,negative}/...
agent[planner]：调 propose_labels() → ["positive", "negative"]
agent[reply]："找到 247 张可标注图（3 张损坏已跳过）。源文件夹按 positive/negative 分类，
              我建议标签集 ["positive", "negative"]，可以吗？同时要把图片整理到项目
              workspace 吗？"
用户：[在 LabelsCard 上手动改成 ["crack", "no_crack"]]
       [chat] "标签按我改的来。整理图片，验证集 20%。"
agent[planner]：organize_images()
agent[tool_executor]：247 → image/00001.jpg ... image/00247.jpg
agent[planner]：propose_split(train=0.7, val=0.2, test=0.1)
agent[planner]：set_export_format("coco")
agent[reply]："整理完成。Split 70/20/10。导出格式 COCO。准备好就点开始标注。"
用户：[点开始标注] → POST /finalize
agent[critic]：全过 → status="ready"
前端：跳 /annotate
```
