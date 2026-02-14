import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { loadConfig, defaultConfig } from "./config.js";

describe("loadConfig", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("should return default config when no env vars set", () => {
    const config = loadConfig();
    expect(config.qdrant.host).toBe(defaultConfig.qdrant.host);
    expect(config.qdrant.port).toBe(defaultConfig.qdrant.port);
    expect(config.ollama.embeddingModel).toBe(defaultConfig.ollama.embeddingModel);
  });

  it("should use MAOMAO_PROJECT_ID env var", () => {
    process.env.MAOMAO_PROJECT_ID = "test-project";
    const config = loadConfig();
    expect(config.project.defaultProjectId).toBe("test-project");
  });

  it("should use MAOMAO_QDRANT_HOST env var", () => {
    process.env.MAOMAO_QDRANT_HOST = "qdrant.example.com";
    const config = loadConfig();
    expect(config.qdrant.host).toBe("qdrant.example.com");
  });

  it("should use MAOMAO_QDRANT_PORT env var", () => {
    process.env.MAOMAO_QDRANT_PORT = "6334";
    const config = loadConfig();
    expect(config.qdrant.port).toBe(6334);
  });

  it("should use MAOMAO_OLLAMA_BASE_URL env var", () => {
    process.env.MAOMAO_OLLAMA_BASE_URL = "http://ollama.example.com:11434";
    const config = loadConfig();
    expect(config.ollama.baseUrl).toBe("http://ollama.example.com:11434");
  });

  it("should use MAOMAO_OLLAMA_MODEL env var", () => {
    process.env.MAOMAO_OLLAMA_MODEL = "nomic-embed-text";
    const config = loadConfig();
    expect(config.ollama.embeddingModel).toBe("nomic-embed-text");
  });

  it("should use MAOMAO_QDRANT_COLLECTION env var", () => {
    process.env.MAOMAO_QDRANT_COLLECTION = "custom_collection";
    const config = loadConfig();
    expect(config.qdrant.collection).toBe("custom_collection");
  });
});
