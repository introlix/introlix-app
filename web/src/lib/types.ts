export interface Workspace {
  id?: string;
  name: string;
  description?: string;
  created_at?: string;
}

export interface WorkspaceItem {
  id?: string;
  workspace_id: string;
  title: string;
  type: "chat" | "deepresearch" | "researchdesk";
  content?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}