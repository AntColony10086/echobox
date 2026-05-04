<p align="center">
  <img src="assets/logo/logo.svg" alt="echobox" width="320">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
  <a href="https://github.com/AntColony10086/echobox/stargazers"><img src="https://img.shields.io/github/stars/AntColony10086/echobox?style=social" alt="Stars"></a>
</p>

<p align="center"><b>One box → all the boxes.</b> · <b>画一框，框出全图。</b></p>

<p align="center">
  <img src="assets/screenshots/03-annotate.png" alt="annotation page" width="900">
</p>

---

## What it does · 核心能力

**EN.** Echobox is a multimodal annotation agent with two workspaces in one app:
the **Workbench** for full agent-driven annotation, and the **Viewer** for a zero-dependency
offline preview of YOLO / point annotations. In the Workbench, you draw one bounding box
and an LLM-supervised exemplar detector ([GECO2](https://github.com/jerpelhan/GECO2),
backed by Meta's [SAM2](https://github.com/facebookresearch/sam2)) returns every similar
object in the image. You adjust, accept, save. A LangGraph agent handles the boring parts —
folder scanning, train/val/test split, label suggestions, and dataset export to COCO / YOLO /
Pascal VOC / Label Studio JSON. The same tools are exposed as MCP, so other agents
(Claude Code, Cursor, …) can drive annotation programmatically.

**中文.** Echobox 是一个多模态智能标注 Agent，一个 app 里两套工作区：
**工作台** 走 Agent 全流程标注，**预览** 是零依赖的离线 YOLO / 点标注预览器。
工作台里你只需画一个 bbox，LLM 监督下的 exemplar 检测器
（[GECO2](https://github.com/jerpelhan/GECO2)，底层用 Meta 的
[SAM2](https://github.com/facebookresearch/sam2)）就把图里所有相似目标都框出来。
你确认、调整、保存。LangGraph agent 负责扫描文件夹、切分 train/val/test、推荐标签、导出
COCO / YOLO / Pascal VOC / Label Studio JSON。同一套工具暴露为 MCP，其它 agent
（Claude Code、Cursor 等）也可以编程方式调用。

## Architecture · 架构

4 processes, all run locally — no Docker required. · 4 个进程纯本地运行，不需要 Docker。

```
Browser ──▶ frontend (Vite, port 5173)
                │
                ▼
          app (FastAPI, port 8000) ──▶ ml_backend (FastAPI + GPU, port 9090)
                │                              │
                │                              └─▶ GECO2 / SAM2 inference
                │
                ├─▶ OpenAI-compatible LLM (DashScope / MiniMax / OpenAI / …)
                └─▶ SQLite + filesystem workspace

mcp_server (stdio) ──▶ app HTTP — for Claude Code / Cursor consumers
```

## Quick start · 快速开始

```bash
# 1. Clone (with GECO2 submodule)
git clone --recurse-submodules https://github.com/AntColony10086/echobox
cd echobox

# 2. Configure your LLM (any OpenAI-compatible)
cp .env.example .env
# Edit .env — set ECHOBOX_APP_LLM_API_KEY, _BASE_URL, _MODEL

# 3. Install (uv handles Python; npm handles JS)
make setup

# 4. Get GECO2 weights
mkdir -p .data/weights
curl -L https://github.com/jerpelhan/GECO2/releases/download/v1.0/CNTQG_multitrain_ca44.pth \
  -o .data/weights/CNTQG_multitrain_ca44.pth

# 5. Initialize the database
make db-upgrade

# 6. Start everything (4 processes via honcho) and open the browser
make dev
# open http://localhost:5173
```

> **EN.** Need help on step 4? See [GECO2 releases](https://github.com/jerpelhan/GECO2/releases) for the latest weight URL and SHA256.
>
> **中文.** 第 4 步遇到问题，去 [GECO2 releases](https://github.com/jerpelhan/GECO2/releases) 查最新权重链接和 SHA256。

## Screenshots · 界面预览

<table align="center">
  <tr>
    <th align="center">Workbench · 工作台</th>
    <th align="center">Viewer · 预览</th>
  </tr>
  <tr>
    <td align="center"><img src="assets/screenshots/01-home.png" alt="workbench"></td>
    <td align="center"><img src="assets/screenshots/06-viewer.png" alt="viewer"></td>
  </tr>
  <tr>
    <th align="center">Setup · 配置</th>
    <th align="center">Export · 导出</th>
  </tr>
  <tr>
    <td align="center"><img src="assets/screenshots/02-setup-modal.png" alt="setup"></td>
    <td align="center"><img src="assets/screenshots/05-export.png" alt="export"></td>
  </tr>
  <tr>
    <th align="center">Annotate · 标注</th>
    <th align="center">Chat · 对话</th>
  </tr>
  <tr>
    <td align="center"><img src="assets/screenshots/03-annotate.png" alt="annotate"></td>
    <td align="center"><img src="assets/screenshots/04-chat.png" alt="chat"></td>
  </tr>
</table>

## MCP integration · MCP 集成

**EN.** Add this to your Claude Code / Cursor MCP config to call echobox tools from another agent:

```json
{
  "mcpServers": {
    "echobox": {
      "command": "uv",
      "args": ["run", "--package", "echobox-mcp", "echobox-mcp"],
      "cwd": "/path/to/echobox",
      "env": {
        "ECHOBOX_MCP_APP_URL": "http://localhost:8000"
      }
    }
  }
}
```

Available tools: `start_annotation_project`, `search_annotations`, `export_dataset`, plus all setup tools.

**中文.** 添加上面 JSON 到你的 Claude Code / Cursor MCP 配置即可让其它 agent 调用 echobox 工具。
工具清单：`start_annotation_project`、`search_annotations`、`export_dataset`，以及全部 setup 工具。

## How GECO2 works · GECO2 原理

**EN.** GECO2 (Generalist Exemplar-based COunting and detection) takes one user-drawn
exemplar and uses SAM2's image embedding to find every similar object. We use it as a
detector (not a counter): the predicted heatmap is binarised and converted to bboxes.
[Paper · jerpelhan/GECO2](https://github.com/jerpelhan/GECO2)

**中文.** GECO2 用一个用户画的 exemplar，借助 SAM2 的 image embedding，找出所有相似目标。
我们把它当作检测器用（不是计数器）：把预测的热力图二值化转成 bbox。
[论文 · jerpelhan/GECO2](https://github.com/jerpelhan/GECO2)

## Project layout · 工程结构

```
echobox/
├─ packages/
│  ├─ app/          (FastAPI + LangGraph agent + REST API)
│  ├─ ml_backend/   (FastAPI + GECO2/SAM2 inference)
│  └─ mcp_server/   (MCP stdio server, calls app HTTP)
├─ frontend/        (React + Vite + react-konva)
├─ docs/            (architecture, API, dev, extending)
├─ assets/          (logo, screenshots, social card)
├─ Procfile         (honcho config: 4 processes)
├─ Makefile         (dev shortcuts)
└─ .env.example
```

## Acknowledgements · 致谢

Echobox stands on the shoulders of these projects — credit and copyright belong to their
authors. · Echobox 完全基于以下项目，版权与归属归原作者所有：

- **GECO2** — [jerpelhan/GECO2](https://github.com/jerpelhan/GECO2) — exemplar-based detector
- **SAM2** — [facebookresearch/sam2](https://github.com/facebookresearch/sam2) — Meta AI
- **Deformable-DETR** — [fundamentalvision/Deformable-DETR](https://github.com/fundamentalvision/Deformable-DETR)
- **LangGraph** — [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
- **FastAPI** — [tiangolo/fastapi](https://github.com/tiangolo/fastapi)

See [`NOTICE`](NOTICE) for the full attribution list.

## License · 许可

Apache-2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Contributing · 参与开发

PRs welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). · PR 欢迎，详见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## Citation

If echobox helps your research, a citation is appreciated:

```bibtex
@software{echobox2026,
  title  = {echobox: Multimodal annotation agent with exemplar-based detection},
  author = {The echobox contributors},
  year   = {2026},
  url    = {https://github.com/AntColony10086/echobox}
}
```
