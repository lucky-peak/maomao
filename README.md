# Maomao - AI 编码知识库系统

一套 **本地化、可控、可演进** 的 AI 编码知识库系统，解决 AI 不理解旧代码、忽略私域规范、破坏向后兼容等问题。

## 特性

- **本地化**: 所有数据存储在本地，无需联网，保护隐私
- **一键安装**: 通过 pip/npm 快速安装，自动检测依赖
- **智能分块**: Markdown 按标题层级分块，搜索更精准
- **增量更新**: 基于内容 hash 的增量导入，避免重复处理
- **MCP 集成**: 通过 MCP 协议与 AI 编码工具无缝集成
- **知识分类**: 区分通用编程知识和项目特定知识，精准检索

## 环境要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.11+ | 核心运行环境 |
| Node.js | 18.0+ | MCP Server 运行环境（可选） |
| Ollama | 任意版本 | 向量化服务 |
| Qdrant | 任意版本 | 向量数据库 |
| Docker | 任意版本 | 运行 Qdrant（推荐） |

## 安装指南

### 方式一：快速安装（推荐）

使用快速启动脚本自动完成环境检测和配置：

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/maomao-ai/maomao/main/scripts/quickstart.sh | bash
```

### 方式二：标准安装

#### 1. 安装 Python 包

```bash
# 从 PyPI 安装（推荐）
pip install maomao

# 或从源码安装
pip install git+https://github.com/maomao-ai/maomao.git
```

#### 2. 安装 MCP Server（可选）

MCP Server 用于与 AI 编码助手（如 Claude Desktop）集成：

```bash
# 全局安装
npm install -g @maomao/mcp-server

# 或使用 npx 直接运行（无需安装）
npx @maomao/mcp-server
```

#### 3. 安装外部依赖

**Ollama**（向量化服务）：

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# 下载 BGE-M3 模型
ollama pull bge-m3
```

**Qdrant**（向量数据库）：

```bash
# 使用 Docker（推荐）
docker run -d --name maomao-qdrant -p 6333:6333 qdrant/qdrant

# 或使用 Docker Compose
# 创建 docker-compose.yml:
# services:
#   qdrant:
#     image: qdrant/qdrant
#     ports:
#       - "6333:6333"
```

### 方式三：开发环境安装

```bash
# 克隆仓库
git clone https://github.com/maomao-ai/maomao.git
cd maomao

# 安装 Python 依赖
pip install -e ".[dev]"

# 安装 MCP Server 依赖
cd mcp-server && npm install && npm run build
```

### 验证安装

```bash
# 检查版本
maomao --version

# 运行环境检测
maomao setup --check

# 完整验证
maomao verify
```

## 快速开始

### 1. 初始化配置

```bash
# 交互式配置（推荐）
maomao init

# 或使用默认模板
maomao init --no-interactive
```

这将创建 `maomao.json` 配置文件。

### 2. 编辑配置文件

编辑 `maomao.json`，配置你的知识源：

```json
{
  "sources": [
    {
      "type": "local_doc",
      "enabled": true,
      "knowledge_scope": "project",
      "project_id": "my-project",
      "config": {
        "path": "/path/to/your/docs",
        "patterns": ["*.md", "*.txt"],
        "recursive": true
      }
    }
  ],
  "ollama": {
    "base_url": "http://127.0.0.1:11434",
    "embedding_model": "bge-m3",
    "embedding_dim": 1024
  },
  "qdrant": {
    "host": "127.0.0.1",
    "port": 6333,
    "collection_name": "maomao_knowledge"
  }
}
```

### 3. 验证配置

```bash
maomao validate
```

### 4. 导入知识

```bash
# 全量导入（首次使用）
maomao ingest --full

# 增量导入（后续更新）
maomao ingest
```

### 5. 搜索测试

```bash
maomao search "变量命名规范"
maomao search "错误处理最佳实践" -l 10
```

## CLI 命令参考

### 基础命令

| 命令 | 说明 |
|------|------|
| `maomao --version` | 显示版本信息 |
| `maomao --help` | 显示帮助信息 |

### 安装与配置

| 命令 | 说明 |
|------|------|
| `maomao setup` | 环境检测和初始化设置 |
| `maomao setup --check` | 仅检查依赖，不执行安装 |
| `maomao doctor` | 诊断系统问题，提供修复建议 |
| `maomao verify` | 验证安装完整性 |
| `maomao init` | 交互式创建配置文件 |
| `maomao init --no-interactive` | 使用默认模板创建配置 |
| `maomao validate` | 验证配置文件 |
| `maomao validate -c <path>` | 验证指定配置文件 |

### 知识管理

| 命令 | 说明 |
|------|------|
| `maomao ingest` | 增量导入知识 |
| `maomao ingest --full` | 全量导入知识 |
| `maomao search <query>` | 搜索知识库 |
| `maomao search <query> -l 10` | 限制返回结果数量 |
| `maomao search <query> -t siyuan` | 按来源类型过滤 |
| `maomao status` | 查看知识库状态 |
| `maomao config` | 显示当前配置 |
| `maomao sources` | 列出可用知识源类型 |

### 命令参数详解

#### `maomao search`

```bash
maomao search <query> [OPTIONS]

参数:
  query                搜索查询文本

选项:
  -l, --limit INT      返回结果数量，默认 5
  -t, --type TEXT      来源类型过滤（如 siyuan, local_doc）
```

#### `maomao ingest`

```bash
maomao ingest [OPTIONS]

选项:
  -f, --full           执行全量导入，重新处理所有知识源
```

## MCP Server 集成

### 配置 Claude Desktop

编辑配置文件：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "maomao": {
      "command": "maomao-mcp",
      "env": {
        "MAOMAO_PROJECT_ID": "my-project"
      }
    }
  }
}
```

或使用 Node.js 直接运行：

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

### 可用工具

| 工具 | 说明 | 适用场景 |
|------|------|---------|
| `search_global_knowledge` | 搜索通用编程知识 | 编码规范、框架用法、设计模式 |
| `search_project_knowledge` | 搜索项目特定知识 | 业务逻辑、架构决策、代码模式 |
| `search_all_knowledge` | 综合搜索 | 需要同时参考通用和项目知识 |
| `knowledge_status` | 获取知识库状态 | 查看向量数量、当前 project_id |

### MCP Server 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MAOMAO_QDRANT_HOST` | Qdrant 主机地址 | `127.0.0.1` |
| `MAOMAO_QDRANT_PORT` | Qdrant 端口 | `6333` |
| `MAOMAO_QDRANT_COLLECTION` | 集合名称 | `maomao_knowledge` |
| `MAOMAO_OLLAMA_BASE_URL` | Ollama API 地址 | `http://127.0.0.1:11434` |
| `MAOMAO_OLLAMA_MODEL` | 嵌入模型 | `bge-m3` |
| `MAOMAO_PROJECT_ID` | 项目标识 | 自动从目录名推断 |

## 配置参考

### knowledge_scope 说明

知识源可以配置 `knowledge_scope` 来区分知识类型：

| 值 | 说明 | 适用场景 |
|---|------|---------|
| `global` | 通用编程知识，跨项目复用 | 编码规范、框架用法、设计模式、最佳实践 |
| `project` | 项目特定知识，仅当前项目相关 | 业务逻辑、架构决策、代码模式说明 |

### 完整配置示例

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
        "root_block_id": ""
      }
    },
    {
      "type": "local_doc",
      "enabled": true,
      "knowledge_scope": "project",
      "project_id": "my-project",
      "config": {
        "path": "/path/to/project/docs",
        "patterns": ["*.md", "*.txt", "*.rst"],
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
    "collection_name": "maomao_knowledge",
    "prefer_grpc": false
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

### 环境变量配置

所有配置都可以通过环境变量设置，前缀为 `MAOMAO_`：

```bash
export MAOMAO_OLLAMA__BASE_URL=http://127.0.0.1:11434
export MAOMAO_QDRANT__HOST=127.0.0.1
export MAOMAO_QDRANT__PORT=6333
```

## 内置知识源

### SiyuanSource (思源笔记)

从思源笔记 API 获取文档内容。

配置项：
| 参数 | 说明 | 必填 |
|------|------|------|
| `api_url` | 思源笔记 API 地址 | 是 |
| `token` | API Token | 是 |
| `box_id` | 笔记本 ID | 是 |
| `root_block_id` | 根文档 ID | 否 |

### LocalDocSource (本地文档)

从本地文件系统读取文档。

配置项：
| 参数 | 说明 | 必填 |
|------|------|------|
| `path` | 文档目录路径 | 是 |
| `patterns` | 文件匹配模式 | 否（默认 `["*.md", "*.txt"]`） |
| `recursive` | 是否递归扫描 | 否（默认 `true`） |

支持的文件格式：
- `.md`, `.markdown` → Markdown 分块器
- `.txt`, `.rst`, `.adoc` → 文本分块器

## 注意事项

### 已知限制

1. **Python 版本**: 仅支持 Python 3.11 及以上版本
2. **嵌入模型**: 默认使用 BGE-M3，需要约 2GB 显存或内存
3. **并发限制**: Ollama 默认单线程处理，大批量导入可能较慢
4. **文件大小**: 单个文件建议不超过 10MB，大文件可能导致内存问题

### 常见问题

#### Q: 连接 Ollama 失败

```bash
# 检查 Ollama 是否运行
ollama list

# 如果未运行，启动服务
ollama serve
```

#### Q: 连接 Qdrant 失败

```bash
# 检查 Qdrant 容器状态
docker ps | grep qdrant

# 重启容器
docker restart maomao-qdrant

# 或重新创建
docker run -d --name maomao-qdrant -p 6333:6333 qdrant/qdrant
```

#### Q: BGE-M3 模型未找到

```bash
# 下载模型
ollama pull bge-m3

# 验证模型已安装
ollama list | grep bge-m3
```

#### Q: 配置文件未找到

```bash
# 检查配置文件位置
ls -la maomao.json

# 或创建新配置
maomao init
```

#### Q: 搜索结果不准确

1. 检查知识源是否正确配置
2. 确认已执行 `maomao ingest --full`
3. 尝试调整搜索查询关键词
4. 检查嵌入模型是否正确加载

### 性能优化建议

1. **使用 SSD**: Qdrant 数据存储在 SSD 上可提升搜索性能
2. **调整分块大小**: 根据文档特点调整 `chunk_size`，默认 512 字符
3. **批量导入**: 首次导入使用 `--full`，后续使用增量导入
4. **Docker 资源**: 为 Qdrant 容器分配足够的内存

```bash
# 为 Qdrant 分配更多资源
docker run -d --name maomao-qdrant \
  -p 6333:6333 \
  --memory=4g \
  --cpus=2 \
  qdrant/qdrant
```

5. **Ollama 并发**: 如需处理大量文档，可配置 Ollama 并发

```bash
# 设置 Ollama 并发数
export OLLAMA_NUM_PARALLEL=4
ollama serve
```

### 安全建议

1. **Token 保护**: 配置文件中的 token 等敏感信息不要提交到版本控制
2. **网络隔离**: Ollama 和 Qdrant 默认仅监听本地，生产环境注意网络安全
3. **数据备份**: 定期备份 Qdrant 数据目录

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
└────────┬────────┴────────┬────────┴─────────────────────────────┘
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

## 开发指南

### 运行测试

```bash
# 单元测试
python -m pytest tests/ -v -m "not e2e"

# E2E 测试（需要外部服务）
./scripts/run_e2e_tests.sh

# TypeScript 测试
cd mcp-server && npm test
```

### 代码检查

```bash
# Lint
python -m ruff check src/maomao/

# 类型检查
python -m mypy src/maomao/ --ignore-missing-imports
```

### 扩展知识源

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
        return [...]
    
    async def get_changes(self, state: dict) -> SourceChange:
        ...
    
    async def close(self) -> None:
        pass
```

### 扩展分块器

```python
from maomao.chunkers.base import Chunker, ChunkerRegistry

@ChunkerRegistry.register
class CodeChunker(Chunker):
    @classmethod
    def chunker_type(cls) -> str:
        return "code"
    
    @classmethod
    def from_config(cls, config: dict) -> "CodeChunker":
        return cls(...)
    
    def chunk(self, content: str, metadata: dict | None) -> list[Chunk]:
        ...
```

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
│   ├── dependency_checker.py # 依赖检测
│   └── cli.py               # CLI 工具
├── mcp-server/              # MCP Server
│   ├── src/
│   │   ├── index.ts         # 入口
│   │   ├── services.ts      # 知识检索服务
│   │   ├── config.ts        # 配置
│   │   └── types.ts         # 类型定义
│   └── package.json
├── scripts/
│   ├── quickstart.sh        # 快速启动脚本
│   └── run_e2e_tests.sh     # E2E 测试脚本
├── tests/                   # 测试目录
├── docs/                    # 文档目录
├── pyproject.toml           # Python 项目配置
└── LICENSE                  # MIT License
```

## License

MIT License - 详见 [LICENSE](LICENSE) 文件
