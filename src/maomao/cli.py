import asyncio
import json
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from maomao.config import get_settings
from maomao.dependency_checker import (
    DependencyChecker,
    auto_fix_dependencies,
    display_check_results,
    display_diagnosis_report,
)
from maomao.pipeline import IngestionPipeline

app = typer.Typer(name="maomao", help="AI编码知识库系统 - 私域知识向量化检索")
console = Console()


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[bool, typer.Option("--version", "-v", help="显示版本信息")] = False,
) -> None:
    """Maomao - AI 编码知识库系统

    私域知识向量化检索，让 AI 理解你的代码和规范。
    """
    if version:
        from importlib.metadata import version as get_version

        try:
            v = get_version("maomao")
        except Exception:
            v = "0.1.0 (dev)"
        console.print(f"maomao version {v}")
        raise typer.Exit()


@app.command()
def ingest(
    full: Annotated[bool, typer.Option("--full", "-f", help="执行全量导入")] = False,
) -> None:
    """导入知识到向量数据库"""
    settings = get_settings()
    pipeline = IngestionPipeline(settings)

    if full:
        result = asyncio.run(pipeline.run_full_ingest())
    else:
        result = asyncio.run(pipeline.run_incremental_ingest())

    table = Table(title="导入结果")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("总块数", str(result.total_chunks))
    table.add_row("新增", str(result.new_chunks))
    table.add_row("更新", str(result.updated_chunks))
    table.add_row("删除", str(result.deleted_chunks))
    table.add_row("耗时", f"{result.duration_seconds:.2f}s")

    if result.errors:
        table.add_row("错误", str(len(result.errors)))

    console.print(table)

    if result.errors:
        console.print("\n[red]错误详情:[/red]")
        for error in result.errors:
            console.print(f"  - {error}")


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="搜索查询")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="返回结果数量")] = 5,
    source_type: Annotated[str | None, typer.Option("--type", "-t", help="来源类型过滤")] = None,
) -> None:
    """搜索知识库"""
    settings = get_settings()
    pipeline = IngestionPipeline(settings)

    results = asyncio.run(pipeline.search(query, limit=limit, source_type=source_type))

    if not results:
        console.print("[yellow]未找到相关结果[/yellow]")
        return

    console.print(f"\n[bold]搜索结果: {query}[/bold]\n")

    for i, result in enumerate(results, 1):
        content = result.chunk.content[:150] + "..." if len(result.chunk.content) > 150 else result.chunk.content
        content = content.replace("\n", " ")
        source_name = result.chunk.source_path.split("/")[-1]

        console.print(f"[cyan]{i}.[/cyan] [green]{source_name}[/green] [dim](相似度: {result.score:.3f})[/dim]")
        console.print(f"   {content}\n")


@app.command()
def status() -> None:
    """查看知识库状态"""
    settings = get_settings()
    pipeline = IngestionPipeline(settings)

    async def get_status() -> int:
        await pipeline.initialize()
        count = pipeline.vector_store.count() if pipeline.vector_store else 0
        return count

    count = asyncio.run(get_status())

    table = Table(title="知识库状态")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("向量数据库", f"{settings.qdrant.host}:{settings.qdrant.port}")
    table.add_row("集合名称", settings.qdrant.collection_name)
    table.add_row("总向量数", str(count))
    table.add_row("嵌入模型", settings.ollama.embedding_model)
    table.add_row("嵌入维度", str(settings.ollama.embedding_dim))

    enabled_sources = [s.type for s in settings.get_enabled_sources()]
    table.add_row("已启用源", ", ".join(enabled_sources) if enabled_sources else "无")

    console.print(table)


@app.command()
def config() -> None:
    """显示当前配置"""
    settings = get_settings()

    console.print("[cyan]当前配置:[/cyan]")
    console.print(f"  Ollama: {settings.ollama.base_url}")
    console.print(f"  模型: {settings.ollama.embedding_model}")
    console.print(f"  Qdrant: {settings.qdrant.host}:{settings.qdrant.port}")
    console.print(f"  集合: {settings.qdrant.collection_name}")

    console.print("\n[cyan]知识源:[/cyan]")
    for source in settings.sources:
        status_str = "[green]启用[/green]" if source.enabled else "[red]禁用[/red]"
        console.print(f"  - {source.type}: {status_str}")
        if source.config:
            for key, value in source.config.items():
                if key in ("token", "password", "api_key"):
                    value = "***"
                console.print(f"      {key}: {value}")


@app.command()
def sources() -> None:
    """列出所有可用的知识源类型"""
    from maomao.sources import SourceRegistry

    table = Table(title="可用知识源类型")
    table.add_column("类型", style="cyan")
    table.add_column("描述", style="white")

    descriptions = {
        "siyuan": "思源笔记 - 从思源笔记API获取文档内容",
        "local_doc": "本地文档 - 从本地文件系统读取文档（.md, .txt, .rst等）",
    }

    for source_type in SourceRegistry.list_sources():
        desc = descriptions.get(source_type, "自定义知识源")
        table.add_row(source_type, desc)

    console.print(table)


@app.command()
def setup(
    check_only: Annotated[bool, typer.Option("--check", "-c", help="仅检查依赖，不执行安装")] = False,
    pull_model: Annotated[bool, typer.Option("--pull-model", "-p", help="自动拉取 BGE-M3 模型")] = True,
) -> None:
    """系统环境检测和初始化设置

    检测并配置 Maomao 运行所需的全部依赖。
    """
    console.print("[bold cyan]Maomao 环境检测与配置[/bold cyan]\n")

    settings = get_settings()
    checker = DependencyChecker(
        ollama_base_url=settings.ollama.base_url,
        qdrant_host=settings.qdrant.host,
        qdrant_port=settings.qdrant.port,
    )
    results = checker.check_all()

    display_check_results(results, console)

    if check_only:
        return

    auto_fix_dependencies(results, pull_model, console)


@app.command()
def doctor() -> None:
    """诊断系统问题

    全面检查系统配置，提供详细的诊断报告和修复建议。
    """
    console.print("[bold cyan]Maomao 系统诊断[/bold cyan]\n")

    settings = get_settings()
    checker = DependencyChecker(
        ollama_base_url=settings.ollama.base_url,
        qdrant_host=settings.qdrant.host,
        qdrant_port=settings.qdrant.port,
    )
    results = checker.check_all()

    display_diagnosis_report(results, console)


@app.command()
def verify() -> None:
    """验证安装

    执行完整的系统验证，确保所有组件正常工作。
    """
    console.print("[bold cyan]Maomao 安装验证[/bold cyan]\n")

    checks = [
        ("配置文件", _verify_config),
        ("Ollama 连接", _verify_ollama),
        ("Qdrant 连接", _verify_qdrant),
    ]

    results: list[tuple[str, bool, str | None]] = []
    for name, check_func in checks:
        console.print(f"[cyan]检查 {name}...[/cyan]", end=" ")
        try:
            check_func()
            console.print("[green]✓[/green]")
            results.append((name, True, None))
        except Exception as e:
            console.print("[red]✗[/red]")
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


def _verify_config() -> None:
    """验证配置文件"""
    candidates = [
        Path.cwd() / "maomao.json",
        Path.cwd() / ".maomao.json",
        Path.home() / ".maomao.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return
    raise FileNotFoundError("未找到配置文件 maomao.json，请运行 maomao init")


def _verify_ollama() -> None:
    """验证 Ollama 连接"""
    import httpx

    settings = get_settings()
    try:
        response = httpx.get(f"{settings.ollama.base_url}/api/tags", timeout=5)
        if response.status_code != 200:
            raise Exception(f"Ollama 返回状态码 {response.status_code}")
    except httpx.ConnectError:
        raise Exception("无法连接 Ollama 服务，请确保 ollama serve 正在运行") from None


def _verify_qdrant() -> None:
    """验证 Qdrant 连接"""
    import httpx

    settings = get_settings()
    try:
        response = httpx.get(
            f"http://{settings.qdrant.host}:{settings.qdrant.port}/collections", timeout=5
        )
        if response.status_code != 200:
            raise Exception(f"Qdrant 返回状态码 {response.status_code}")
    except httpx.ConnectError:
        raise Exception(
            "无法连接 Qdrant 服务，请运行 docker run -d -p 6333:6333 qdrant/qdrant"
        ) from None


@app.command()
def init(
    output: Annotated[str, typer.Option("--output", "-o", help="配置文件输出路径")] = "maomao.json",
    interactive: Annotated[bool, typer.Option("--interactive/--no-interactive", "-i", help="交互式配置")] = True,
) -> None:
    """初始化配置文件

    创建 maomao.json 配置文件，支持交互式和模板两种模式。
    """
    output_path = Path(output)

    if output_path.exists():
        console.print(f"[yellow]配置文件 {output} 已存在[/yellow]")
        if not typer.confirm("是否覆盖？"):
            console.print("操作已取消")
            return

    config_dict = _interactive_config(console) if interactive else _get_default_config()

    output_path.write_text(json.dumps(config_dict, indent=2, ensure_ascii=False))
    console.print(f"\n[green]✓ 配置文件已创建: {output}[/green]")
    console.print("\n下一步:")
    console.print("  1. 编辑配置文件，填写知识源信息")
    console.print("  2. 运行 [cyan]maomao setup[/cyan] 检查依赖")
    console.print("  3. 运行 [cyan]maomao ingest --full[/cyan] 导入知识")


def _interactive_config(console: Console) -> dict[str, Any]:
    """交互式配置"""
    console.print("[bold]交互式配置向导[/bold]\n")

    config_dict: dict[str, Any] = {
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

    if typer.confirm("是否配置思源笔记知识源？", default=False):
        source: dict[str, Any] = {
            "type": "siyuan",
            "enabled": True,
            "knowledge_scope": typer.prompt("知识范围 (global/project)", default="global"),
            "config": {
                "api_url": typer.prompt("API 地址", default="http://127.0.0.1:6806"),
                "token": typer.prompt("Token", default=""),
                "box_id": typer.prompt("笔记本 ID", default=""),
            },
        }
        config_dict["sources"].append(source)

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
        config_dict["sources"].append(source)

    return config_dict


def _get_default_config() -> dict[str, Any]:
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


@app.command()
def validate(
    config_file: Annotated[str | None, typer.Option("--config", "-c", help="配置文件路径")] = None,
) -> None:
    """验证配置文件

    检查配置文件的完整性和正确性。
    """
    path = Path(config_file) if config_file else Path("maomao.json")

    if not path.exists():
        console.print(f"[red]错误: 配置文件不存在: {path}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]验证配置文件: {path}[/cyan]\n")

    try:
        content = path.read_text()
        config_dict = json.loads(content)

        errors = []
        warnings = []

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

        ollama = config_dict.get("ollama", {})
        if not ollama.get("base_url"):
            warnings.append("未配置 Ollama base_url，使用默认值")

        qdrant = config_dict.get("qdrant", {})
        if not qdrant.get("collection_name"):
            warnings.append("未配置 Qdrant collection_name，使用默认值")

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
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
