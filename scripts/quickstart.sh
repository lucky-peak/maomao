#!/bin/bash
set -e

echo "🚀 Maomao 快速启动脚本"
echo "========================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.11+"
    echo "   https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python 版本: $PYTHON_VERSION"

# 检查 maomao 是否已安装
if ! command -v maomao &> /dev/null; then
    echo "📦 Maomao 未安装，正在安装..."
    pip install -e . || pip install maomao
fi
echo "✓ Maomao 已安装"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker 未安装，无法自动启动 Qdrant"
    echo "   请手动安装 Docker: https://docs.docker.com/get-docker/"
    echo "   或使用其他方式运行 Qdrant"
else
    echo "✓ Docker 已安装"
    
    # 启动 Qdrant
    echo "📦 检查 Qdrant..."
    if ! docker ps --format '{{.Names}}' | grep -q "maomao-qdrant"; then
        if docker ps -a --format '{{.Names}}' | grep -q "maomao-qdrant"; then
            echo "   启动已存在的 Qdrant 容器..."
            docker start maomao-qdrant
        else
            echo "   创建并启动 Qdrant 容器..."
            docker run -d --name maomao-qdrant -p 6333:6333 qdrant/qdrant
        fi
        sleep 3
    fi
    echo "✓ Qdrant 已就绪"
fi

# 检查 Ollama
echo "🤖 检查 Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama 未安装"
    echo "   请安装 Ollama: https://ollama.ai/download"
else
    echo "✓ Ollama 已安装"
    
    # 检查 Ollama 服务是否运行
    if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "   Ollama 服务未运行，尝试启动..."
        ollama serve &
        sleep 3
    fi
    
    # 拉取 BGE-M3 模型
    echo "📥 检查 BGE-M3 模型..."
    if ! ollama list | grep -q "bge-m3"; then
        echo "   正在下载 BGE-M3 模型..."
        ollama pull bge-m3
    fi
    echo "✓ BGE-M3 模型已就绪"
fi

# 检查配置文件
echo "📝 检查配置文件..."
if [ ! -f "maomao.json" ]; then
    echo "   创建默认配置文件..."
    maomao init --no-interactive
fi
echo "✓ 配置文件已就绪"

# 运行环境检测
echo ""
echo "🔍 运行环境检测..."
maomao setup --check

echo ""
echo "✅ Maomao 环境配置完成！"
echo ""
echo "下一步:"
echo "  1. 编辑 maomao.json 配置知识源"
echo "  2. 运行: maomao ingest --full"
echo "  3. 搜索: maomao search \"你的查询\""
echo ""
echo "MCP 集成 (Claude Desktop):"
echo '  编辑 ~/Library/Application\ Support/Claude/claude_desktop_config.json:'
echo '  {'
echo '    "mcpServers": {'
echo '      "maomao": {'
echo '        "command": "maomao-mcp"'
echo '      }'
echo '    }'
echo '  }'
