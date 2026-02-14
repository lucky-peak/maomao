import { describe, it, expect } from "vitest";
import type { SearchResult, SearchOptions, KnowledgeContext } from "./types.js";

describe("SearchResult type", () => {
  it("should have all required fields", () => {
    const result: SearchResult = {
      id: "test-id",
      content: "test content",
      sourceType: "siyuan",
      sourcePath: "/test/path",
      sourceId: "source-123",
      knowledgeScope: "global",
      projectId: "",
      metadata: { title: "Test" },
      contentHash: "abc123",
      score: 0.95,
    };

    expect(result.id).toBe("test-id");
    expect(result.knowledgeScope).toBe("global");
    expect(result.projectId).toBe("");
  });

  it("should support project scope", () => {
    const result: SearchResult = {
      id: "test-id",
      content: "test content",
      sourceType: "local_doc",
      sourcePath: "/test/path",
      sourceId: "source-123",
      knowledgeScope: "project",
      projectId: "my-project",
      metadata: {},
      contentHash: "",
      score: 0.85,
    };

    expect(result.knowledgeScope).toBe("project");
    expect(result.projectId).toBe("my-project");
  });
});

describe("SearchOptions type", () => {
  it("should support knowledgeScope filter", () => {
    const options: SearchOptions = {
      knowledgeScope: "global",
      limit: 10,
    };

    expect(options.knowledgeScope).toBe("global");
  });

  it("should support projectId filter", () => {
    const options: SearchOptions = {
      knowledgeScope: "project",
      projectId: "my-project",
      limit: 5,
    };

    expect(options.projectId).toBe("my-project");
  });

  it("should support all filter options", () => {
    const options: SearchOptions = {
      limit: 20,
      sourceType: "siyuan",
      sourcePathPrefix: "/docs/",
      knowledgeScope: "global",
      projectId: "",
      minScore: 0.7,
    };

    expect(options.limit).toBe(20);
    expect(options.sourceType).toBe("siyuan");
    expect(options.sourcePathPrefix).toBe("/docs/");
    expect(options.knowledgeScope).toBe("global");
    expect(options.minScore).toBe(0.7);
  });
});

describe("KnowledgeContext type", () => {
  it("should have all required fields", () => {
    const context: KnowledgeContext = {
      query: "test query",
      results: [],
      totalFound: 0,
      searchTime: 50,
    };

    expect(context.query).toBe("test query");
    expect(context.results).toEqual([]);
    expect(context.totalFound).toBe(0);
    expect(context.searchTime).toBe(50);
  });
});
