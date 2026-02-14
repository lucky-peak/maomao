# Maomao - AI 编码知识库系统

一套 **本地化、可控、可演进** 的 AI 编码知识库系统，解决 AI 不理解旧代码、忽略私域规范、破坏向后兼容等问题。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        知识源 (可扩展)                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   SiyuanSource  │  LocalDocSource │  自定义 Source...            │
│   (思源笔记)     │  (本地文档)      │  (Notion/Obsidian/...)       │
└────────┬────────┴────────┬────────┴─────────────────────────────┘
         │                 │
         ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      分块器 (可扩展)                              │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ MarkdownChunker │   TextChunker   │  自定义 Chunker...           │
│  (按标题分块)     │  (按段落分块)    │  (代码/表格/...)              │
└────────┬────────┴────────┬────────┴────────────────────────────┘
         │                 │
         ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Python Ingestion Pipeline                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  解析     │→ │  分块     │→ │ 向量化   │→ │  存储     │        │
│  │  Source  │  │ Chunker  │  │ Ollama   │  │ Qdrant   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server (TypeScript)                       │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │search_global_knowledge│  │search_project_knowledge│            │
│  │  (通用编程知识)       │  │  (项目特定知识)       │              │
│  └─────────────────────┘  └─────────────────────┘               │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │search_all_knowledge │  │  knowledge_status   │               │
│  │  (综合搜索)          │  │  (知识库状态)        │               │
│  └─────────────────────┘  └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Coding Agent (支持 MCP)                        │
│              Claude / Cursor / Trae / ...                        │
└─────────────────────────────────────────────────────────────────┘
```

## 特性

- **本地化**: 所有数据存储在本地，无需联网
- **可扩展**: 插件式知识源和分块器架构，轻松扩展
- **智能分块**: Markdown 按标题层级分块，搜索更精准
- **增量更新**: 基于内容 hash 的增量导入，避免重复处理
- **MCP 集成**: 通过 MCP 协议与 AI 编码工具无缝集成
- **知识分类**: 区分通用编程知识和项目特定知识，精准检索

## 快速开始

### 1. 安装依赖

```bash
# 安装 Python 包
pip install -e .

# 安装 MCP Server
cd mcp-server && npm install && npm run build
```

### 2. 启动服务

```bash
# 启动 Ollama (需要先安装 bge-m3 模型)
ollama pull bge-m3

# 启动 Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### 3. 配置知识源

创建 `maomao.json`:

```json
{
  "sources": [
    {
      "type": "siyuan",
      "enabled": true,
      "knowledge_scope": "global",
      "config": {
        "api_url": "http://127.0.0.1:6806",
        "token": "your-token",
        "box_id": "your-box-id"
      }
    },
    {
      "type": "local_doc",
      "enabled": true,
      "knowledge_scope": "project",
      "project_id": "my-project",
      "config": {
        "path": "/path/to/project/docs",
        "patterns": ["*.md", "*.txt"]
      }
    }
  ]
}
```

#### knowledge_scope 说明

知识源可以配置 `knowledge_scope` 来区分知识类型：

| 值 | 说明 | 适用场景 |
|---|------|---------|
| `global` | 通用编程知识，跨项目复用 | 编码规范、框架用法、设计模式、最佳实践 |
| `project` | 项目特定知识，仅当前项目相关 | 业务逻辑、架构决策、代码模式说明 |

配置项：
- `knowledge_scope`: 知识范围，`global` 或 `project`
- `project_id`: 项目标识（仅 `project` 范围需要），用于区分不同项目

### 4. 导入知识

```bash
# 全量导入
maomao ingest --full

# 增量导入
maomao ingest
```

### 5. 搜索测试

```bash
maomao search "变量命名规范"
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `maomao ingest` | 增量导入知识 |
| `maomao ingest --full` | 全量导入知识 |
| `maomao search <query>` | 搜索知识库 |
| `maomao status` | 查看知识库状态 |
| `maomao config` | 显示当前配置 |
| `maomao sources` | 列出可用知识源类型 |

## MCP Server 集成

### 配置 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "maomao": {
      "command": "node",
      "args": ["/path/to/maomao/mcp-server/dist/index.js"],
      "env": {
        "MAOMAO_PROJECT_ID": "my-project"
      }
    }
  }
}
```

> **注意**: `MAOMAO_PROJECT_ID` 环境变量可选。如果不设置，系统会自动从当前工作目录名推断 project_id。

### 可用工具

| 工具 | 说明 | 适用场景 |
|------|------|---------|
| `search_global_knowledge` | 搜索通用编程知识 | 线程池配置、日志规范、框架用法、设计模式 |
| `search_project_knowledge` | 搜索项目特定知识 | 业务流程、架构决策、代码模式说明 |
| `search_all_knowledge` | 同时搜索两类知识 | 需要综合参考时 |
| `knowledge_status` | 获取知识库状态 | 查看向量数量、当前 project_id |

### 工具使用示例

**搜索通用知识**：
```
问题: 如何正确配置线程池参数？
工具: search_global_knowledge
参数: { "query": "线程池参数配置最佳实践" }
```

**搜索项目知识**：
```
问题: 这个项目的 Controller 是什么模式？
工具: search_project_knowledge
参数: { "query": "Controller 模式 RPC HTTP" }
```

**综合搜索**：
```
问题: 需要参考通用最佳实践和项目特定实现
工具: search_all_knowledge
参数: { "query": "错误处理规范" }
```

## 核心设计

### 知识源 (Source)

知识源负责从不同来源获取原始内容。每个源可以指定默认的分块器类型。

```python
from maomao.sources.base import KnowledgeSource, SourceItem, SourceRegistry

@SourceRegistry.register
class MySource(KnowledgeSource):
    @classmethod
    def source_type(cls) -> str:
        return "my_source"
    
    @classmethod
    def from_config(cls, config: dict) -> "MySource":
        return cls(...)
    
    async def scan(self) -> list[SourceItem]:
        return [
            SourceItem(
                content="...",
                source_type=self.source_type(),
                source_path="...",
                source_id="...",
                chunker_type="markdown",  # 指定分块器类型
                metadata={...},
            )
        ]
    
    async def get_changes(self, state: dict) -> SourceChange:
        # 增量更新逻辑
        pass
    
    async def close(self) -> None:
        pass
```

### 分块器 (Chunker)

分块器负责将内容切分成适合向量化的片段。不同类型的内容使用不同的分块策略。

#### MarkdownChunker

按标题层级智能分块：
1. 优先按 `##` 二级标题划分
2. 如果块过长，按 `###` 三级标题划分
3. 最终降级为按段落分割

```python
from maomao.chunkers import MarkdownChunker

chunker = MarkdownChunker(
    max_chunk_size=1000,    # 最大块大小
    min_chunk_size=50,      # 最小块大小
    heading_levels=[2, 3],  # 按哪些标题级别分块
)

chunks = chunker.chunk(markdown_content, {"source": "..."})
# 每个块的 metadata 包含:
# - title: 标题文本
# - heading_level: 标题级别
# - heading_path: 标题路径 ["一级标题", "二级标题", ...]
```

#### TextChunker

通用文本分块，按段落分割并保持重叠：

```python
from maomao.chunkers import TextChunker

chunker = TextChunker(
    chunk_size=512,         # 目标块大小
    chunk_overlap=50,       # 块之间的重叠
    min_chunk_size=50,      # 最小块大小
)
```

#### 扩展新分块器

```python
from maomao.chunkers.base import Chunker, ChunkerRegistry

@ChunkerRegistry.register
class CodeChunker(Chunker):
    @classmethod
    def chunker_type(cls) -> str:
        return "code"
    
    @classmethod
    def from_config(cls, config: dict) -> "CodeChunker":
        return cls(language=config.get("language", "python"))
    
    def chunk(self, content: str, metadata: dict | None) -> list[Chunk]:
        # 按函数/类分块
        pass
```

### 数据流

```
SourceItem                    Chunk                      KnowledgeChunk
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│ content      │            │ content      │            │ content      │
│ source_type  │──Chunker──▶│ metadata     │──Pipeline─▶│ source_type  │
│ source_path  │            │ content_hash │            │ source_path  │
│ chunker_type │            └──────────────┘            │ embedding    │
│ metadata     │                                        └──────────────┘
└──────────────┘                                              │
                                                              ▼
                                                          Qdrant 存储
```

## 内置知识源

### SiyuanSource (思源笔记)

从思源笔记 API 获取文档内容，适合存储：
- 编码规范和最佳实践
- 项目架构文档
- 反模式和踩坑记录
- 业务领域知识

配置项：
- `api_url`: 思源笔记 API 地址
- `token`: API Token
- `box_id`: 笔记本 ID
- `root_block_id`: 根文档 ID（可选）
- `chunker_type`: 分块器类型，默认 `markdown`

### LocalDocSource (本地文档)

从本地文件系统读取文档，支持 `.md`, `.txt`, `.rst`, `.adoc` 等格式。

配置项：
- `path`: 文档目录路径
- `patterns`: 文件匹配模式
- `recursive`: 是否递归扫描
- `chunker_type`: 分块器类型，默认根据文件扩展名自动选择

文件扩展名与分块器映射：
- `.md`, `.markdown` → `markdown`
- `.txt`, `.rst`, `.adoc` → `text`

## 配置参考

### 环境变量

所有配置都可以通过环境变量设置，前缀为 `MAOMAO_`：

```bash
MAOMAO_OLLAMA__BASE_URL=http://127.0.0.1:11434
MAOMAO_QDRANT__HOST=127.0.0.1
MAOMAO_QDRANT__PORT=6333
```

### 完整配置

```json
{
  "sources": [
    {
      "type": "siyuan",
      "enabled": true,
      "knowledge_scope": "global",
      "config": {
        "api_url": "http://127.0.0.1:6806",
        "token": "your-token",
        "box_id": "your-box-id",
        "chunker_type": "markdown"
      }
    },
    {
      "type": "local_doc",
      "enabled": true,
      "knowledge_scope": "project",
      "project_id": "my-project",
      "config": {
        "path": "/path/to/project/docs",
        "patterns": ["*.md", "*.txt"],
        "recursive": true
      }
    }
  ],
  "ollama": {
    "base_url": "http://127.0.0.1:11434",
    "embedding_model": "bge-m3",
    "embedding_dim": 1024,
    "timeout": 120
  },
  "qdrant": {
    "host": "127.0.0.1",
    "port": 6333,
    "collection_name": "maomao_knowledge"
  },
  "chunk": {
    "chunk_size": 512,
    "chunk_overlap": 50,
    "min_chunk_size": 50
  },
  "incremental": {
    "enabled": true,
    "state_file": ".maomao/state.json"
  },
  "log_level": "INFO"
}
```

### MCP Server 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MAOMAO_QDRANT_HOST` | Qdrant 主机地址 | `127.0.0.1` |
| `MAOMAO_QDRANT_PORT` | Qdrant 端口 | `6333` |
| `MAOMAO_QDRANT_COLLECTION` | 集合名称 | `maomao_knowledge` |
| `MAOMAO_OLLAMA_BASE_URL` | Ollama API 地址 | `http://127.0.0.1:11434` |
| `MAOMAO_OLLAMA_MODEL` | 嵌入模型 | `bge-m3` |
| `MAOMAO_PROJECT_ID` | 项目标识 | 自动从目录名推断 |

## 测试

### 单元测试

```bash
# 运行 Python 单元测试
python -m pytest tests/ -v

# 排除 E2E 测试
python -m pytest tests/ -v -m "not e2e"

# 运行 TypeScript 测试
cd mcp-server && npm test
```

### 端到端测试

E2E 测试需要外部服务（Ollama、Qdrant），使用 Docker Compose 搭建测试环境：

```bash
# 运行 E2E 测试（自动启动/停止服务）
./scripts/run_e2e_tests.sh

# 或手动启动服务后运行
docker-compose -f docker-compose.test.yml up -d
python -m pytest tests/test_e2e.py -v -m e2e
docker-compose -f docker-compose.test.yml down -v
```

### 测试覆盖

| 测试类型 | 文件 | 覆盖内容 |
|---------|------|---------|
| 单元测试 | `tests/test_models.py` | 数据模型、枚举 |
| 单元测试 | `tests/test_config.py` | 配置类 |
| 单元测试 | `tests/test_sources.py` | 知识源基类、注册表 |
| 单元测试 | `tests/test_chunkers.py` | 分块器 |
| E2E 测试 | `tests/test_e2e.py` | 全量导入、增量导入、搜索 |

### 测试统计

| 类型 | 数量 |
|------|------|
| Python 单元测试 | 39 个 |
| Python E2E 测试 | 9 个 |
| TypeScript 测试 | 13 个 |
| **总计** | **61 个** |

## 变更日志

### 2026-02-14: knowledge_scope 功能

#### 新增功能

**知识分类搜索**：支持区分通用编程知识和项目特定知识

- 新增 `knowledge_scope` 字段：`global`（通用知识）或 `project`（项目知识）
- 新增 `project_id` 字段：用于区分不同项目的知识
- MCP 工具重构为三个专门的搜索工具：
  - `search_global_knowledge`：搜索通用编程知识
  - `search_project_knowledge`：搜索项目特定知识
  - `search_all_knowledge`：综合搜索

**自动检测 project_id**：MCP Server 启动时自动从当前工作目录名推断 project_id

#### 数据模型变更

```python
# KnowledgeChunk 新增字段
knowledge_scope: str = "global"  # "global" 或 "project"
project_id: str = ""             # 项目标识

# SourceConfig 新增字段
knowledge_scope: Literal["global", "project"] = "global"
project_id: str = ""
```

#### 配置示例

```json
{
  "sources": [
    {
      "type": "siyuan",
      "knowledge_scope": "global",
      "config": { ... }
    },
    {
      "type": "local_doc",
      "knowledge_scope": "project",
      "project_id": "my-project",
      "config": { ... }
    }
  ]
}
```

#### Bug 修复

- **增量导入删除检测**：修复 `LocalDocSource.get_changes` 中状态结构解析错误，导致无法检测删除文件的问题

## 项目结构

```
maomao/
├── src/maomao/              # Python 包
│   ├── sources/             # 知识源
│   │   ├── base.py          # 抽象基类和注册表
│   │   ├── siyuan.py        # 思源笔记源
│   │   └── local_doc.py     # 本地文档源
│   ├── chunkers/            # 分块器
│   │   ├── base.py          # 抽象基类和注册表
│   │   ├── markdown.py      # Markdown 分块器
│   │   └── text.py          # 文本分块器
│   ├── embeddings.py        # 向量化服务
│   ├── vectorstore.py       # 向量存储
│   ├── pipeline.py          # 导入流程
│   ├── state.py             # 状态管理
│   ├── config.py            # 配置
│   ├── models.py            # 数据模型
│   └── cli.py               # CLI 工具
├── mcp-server/              # MCP Server
│   ├── src/
│   │   ├── index.ts         # 入口
│   │   ├── services.ts      # 知识检索服务
│   │   ├── config.ts        # 配置
│   │   └── types.ts         # 类型定义
│   └── package.json
└── pyproject.toml
```

## License

MIT
