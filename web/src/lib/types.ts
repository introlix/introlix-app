export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

// -------------------- CHAT --------------------
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  tokens?: number;
  model?: string;
}

export interface Chat {
  id: string;
  workspace_id: string;
  title?: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Workspace {
  id: string | null;
  name: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceItem {
  id: string;
  workspace_id: string;
  title: string;
  type: 'chat' | 'deep_research' | 'research_desk' | null;
  created_at: string;
  updated_at: string;
}

export interface CreateChatRequest {
  workspace_id?: string;
  title?: string;
  messages?: Message[];
}

export interface SendMessageRequest {
  prompt: string;
  model: string;
  search: boolean;
  agent: string;
}

// -------------------- RESEARCH DESK --------------------
export interface CreateResearchDeskRequest {
  workspace_id?: string;
  title?: string;
  documents?: object;
}

export interface ContextAgent {
  id?: string | null;
  conv_history?: unknown;
  questions?: Array<string>;
  move_next?: boolean;
  confidence_level?: number;
  final_prompt?: string;
  research_parameters?: Record<string, unknown> | null;
}

interface TopicData {
  topic: string;
  priority: string;
  estimated_sources_needed: number;
  keywords: string[];
}

export interface ResearchDesk {
  id: string | null;
  workspace_id?: string;
  state?: string;
  title?: string;
  documents?: object;
  context_agent?: ContextAgent | null;
  planner_agent?: { topics: TopicData[] } | null;
  messages?: Message[];
  created_at: string;
  updated_at: string;
}

export interface ResearchDeskContextAgentRequest {
  prompt: string;
  model: string;
  answers?: string;
  research_scope: "narrow" | "medium" | "comprehensive";
  user_files?: Array<object>;
}

export interface ContextAgentStep {
  questions: string[];
  move_next: boolean;
  confidence_level: number;
  final_prompt: string | null;
  research_parameters: Record<string, unknown> | null;
  state: string;
}