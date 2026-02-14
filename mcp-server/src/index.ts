#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { loadConfig } from "./config.js";
import { KnowledgeService } from "./services.js";

const config = loadConfig();
const knowledge = new KnowledgeService(config);

const server = new McpServer(
  { name: "maomao-knowledge", version: "0.1.0" },
  { capabilities: { tools: {}, resources: {} } }
);

server.registerTool(
  "search_global_knowledge",
  {
    description:
      "搜索通用编程知识库。用于查找编程最佳实践、框架使用方法、设计模式、编码规范等跨项目可复用的知识。\n\n" +
      "适用场景示例：\n" +
      "- 如何正确配置线程池参数？\n" +
      "- 日志打印的最佳实践是什么？\n" +
      "- 数据库事务应该怎么处理？\n" +
      "- 某个第三方框架怎么使用？\n" +
      "- 常见的设计模式有哪些？\n\n" +
      "这些知识通常来自思源笔记等独立于项目的知识沉淀。",
    inputSchema: {
      query: z.string().describe("搜索查询，描述你想查找的通用编程知识"),
      limit: z.number().default(10).describe("返回结果数量，默认10"),
    },
  },
  async (args) => {
    const query = args.query;
    const limit = args.limit ?? 10;

    const results = await knowledge.search(query, {
      limit,
      knowledgeScope: "global",
    });

    const formatted = results
      .map((r, i) => {
        const source = r.sourcePath;
        const location = r.location ? ` (行 ${r.location.start_line}-${r.location.end_line})` : "";
        return `### 通用知识 ${i + 1} (相关度: ${r.score.toFixed(3)})${location}\n来源: ${source}\n\n${r.content}`;
      })
      .join("\n\n---\n\n");

    const header = results.length > 0
      ? `从通用知识库搜索到 ${results.length} 条相关知识：\n\n`
      : "未找到相关通用知识。\n";

    return {
      content: [
        {
          type: "text",
          text: header + formatted,
        },
      ],
    };
  }
);

server.registerTool(
  "search_project_knowledge",
  {
    description:
      "搜索当前项目特定的知识库。用于查找项目业务逻辑、架构决策、代码模式说明等与当前项目高度相关的知识。\n\n" +
      "适用场景示例：\n" +
      "- 这个项目的业务流程是什么？\n" +
      "- 项目中的 Controller 是什么模式？\n" +
      "- 这个模块的设计思路是什么？\n" +
      "- 项目中某个功能是如何实现的？\n" +
      "- 项目的目录结构是怎样的？\n\n" +
      "这些知识通常来自项目 docs 文件夹下的文档。",
    inputSchema: {
      query: z.string().describe("搜索查询，描述你想查找的项目特定知识"),
      project_id: z.string().optional().describe("项目标识，用于区分不同项目的知识"),
      limit: z.number().default(10).describe("返回结果数量，默认10"),
    },
  },
  async (args) => {
    const query = args.query;
    const limit = args.limit ?? 10;
    const projectId = args.project_id ?? config.project.defaultProjectId;

    const results = await knowledge.search(query, {
      limit,
      knowledgeScope: "project",
      projectId,
    });

    const formatted = results
      .map((r, i) => {
        const source = r.sourcePath;
        const project = r.projectId ? `[${r.projectId}] ` : "";
        const location = r.location ? ` (行 ${r.location.start_line}-${r.location.end_line})` : "";
        return `### 项目知识 ${i + 1} (相关度: ${r.score.toFixed(3)})${location}\n${project}来源: ${source}\n\n${r.content}`;
      })
      .join("\n\n---\n\n");

    const header = results.length > 0
      ? `从项目知识库搜索到 ${results.length} 条相关知识：\n\n`
      : "未找到相关项目知识。\n";

    return {
      content: [
        {
          type: "text",
          text: header + formatted,
        },
      ],
    };
  }
);

server.registerTool(
  "search_all_knowledge",
  {
    description:
      "同时搜索通用知识库和项目知识库。当你不确定知识属于哪一类，或者需要综合参考时使用。\n\n" +
      "适用场景：\n" +
      "- 需要同时参考通用最佳实践和项目特定实现\n" +
      "- 不确定某个知识点是通用的还是项目特定的\n" +
      "- 需要更全面的上下文信息",
    inputSchema: {
      query: z.string().describe("搜索查询"),
      project_id: z.string().optional().describe("项目标识（可选）"),
      limit: z.number().default(10).describe("返回结果数量，默认10"),
    },
  },
  async (args) => {
    const query = args.query;
    const limit = args.limit ?? 10;
    const projectId = args.project_id ?? config.project.defaultProjectId;

    const results = await knowledge.search(query, {
      limit,
      projectId,
    });

    const globalResults = results.filter(r => r.knowledgeScope === "global");
    const projectResults = results.filter(r => r.knowledgeScope === "project");

    let output = "";

    if (globalResults.length > 0) {
      output += `## 通用知识 (${globalResults.length} 条)\n\n`;
      output += globalResults
        .map((r, i) => {
          const location = r.location ? ` (行 ${r.location.start_line}-${r.location.end_line})` : "";
          return `### ${i + 1}. ${r.sourcePath}${location} (相关度: ${r.score.toFixed(3)})\n\n${r.content}`;
        })
        .join("\n\n---\n\n");
      output += "\n\n";
    }

    if (projectResults.length > 0) {
      output += `## 项目知识 (${projectResults.length} 条)\n\n`;
      output += projectResults
        .map((r, i) => {
          const project = r.projectId ? `[${r.projectId}] ` : "";
          const location = r.location ? ` (行 ${r.location.start_line}-${r.location.end_line})` : "";
          return `### ${i + 1}. ${project}${r.sourcePath}${location} (相关度: ${r.score.toFixed(3)})\n\n${r.content}`;
        })
        .join("\n\n---\n\n");
    }

    if (results.length === 0) {
      output = "未找到相关知识。";
    }

    return {
      content: [
        {
          type: "text",
          text: output,
        },
      ],
    };
  }
);

server.registerTool(
  "knowledge_status",
  {
    description: "获取知识库状态信息，包括向量数量、使用的嵌入模型等",
    inputSchema: {},
  },
  async () => {
    const status = await knowledge.getStatus();
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              status: "ok",
              vectorCount: status.count,
              collection: config.qdrant.collection,
              embeddingModel: config.ollama.embeddingModel,
              projectId: config.project.defaultProjectId,
            },
            null,
            2
          ),
        },
      ],
    };
  }
);

server.registerResource(
  "status",
  "maomao://status",
  {
    description: "当前知识库的状态信息",
    mimeType: "application/json",
  },
  async () => {
    const status = await knowledge.getStatus();
    return {
      contents: [
        {
          uri: "maomao://status",
          mimeType: "application/json",
          text: JSON.stringify(
            {
              vectorCount: status.count,
              config: {
                qdrant: config.qdrant,
                ollama: config.ollama,
              },
            },
            null,
            2
          ),
        },
      ],
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Maomao MCP Server started");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
