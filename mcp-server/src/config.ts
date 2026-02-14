import { z } from "zod";
import { cwd } from "process";
import { basename } from "path";

export const configSchema = z.object({
  qdrant: z.object({
    host: z.string().default("127.0.0.1"),
    port: z.number().default(6333),
    collection: z.string().default("maomao_knowledge"),
  }),
  ollama: z.object({
    baseUrl: z.string().default("http://127.0.0.1:11434"),
    embeddingModel: z.string().default("bge-m3"),
    embeddingDim: z.number().default(1024),
  }),
  search: z.object({
    defaultLimit: z.number().default(10),
    minScore: z.number().default(0.5),
  }),
  project: z.object({
    defaultProjectId: z.string().default(""),
  }),
});

export type Config = z.infer<typeof configSchema>;

function detectProjectId(): string {
  const envProjectId = process.env.MAOMAO_PROJECT_ID;
  if (envProjectId) {
    return envProjectId;
  }
  return basename(cwd());
}

export const defaultConfig: Config = {
  qdrant: {
    host: "127.0.0.1",
    port: 6333,
    collection: "maomao_knowledge",
  },
  ollama: {
    baseUrl: "http://127.0.0.1:11434",
    embeddingModel: "bge-m3",
    embeddingDim: 1024,
  },
  search: {
    defaultLimit: 10,
    minScore: 0.5,
  },
  project: {
    defaultProjectId: "",
  },
};

export function loadConfig(): Config {
  const qdrantHost = process.env.MAOMAO_QDRANT_HOST;
  const qdrantPort = process.env.MAOMAO_QDRANT_PORT;
  const qdrantCollection = process.env.MAOMAO_QDRANT_COLLECTION;
  const ollamaBaseUrl = process.env.MAOMAO_OLLAMA_BASE_URL;
  const ollamaModel = process.env.MAOMAO_OLLAMA_MODEL;

  const config: Config = {
    qdrant: {
      host: qdrantHost ?? defaultConfig.qdrant.host,
      port: qdrantPort ? parseInt(qdrantPort, 10) : defaultConfig.qdrant.port,
      collection: qdrantCollection ?? defaultConfig.qdrant.collection,
    },
    ollama: {
      baseUrl: ollamaBaseUrl ?? defaultConfig.ollama.baseUrl,
      embeddingModel: ollamaModel ?? defaultConfig.ollama.embeddingModel,
      embeddingDim: defaultConfig.ollama.embeddingDim,
    },
    search: defaultConfig.search,
    project: {
      defaultProjectId: detectProjectId(),
    },
  };

  return configSchema.parse(config);
}
