import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from maomao.config import get_settings
from maomao.pipeline import IngestionPipeline

app = typer.Typer(name="maomao", help="AI编码知识库系统 - 私域知识向量化检索")
console = Console()


@app.command()
def ingest(
    full: Annotated[bool, typer.Option("--full", "-f", help="执行全量导入")] = False,
):
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
):
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
def status():
    """查看知识库状态"""
    settings = get_settings()
    pipeline = IngestionPipeline(settings)

    async def get_status():
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
def config():
    """显示当前配置"""
    settings = get_settings()

    console.print("[cyan]当前配置:[/cyan]")
    console.print(f"  Ollama: {settings.ollama.base_url}")
    console.print(f"  模型: {settings.ollama.embedding_model}")
    console.print(f"  Qdrant: {settings.qdrant.host}:{settings.qdrant.port}")
    console.print(f"  集合: {settings.qdrant.collection_name}")

    console.print("\n[cyan]知识源:[/cyan]")
    for source in settings.sources:
        status = "[green]启用[/green]" if source.enabled else "[red]禁用[/red]"
        console.print(f"  - {source.type}: {status}")
        if source.config:
            for key, value in source.config.items():
                if key in ("token", "password", "api_key"):
                    value = "***"
                console.print(f"      {key}: {value}")


@app.command()
def sources():
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


if __name__ == "__main__":
    app()
