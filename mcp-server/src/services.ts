import { QdrantClient } from "@qdrant/js-client-rest";
import type { Config } from "./config.js";
import type { SearchResult, SearchOptions, ChunkLocation } from "./types.js";

export class EmbeddingService {
  private baseUrl: string;
  private model: string;
  private dim: number;

  constructor(config: Config["ollama"]) {
    this.baseUrl = config.baseUrl;
    this.model = config.embeddingModel;
    this.dim = config.embeddingDim;
  }

  async embed(text: string): Promise<number[]> {
    const response = await fetch(`${this.baseUrl}/api/embeddings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: this.model, prompt: text }),
    });

    if (!response.ok) {
      throw new Error(`Embedding failed: ${response.statusText}`);
    }

    const data = (await response.json()) as { embedding?: number[] };
    return data.embedding ?? new Array(this.dim).fill(0);
  }

  async embedBatch(texts: string[]): Promise<number[][]> {
    const embeddings: number[][] = [];
    const batchSize = 10;

    for (let i = 0; i < texts.length; i += batchSize) {
      const batch = texts.slice(i, i + batchSize);
      const results = await Promise.all(batch.map((t) => this.embed(t)));
      embeddings.push(...results);
    }

    return embeddings;
  }
}

export class VectorStore {
  private client: QdrantClient;
  private collection: string;

  constructor(config: Config["qdrant"]) {
    this.client = new QdrantClient({
      host: config.host,
      port: config.port,
    });
    this.collection = config.collection;
  }

  async search(
    vector: number[],
    options: SearchOptions = {}
  ): Promise<SearchResult[]> {
    const limit = options.limit ?? 10;

    const filter: Record<string, unknown> = {};
    const must: Record<string, unknown>[] = [];

    if (options.sourceType) {
      must.push({
        key: "source_type",
        match: { value: options.sourceType },
      });
    }

    if (options.sourcePathPrefix) {
      must.push({
        key: "source_path",
        match: { text: options.sourcePathPrefix },
      });
    }

    if (options.knowledgeScope) {
      must.push({
        key: "knowledge_scope",
        match: { value: options.knowledgeScope },
      });
    }

    if (options.projectId) {
      must.push({
        key: "project_id",
        match: { value: options.projectId },
      });
    }

    if (must.length > 0) {
      filter.must = must;
    }

    const results = await this.client.search(this.collection, {
      vector,
      limit,
      filter: must.length > 0 ? filter : undefined,
    });

    return results
      .filter((r) => (options.minScore ?? 0) <= r.score)
      .map((r) => {
        const payload = r.payload || {};
        const locationData = payload.location as Record<string, number> | undefined;
        const location: ChunkLocation | undefined = locationData ? {
          start_line: locationData.start_line ?? 0,
          end_line: locationData.end_line ?? 0,
          char_start: locationData.char_start ?? 0,
          char_end: locationData.char_end ?? 0,
        } : undefined;
        
        return {
          id: String(r.id),
          content: (payload.content as string) ?? "",
          sourceType: (payload.source_type as string) ?? "",
          sourcePath: (payload.source_path as string) ?? "",
          sourceId: (payload.source_id as string) ?? "",
          knowledgeScope: (payload.knowledge_scope as string) ?? "global",
          projectId: (payload.project_id as string) ?? "",
          metadata: (payload.metadata as Record<string, unknown>) ?? {},
          contentHash: (payload.content_hash as string) ?? "",
          score: r.score,
          location,
        };
      });
  }

  async count(): Promise<number> {
    const result = await this.client.count(this.collection);
    return result.count;
  }
}

export class KnowledgeService {
  private embedding: EmbeddingService;
  private vectorStore: VectorStore;
  private defaultLimit: number;
  private minScore: number;

  constructor(config: Config) {
    this.embedding = new EmbeddingService(config.ollama);
    this.vectorStore = new VectorStore(config.qdrant);
    this.defaultLimit = config.search.defaultLimit;
    this.minScore = config.search.minScore;
  }

  async search(query: string, options: SearchOptions = {}): Promise<SearchResult[]> {
    const vector = await this.embedding.embed(query);
    return this.vectorStore.search(vector, {
      limit: options.limit ?? this.defaultLimit,
      minScore: options.minScore ?? this.minScore,
      sourceType: options.sourceType,
      sourcePathPrefix: options.sourcePathPrefix,
      knowledgeScope: options.knowledgeScope,
      projectId: options.projectId,
      contextLines: options.contextLines,
    });
  }

  async getContext(
    query: string,
    options: SearchOptions = {}
  ): Promise<string> {
    const startTime = Date.now();
    const results = await this.search(query, options);
    const searchTime = Date.now() - startTime;

    if (results.length === 0) {
      return "未找到相关知识片段。";
    }

    const contextParts = results.map((r, i) => {
      const source = `[${r.sourceType}] ${r.sourcePath}`;
      const location = r.location ? ` (行 ${r.location.start_line}-${r.location.end_line})` : "";
      let content = r.content;
      
      if (r.contextBefore || r.contextAfter) {
        content = [
          r.contextBefore ? `...\n${r.contextBefore}` : "",
          r.content,
          r.contextAfter ? `${r.contextAfter}\n...` : "",
        ].filter(Boolean).join("\n");
      }
      
      return `### 相关知识 ${i + 1} (相关度: ${r.score.toFixed(3)})${location}\n来源: ${source}\n\n${content}`;
    });

    const header = `基于知识库搜索到 ${results.length} 条相关知识 (耗时 ${searchTime}ms):\n`;
    return header + contextParts.join("\n\n---\n\n");
  }

  async getStatus(): Promise<{ count: number }> {
    const count = await this.vectorStore.count();
    return { count };
  }
}
