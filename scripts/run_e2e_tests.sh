#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== Maomao E2E Test Runner ==="

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "Error: Docker is not running"
        exit 1
    fi
}

start_services() {
    echo "Starting test services (Qdrant, Ollama)..."
    docker-compose -f "$PROJECT_DIR/docker-compose.test.yml" up -d
    
    echo "Waiting for services to be ready..."
    sleep 5
    
    for i in {1..30}; do
        if curl -s http://localhost:6333/health > /dev/null 2>&1; then
            echo "Qdrant is ready"
            break
        fi
        echo "Waiting for Qdrant... ($i/30)"
        sleep 2
    done
    
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "Ollama is ready"
            break
        fi
        echo "Waiting for Ollama... ($i/30)"
        sleep 2
    done
}

pull_model() {
    local model="${MAOMAO_OLLAMA_MODEL:-bge-m3}"
    echo "Pulling embedding model: $model"
    docker exec maomao-ollama-1 ollama pull "$model" || {
        echo "Warning: Failed to pull model $model, tests may fail"
        echo "You can manually pull with: docker exec maomao-ollama-1 ollama pull $model"
    }
}

run_tests() {
    echo "Running E2E tests..."
    python -m pytest tests/test_e2e.py -v -m e2e "$@"
}

stop_services() {
    echo "Stopping test services..."
    docker-compose -f "$PROJECT_DIR/docker-compose.test.yml" down -v
}

cleanup() {
    stop_services
}

trap cleanup EXIT

check_docker
start_services
pull_model
run_tests "$@"
