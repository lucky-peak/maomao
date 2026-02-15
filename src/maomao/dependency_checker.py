"""依赖检测模块"""

import shutil
import subprocess
import sys
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

    def __init__(
        self,
        ollama_base_url: str = "http://127.0.0.1:11434",
        qdrant_host: str = "127.0.0.1",
        qdrant_port: int = 6333,
    ) -> None:
        self.ollama_base_url = ollama_base_url
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
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
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if version.major == 3 and version.minor >= 11:
            return DependencyResult(
                name="Python",
                status=DependencyStatus.OK,
                message=f"版本 {version_str}",
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
            response = httpx.get(f"{self.ollama_base_url}/api/tags", timeout=5)
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
        return DependencyResult(
            name="BGE-M3 模型",
            status=DependencyStatus.ERROR,
            message="未知错误",
        )

    def _check_qdrant(self) -> DependencyResult:
        """检查 Qdrant"""
        try:
            response = httpx.get(
                f"http://{self.qdrant_host}:{self.qdrant_port}/collections", timeout=5
            )
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
        return DependencyResult(
            name="Qdrant",
            status=DependencyStatus.ERROR,
            message="未知错误",
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


def display_check_results(results: list[DependencyResult], console: Console) -> None:
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


def display_diagnosis_report(results: list[DependencyResult], console: Console) -> None:
    """显示诊断报告"""
    display_check_results(results, console)

    errors = [
        r for r in results if r.status in (DependencyStatus.ERROR, DependencyStatus.NOT_INSTALLED)
    ]

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


def auto_fix_dependencies(
    results: list[DependencyResult], pull_model: bool, console: Console
) -> None:
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
