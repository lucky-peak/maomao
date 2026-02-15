# Maomao 软件分发优化方案

## 概述

本方案旨在优化 Maomao 知识库系统的分发流程，实现用户通过最少的操作步骤完成软件的安装和配置。

---

## 1. Python 包分发优化

### 1.1 当前状态分析

**现有配置** ([pyproject.toml](../pyproject.toml)):
- 项目名称: `maomao`
- 版本: `0.1.0`
- Python 版本要求: `>=3.11`
- 入口点: `maomao = "maomao.cli:app"`

**需要改进的问题**:
1. 缺少 PyPI 发布所需的完整元数据
2. 缺少 LICENSE 文件声明
3. 缺少分类器（classifiers）信息
4. 缺少发布自动化配置

### 1.2 优化方案

#### 1.2.1 完善 pyproject.toml 配置

```toml
[project]
name = "maomao"
version = "0.1.0"
description = "AI编码知识库系统 - 本地向量化 + MCP集成"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Maomao Team", email = "team@example.com"}
]
keywords = [
    "ai", "knowledge-base", "vector-database", "ollama", 
    "qdrant", "mcp", "rag", "embedding"
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Documentation",
    "Typing :: Typed",
]

dependencies = [
    "qdrant-client>=1.7.0",
    "ollama>=0.1.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "pyyaml>=6.0",
    "httpx>=0.26.0",
    "tree-sitter>=0.21.0",
    "tree-sitter-python>=0.21.0",
    "tree-sitter-javascript>=0.21.0",
    "tree-sitter-typescript>=0.21.0",
    "tree-sitter-go>=0.21.0",
    "tree-sitter-rust>=0.21.0",
    "tree-sitter-java>=0.21.0",
    "rich>=13.7.0",
    "typer>=0.9.0",
    "watchdog>=3.0.0",
    "python-frontmatter>=1.1.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "build>=1.0.0",
    "twine>=4.0.0",
]

[project.urls]
Homepage = "https://github.com/your-org/maomao"
Documentation = "https://github.com/your-org/maomao#readme"
Repository = "https://github.com/your-org/maomao.git"
Issues = "https://github.com/your-org/maomao/issues"
Changelog = "https://github.com/your-org/maomao/blob/main/CHANGELOG.md"

[project.scripts]
maomao = "maomao.cli:app"
```

#### 1.2.2 添加 GitHub Actions 自动发布配置

创建 `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      target:
        description: 'Target environment'
        required: true
        default: 'testpypi'
        type: choice
        options:
          - testpypi
          - pypi

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Check package
        run: twine check dist/*
      
      - name: Publish to TestPyPI
        if: github.event.inputs.target == 'testpypi' || github.event_name == 'workflow_dispatch'
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
      
      - name: Publish to PyPI
        if: github.event_name == 'release' || github.event.inputs.target == 'pypi'
        uses: pypa/gh-action-pypi-publish@release/v1
```

#### 1.2.3 用户安装方式

发布后，用户可以通过以下方式安装：

```bash
# 从 PyPI 安装（推荐）
pip install luckypeak-maomao

# 安装开发版本
pip install luckypeak-maomao[dev]

# 从 GitHub 安装最新版本
pip install git+https://github.com/your-org/maomao.git
```

---

## 2. MCP Server NPM 包分发优化

### 2.1 当前状态分析

**现有配置** ([mcp-server/package.json](../mcp-server/package.json)):
- 包名: `@luckypeak/mcp-server`
- 版本: `0.1.0`
- Node 版本要求: `>=18.0.0`
- 已配置 bin 入口: `maomao-mcp`

**需要改进的问题**:
1. 缺少发布相关的 npm 脚本
2. 缺少 .npmignore 或 files 字段
3. 缺少完整的包元数据
4. 缺少发布自动化配置

### 2.2 优化方案

#### 2.2.1 完善 package.json 配置

```json
{
  "name": "@luckypeak/mcp-server",
  "version": "0.1.0",
  "description": "MCP Server for Maomao Knowledge Base - AI Coding Knowledge Search",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "bin": {
    "maomao-mcp": "dist/index.js"
  },
  "files": [
    "dist/",
    "README.md",
    "LICENSE"
  ],
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "start": "node dist/index.js",
    "lint": "eslint src/",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "prepublishOnly": "npm run build && npm test",
    "release": "standard-version",
    "release:dry": "standard-version --dry-run"
  },
  "keywords": [
    "mcp",
    "model-context-protocol",
    "ai",
    "knowledge-base",
    "vector-search",
    "ollama",
    "qdrant",
    "coding-assistant"
  ],
  "author": "Maomao Team",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/your-org/maomao.git",
    "directory": "mcp-server"
  },
  "bugs": {
    "url": "https://github.com/your-org/maomao/issues"
  },
  "homepage": "https://github.com/your-org/maomao#readme",
  "engines": {
    "node": ">=18.0.0"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "@qdrant/js-client-rest": "^1.7.0",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "typescript": "^5.3.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/eslint-plugin": "^6.19.0",
    "@typescript-eslint/parser": "^6.19.0",
    "vitest": "^3.0.0",
    "standard-version": "^9.5.0"
  },
  "publishConfig": {
    "access": "public",
    "registry": "https://registry.npmjs.org/"
  }
}
```

#### 2.2.2 添加 GitHub Actions 自动发布配置

创建 `.github/workflows/publish-npm.yml`:

```yaml
name: Publish to NPM

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'
      
      - name: Install dependencies
        working-directory: mcp-server
        run: npm ci
      
      - name: Build
        working-directory: mcp-server
        run: npm run build
      
      - name: Test
        working-directory: mcp-server
        run: npm test
      
      - name: Publish to NPM
        working-directory: mcp-server
        run: npm publish --provenance
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

#### 2.2.3 用户安装方式

发布后，用户可以通过以下方式安装：

```bash
# 全局安装（推荐用于 MCP 集成）
npm install -g @luckypeak/mcp-server

# 本地安装
npm install @luckypeak/mcp-server

# 使用 npx 直接运行（无需安装）
npx @luckypeak/mcp-server
```

---

## 3. 统一安装脚本和依赖检测工具

### 3.1 设计思路

创建一个统一的安装命令 `maomao setup`，实现：
1. 自动检测系统环境
2. 检测外部依赖（Ollama、Qdrant）
3. 自动拉取 BGE-M3 模型
4. 生成依赖检查报告
5. 提供一键启动 Qdrant 的 Docker 命令

### 3.2 实现方案

#### 3.2.1 新增 CLI 命令

在 [src/maomao/cli.py](../src/maomao/cli.py) 中添加以下命令：

```python
@app.command()
def setup(
    check_only: Annotated[bool, typer.Option("--check", "-c", help="仅检查依赖，不执行安装")] = False,
    pull_model: Annotated[bool, typer.Option("--pull-model", "-p", help="自动拉取 BGE-M3 模型")] = True,
):
    """
    系统环境检测和初始化设置
    
    检测并配置 Maomao 运行所需的全部依赖。
    """
    console.print("[bold cyan]Maomao 环境检测与配置[/bold cyan]\n")
    
    results = DependencyChecker().check_all()
    
    # 显示检测结果
    _display_check_results(results, console)
    
    if check_only:
        return
    
    # 自动修复缺失项
    _auto_fix_dependencies(results, pull_model, console)


@app.command()
def doctor():
    """
    诊断系统问题
    
    全面检查系统配置，提供详细的诊断报告和修复建议。
    """
    console.print("[bold cyan]Maomao 系统诊断[/bold cyan]\n")
    
    checker = DependencyChecker()
    results = checker.check_all()
    
    _display_diagnosis_report(results, console)
```

#### 3.2.2 创建依赖检测模块

创建 `src/maomao/dependency_checker.py`:

```python
"""依赖检测模块"""

import asyncio
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from rich.console import Console
from rich.table import Table


class DependencyStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    NOT_INSTALLED = "not_installed"


@dataclass
class DependencyResult:
    name: str
    status: DependencyStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    fix_command: str | None = None
    fix_url: str | None = None


class DependencyChecker:
    """依赖检测器"""
    
    def __init__(self):
        self.results: list[DependencyResult] = []
    
    def check_all(self) -> list[DependencyResult]:
        """执行所有依赖检测"""
        self.results = [
            self._check_python_version(),
            self._check_pip(),
            self._check_ollama(),
            self._check_bge_m3_model(),
            self._check_qdrant(),
            self._check_docker(),
        ]
        return self.results
    
    def _check_python_version(self) -> DependencyResult:
        """检查 Python 版本"""
        import sys
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major == 3 and version.minor >= 11:
            return DependencyResult(
                name="Python",
                status=DependencyStatus.OK,
                message=f"版本 {version_str} ✓",
                details={"version": version_str},
            )
        else:
            return DependencyResult(
                name="Python",
                status=DependencyStatus.ERROR,
                message=f"版本 {version_str} 不满足要求 (需要 >= 3.11)",
                fix_url="https://www.python.org/downloads/",
            )
    
    def _check_pip(self) -> DependencyResult:
        """检查 pip"""
        if shutil.which("pip") or shutil.which("pip3"):
            return DependencyResult(
                name="pip",
                status=DependencyStatus.OK,
                message="已安装",
            )
        return DependencyResult(
            name="pip",
            status=DependencyStatus.ERROR,
            message="未找到 pip",
            fix_url="https://pip.pypa.io/en/stable/installation/",
        )
    
    def _check_ollama(self) -> DependencyResult:
        """检查 Ollama"""
        if not shutil.which("ollama"):
            return DependencyResult(
                name="Ollama",
                status=DependencyStatus.NOT_INSTALLED,
                message="未安装",
                fix_url="https://ollama.ai/download",
                fix_command="# 请访问 https://ollama.ai/download 下载安装",
            )
        
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
                return DependencyResult(
                    name="Ollama",
                    status=DependencyStatus.OK,
                    message=f"已安装 ({version})",
                    details={"version": version},
                )
        except Exception:
            pass
        
        return DependencyResult(
            name="Ollama",
            status=DependencyStatus.WARNING,
            message="已安装但无法获取版本信息",
        )
    
    def _check_bge_m3_model(self) -> DependencyResult:
        """检查 BGE-M3 模型"""
        try:
            response = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                if any("bge-m3" in name for name in model_names):
                    return DependencyResult(
                        name="BGE-M3 模型",
                        status=DependencyStatus.OK,
                        message="已下载",
                        fix_command="ollama pull bge-m3",
                    )
                else:
                    return DependencyResult(
                        name="BGE-M3 模型",
                        status=DependencyStatus.NOT_INSTALLED,
                        message="未下载",
                        fix_command="ollama pull bge-m3",
                    )
        except httpx.ConnectError:
            return DependencyResult(
                name="BGE-M3 模型",
                status=DependencyStatus.ERROR,
                message="无法连接 Ollama 服务",
                fix_command="ollama serve",
            )
        except Exception as e:
            return DependencyResult(
                name="BGE-M3 模型",
                status=DependencyStatus.ERROR,
                message=f"检测失败: {e}",
            )
    
    def _check_qdrant(self) -> DependencyResult:
        """检查 Qdrant"""
        try:
            response = httpx.get("http://127.0.0.1:6333/collections", timeout=5)
            if response.status_code == 200:
                return DependencyResult(
                    name="Qdrant",
                    status=DependencyStatus.OK,
                    message="运行中",
                    fix_command="docker run -d -p 6333:6333 qdrant/qdrant",
                )
        except httpx.ConnectError:
            return DependencyResult(
                name="Qdrant",
                status=DependencyStatus.NOT_INSTALLED,
                message="未运行",
                fix_command="docker run -d -p 6333:6333 qdrant/qdrant",
            )
        except Exception as e:
            return DependencyResult(
                name="Qdrant",
                status=DependencyStatus.ERROR,
                message=f"检测失败: {e}",
            )
    
    def _check_docker(self) -> DependencyResult:
        """检查 Docker"""
        if not shutil.which("docker"):
            return DependencyResult(
                name="Docker",
                status=DependencyStatus.NOT_INSTALLED,
                message="未安装 (可选，用于运行 Qdrant)",
                fix_url="https://docs.docker.com/get-docker/",
            )
        
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return DependencyResult(
                    name="Docker",
                    status=DependencyStatus.OK,
                    message="已安装",
                )
        except Exception:
            pass
        
        return DependencyResult(
            name="Docker",
            status=DependencyStatus.WARNING,
            message="已安装但可能未运行",
        )


def _display_check_results(results: list[DependencyResult], console: Console):
    """显示检测结果"""
    table = Table(title="依赖检测结果")
    table.add_column("组件", style="cyan")
    table.add_column("状态", justify="center")
    table.add_column("说明", style="white")
    table.add_column("修复方式", style="yellow")
    
    status_styles = {
        DependencyStatus.OK: "[green]✓ OK[/green]",
        DependencyStatus.WARNING: "[yellow]⚠ 警告[/yellow]",
        DependencyStatus.ERROR: "[red]✗ 错误[/red]",
        DependencyStatus.NOT_INSTALLED: "[red]✗ 未安装[/red]",
    }
    
    for r in results:
        fix = r.fix_command or (f"[link={r.fix_url}]下载链接[/link]" if r.fix_url else "-")
        table.add_row(r.name, status_styles[r.status], r.message, fix)
    
    console.print(table)


def _display_diagnosis_report(results: list[DependencyResult], console: Console):
    """显示诊断报告"""
    _display_check_results(results, console)
    
    errors = [r for r in results if r.status in (DependencyStatus.ERROR, DependencyStatus.NOT_INSTALLED)]
    
    if errors:
        console.print("\n[bold red]需要修复的问题:[/bold red]")
        for r in errors:
            console.print(f"\n[cyan]{r.name}[/cyan]")
            console.print(f"  问题: {r.message}")
            if r.fix_command:
                console.print(f"  命令: [green]{r.fix_command}[/green]")
            if r.fix_url:
                console.print(f"  链接: [blue]{r.fix_url}[/blue]")
    else:
        console.print("\n[bold green]所有依赖检查通过！[/bold green]")


def _auto_fix_dependencies(results: list[DependencyResult], pull_model: bool, console: Console):
    """自动修复依赖"""
    for r in results:
        if r.status == DependencyStatus.NOT_INSTALLED and r.name == "BGE-M3 模型" and pull_model:
            console.print("\n[yellow]正在下载 BGE-M3 模型...[/yellow]")
            try:
                subprocess.run(["ollama", "pull", "bge-m3"], check=True)
                console.print("[green]BGE-M3 模型下载完成！[/green]")
            except Exception as e:
                console.print(f"[red]下载失败: {e}[/red]")
                console.print("请手动执行: [green]ollama pull bge-m3[/green]")
```

### 3.3 依赖检查报告示例

```
╭──────────────────────────────────────────────────────────────────────────────╮
│                         依赖检测结果                                          │
├──────────────┬──────────┬─────────────────────────────┬──────────────────────┤
│ 组件         │ 状态     │ 说明                         │ 修复方式              │
├──────────────┼──────────┼─────────────────────────────┼──────────────────────┤
│ Python       │ ✓ OK     │ 版本 3.11.5                  │ -                    │
│ pip          │ ✓ OK     │ 已安装                       │ -                    │
│ Ollama       │ ✓ OK     │ 已安装 (0.1.26)              │ -                    │
│ BGE-M3 模型  │ ✗ 未安装 │ 未下载                       │ ollama pull bge-m3   │
│ Qdrant       │ ✗ 未安装 │ 未运行                       │ docker run -d ...    │
│ Docker       │ ✓ OK     │ 已安装                       │ -                    │
╰──────────────┴──────────┴─────────────────────────────┴──────────────────────╯

需要修复的问题:

BGE-M3 模型
  问题: 未下载
  命令: ollama pull bge-m3

Qdrant
  问题: 未运行
  命令: docker run -d -p 6333:6333 qdrant/qdrant
```

---

## 4. 配置管理优化

### 4.1 配置文件引导

#### 4.1.1 新增 `maomao init` 命令

```python
@app.command()
def init(
    output: Annotated[str, typer.Option("--output", "-o", help="配置文件输出路径")] = "maomao.json",
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="交互式配置")] = True,
):
    """
    初始化配置文件
    
    创建 maomao.json 配置文件，支持交互式和模板两种模式。
    """
    from pathlib import Path
    
    output_path = Path(output)
    
    if output_path.exists():
        console.print(f"[yellow]配置文件 {output} 已存在[/yellow]")
        if not typer.confirm("是否覆盖？"):
            console.print("操作已取消")
            return
    
    if interactive:
        config = _interactive_config(console)
    else:
        config = _get_default_config()
    
    output_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    console.print(f"\n[green]✓ 配置文件已创建: {output}[/green]")
    console.print("\n下一步:")
    console.print("  1. 编辑配置文件，填写知识源信息")
    console.print("  2. 运行 [cyan]maomao setup[/cyan] 检查依赖")
    console.print("  3. 运行 [cyan]maomao ingest --full[/cyan] 导入知识")


def _interactive_config(console: Console) -> dict:
    """交互式配置"""
    console.print("[bold]交互式配置向导[/bold]\n")
    
    config = {
        "sources": [],
        "ollama": {
            "base_url": "http://127.0.0.1:11434",
            "embedding_model": "bge-m3",
            "embedding_dim": 1024,
        },
        "qdrant": {
            "host": "127.0.0.1",
            "port": 6333,
            "collection_name": "maomao_knowledge",
        },
    }
    
    # 添加思源笔记源
    if typer.confirm("是否配置思源笔记知识源？", default=False):
        source = {
            "type": "siyuan",
            "enabled": True,
            "knowledge_scope": typer.prompt("知识范围 (global/project)", default="global"),
            "config": {
                "api_url": typer.prompt("API 地址", default="http://127.0.0.1:6806"),
                "token": typer.prompt("Token", default=""),
                "box_id": typer.prompt("笔记本 ID", default=""),
            },
        }
        config["sources"].append(source)
    
    # 添加本地文档源
    if typer.confirm("是否配置本地文档知识源？", default=True):
        source = {
            "type": "local_doc",
            "enabled": True,
            "knowledge_scope": typer.prompt("知识范围 (global/project)", default="project"),
            "project_id": typer.prompt("项目 ID", default="my-project"),
            "config": {
                "path": typer.prompt("文档路径"),
                "patterns": ["*.md", "*.txt"],
                "recursive": True,
            },
        }
        config["sources"].append(source)
    
    return config


def _get_default_config() -> dict:
    """获取默认配置模板"""
    return {
        "sources": [
            {
                "type": "local_doc",
                "enabled": True,
                "knowledge_scope": "project",
                "project_id": "my-project",
                "config": {
                    "path": "./docs",
                    "patterns": ["*.md", "*.txt"],
                    "recursive": True,
                },
            }
        ],
        "ollama": {
            "base_url": "http://127.0.0.1:11434",
            "embedding_model": "bge-m3",
            "embedding_dim": 1024,
        },
        "qdrant": {
            "host": "127.0.0.1",
            "port": 6333,
            "collection_name": "maomao_knowledge",
        },
    }
```

#### 4.1.2 配置验证命令

```python
@app.command()
def validate(
    config_file: Annotated[str | None, typer.Option("--config", "-c", help="配置文件路径")] = None,
):
    """
    验证配置文件
    
    检查配置文件的完整性和正确性。
    """
    from pathlib import Path
    
    if config_file:
        path = Path(config_file)
    else:
        path = Path("maomao.json")
    
    if not path.exists():
        console.print(f"[red]错误: 配置文件不存在: {path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]验证配置文件: {path}[/cyan]\n")
    
    try:
        content = path.read_text()
        config_dict = json.loads(content)
        
        errors = []
        warnings = []
        
        # 验证知识源
        sources = config_dict.get("sources", [])
        if not sources:
            warnings.append("未配置任何知识源")
        
        for i, source in enumerate(sources):
            if not source.get("type"):
                errors.append(f"知识源 #{i+1}: 缺少 type 字段")
            if source.get("enabled", True):
                if source["type"] == "siyuan":
                    cfg = source.get("config", {})
                    if not cfg.get("token"):
                        warnings.append(f"知识源 #{i+1} (siyuan): 未配置 token")
                    if not cfg.get("box_id"):
                        warnings.append(f"知识源 #{i+1} (siyuan): 未配置 box_id")
                elif source["type"] == "local_doc":
                    cfg = source.get("config", {})
                    doc_path = cfg.get("path")
                    if not doc_path:
                        errors.append(f"知识源 #{i+1} (local_doc): 未配置 path")
                    elif not Path(doc_path).exists():
                        warnings.append(f"知识源 #{i+1} (local_doc): 路径不存在: {doc_path}")
        
        # 验证 Ollama 配置
        ollama = config_dict.get("ollama", {})
        if not ollama.get("base_url"):
            warnings.append("未配置 Ollama base_url，使用默认值")
        
        # 验证 Qdrant 配置
        qdrant = config_dict.get("qdrant", {})
        if not qdrant.get("collection_name"):
            warnings.append("未配置 Qdrant collection_name，使用默认值")
        
        # 显示结果
        if errors:
            console.print("[red]错误:[/red]")
            for e in errors:
                console.print(f"  ✗ {e}")
        
        if warnings:
            console.print("[yellow]警告:[/yellow]")
            for w in warnings:
                console.print(f"  ⚠ {w}")
        
        if not errors and not warnings:
            console.print("[green]✓ 配置文件验证通过[/green]")
        elif not errors:
            console.print("\n[yellow]配置文件有警告，但可以正常使用[/yellow]")
        else:
            console.print("\n[red]配置文件存在错误，请修复后重试[/red]")
            raise typer.Exit(1)
            
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON 解析错误: {e}[/red]")
        raise typer.Exit(1)
```

### 4.2 配置文件模板

更新 `maomao.example.json`，添加更详细的注释：

```json
{
  "$schema": "https://raw.githubusercontent.com/your-org/maomao/main/schema/maomao.schema.json",
  "sources": [
    {
      "type": "siyuan",
      "enabled": true,
      "knowledge_scope": "global",
      "config": {
        "api_url": "http://127.0.0.1:6806",
        "token": "your-token-here",
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
        "path": "/path/to/your/repo/docs",
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

---

## 5. 用户体验优化

### 5.1 CLI 界面优化

#### 5.1.1 欢迎信息

```python
@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-v", help="显示版本信息")] = False,
):
    """
    Maomao - AI 编码知识库系统
    
    私域知识向量化检索，让 AI 理解你的代码和规范。
    """
    if version:
        from importlib.metadata import version as get_version
        console.print(f"maomao version {get_version('maomao')}")
        raise typer.Exit()
```

#### 5.1.2 错误处理优化

```python
from rich.traceback import install

install(show_locals=True)

def handle_errors(func):
    """错误处理装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except httpx.ConnectError as e:
            console.print(f"[red]连接错误: {e}[/red]")
            console.print("\n[yellow]请检查服务是否运行:[/yellow]")
            console.print("  - Ollama: [cyan]ollama serve[/cyan]")
            console.print("  - Qdrant: [cyan]docker run -d -p 6333:6333 qdrant/qdrant[/cyan]")
            raise typer.Exit(1)
        except FileNotFoundError as e:
            console.print(f"[red]文件未找到: {e}[/red]")
            console.print("\n[yellow]请先创建配置文件:[/yellow]")
            console.print("  [cyan]maomao init[/cyan]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            if "--debug" in sys.argv:
                console.print_exception()
            raise typer.Exit(1)
    return wrapper
```

### 5.2 安装后验证

```python
@app.command()
def verify():
    """
    验证安装
    
    执行完整的系统验证，确保所有组件正常工作。
    """
    console.print("[bold cyan]Maomao 安装验证[/bold cyan]\n")
    
    checks = [
        ("配置文件", _verify_config),
        ("Ollama 连接", _verify_ollama),
        ("BGE-M3 模型", _verify_bge_m3),
        ("Qdrant 连接", _verify_qdrant),
        ("向量存储", _verify_vectorstore),
        ("导入流程", _verify_pipeline),
    ]
    
    results = []
    for name, check_func in checks:
        console.print(f"[cyan]检查 {name}...[/cyan]", end=" ")
        try:
            check_func()
            console.print("[green]✓[/green]")
            results.append((name, True, None))
        except Exception as e:
            console.print(f"[red]✗[/red]")
            results.append((name, False, str(e)))
    
    console.print()
    
    failed = [r for r in results if not r[1]]
    if failed:
        console.print("[red]验证失败:[/red]")
        for name, _, error in failed:
            console.print(f"  - {name}: {error}")
        raise typer.Exit(1)
    else:
        console.print("[bold green]✓ 所有检查通过！[/bold green]")
        console.print("\n下一步:")
        console.print("  - 导入知识: [cyan]maomao ingest --full[/cyan]")
        console.print("  - 搜索测试: [cyan]maomao search \"你的查询\"[/cyan]")
```

### 5.3 一键启动脚本

创建 `scripts/quickstart.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Maomao 快速启动脚本"
echo "========================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# 启动 Qdrant
echo "📦 启动 Qdrant..."
if ! docker ps | grep -q qdrant; then
    docker run -d --name maomao-qdrant -p 6333:6333 qdrant/qdrant
    echo "✓ Qdrant 已启动"
else
    echo "✓ Qdrant 已在运行"
fi

# 检查 Ollama
echo "🤖 检查 Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama 未安装，请先安装 Ollama"
    echo "   https://ollama.ai/download"
    exit 1
fi

# 拉取 BGE-M3 模型
echo "📥 检查 BGE-M3 模型..."
if ! ollama list | grep -q "bge-m3"; then
    echo "正在下载 BGE-M3 模型..."
    ollama pull bge-m3
fi
echo "✓ BGE-M3 模型已就绪"

# 检查配置文件
echo "📝 检查配置文件..."
if [ ! -f "maomao.json" ]; then
    echo "创建默认配置文件..."
    maomao init --no-interactive
fi
echo "✓ 配置文件已就绪"

# 运行验证
echo "🔍 验证安装..."
maomao verify

echo ""
echo "✅ Maomao 已准备就绪！"
echo ""
echo "下一步:"
echo "  1. 编辑 maomao.json 配置知识源"
echo "  2. 运行: maomao ingest --full"
echo "  3. 搜索: maomao search \"你的查询\""
```

---

## 6. 实施计划

### 阶段一：Python 包优化（预计 1-2 天）

1. 完善 `pyproject.toml` 配置
2. 添加 LICENSE 文件
3. 创建 GitHub Actions 发布工作流
4. 测试 PyPI 发布流程

### 阶段二：NPM 包优化（预计 1 天）

1. 完善 `package.json` 配置
2. 添加发布脚本
3. 创建 GitHub Actions 发布工作流
4. 测试 NPM 发布流程

### 阶段三：依赖检测工具（预计 2-3 天）

1. 实现 `dependency_checker.py` 模块
2. 添加 `maomao setup` 命令
3. 添加 `maomao doctor` 命令
4. 添加 `maomao verify` 命令

### 阶段四：配置管理优化（预计 1-2 天）

1. 实现 `maomao init` 命令
2. 实现 `maomao validate` 命令
3. 创建 JSON Schema 文件
4. 更新配置模板

### 阶段五：用户体验优化（预计 1 天）

1. 优化错误处理
2. 添加欢迎信息
3. 创建快速启动脚本
4. 更新文档

---

## 7. 用户安装流程（优化后）

### 7.1 标准安装流程

```bash
# 1. 安装 Python 包
pip install luckypeak-maomao

# 2. 安装 MCP Server（可选，用于 AI 编码助手集成）
npm install -g @luckypeak/mcp-server

# 3. 运行环境检测和初始化
maomao setup

# 4. 创建配置文件
maomao init

# 5. 验证安装
maomao verify

# 6. 导入知识
maomao ingest --full
```

### 7.2 快速启动流程

```bash
# 使用快速启动脚本（自动处理大部分步骤）
curl -fsSL https://raw.githubusercontent.com/your-org/maomao/main/scripts/quickstart.sh | bash
```

### 7.3 MCP 集成配置

编辑 Claude Desktop 配置文件：

```json
{
  "mcpServers": {
    "maomao": {
      "command": "maomao-mcp"
    }
  }
}
```

---

## 8. 总结

本方案通过以下优化实现了用户友好的分发流程：

| 优化项 | 改进内容 |
|--------|----------|
| Python 包 | PyPI 发布、完整元数据、自动化发布流程 |
| NPM 包 | NPM 发布、全局安装支持、一键启动 |
| 依赖管理 | 自动检测、一键修复、详细报告 |
| 配置管理 | 交互式配置、验证功能、模板支持 |
| 用户体验 | 清晰的 CLI 界面、错误处理、安装验证 |

用户现在可以通过 `pip install luckypeak-maomao` 一键安装，然后运行 `maomao setup` 完成环境配置，大大降低了使用门槛。
