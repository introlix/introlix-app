export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}


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