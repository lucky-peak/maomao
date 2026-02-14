export interface ChunkLocation {
  start_line: number;
  end_line: number;
  char_start: number;
  char_end: number;
}

export interface SearchResult {
  id: string;
  content: string;
  sourceType: string;
  sourcePath: string;
  sourceId: string;
  knowledgeScope: string;
  projectId: string;
  metadata: Record<string, unknown>;
  contentHash: string;
  score: number;
  location?: ChunkLocation;
  contextBefore?: string;
  contextAfter?: string;
}

export interface SearchOptions {
  limit?: number;
  sourceType?: string;
  sourcePathPrefix?: string;
  knowledgeScope?: string;
  projectId?: string;
  minScore?: number;
  contextLines?: number;
}

export interface KnowledgeContext {
  query: string;
  results: SearchResult[];
  totalFound: number;
  searchTime: number;
}
