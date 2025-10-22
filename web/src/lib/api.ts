import { Workspace, PaginatedResponse, Chat, CreateChatRequest, SendMessageRequest } from "./types";

const BASE_URL = "http://localhost:8000";

// -------------------- WORKSPACES --------------------
export async function getWorkspaces(page = 1, limit = 10): Promise<PaginatedResponse<Workspace>> {
  const res = await fetch(`${BASE_URL}/workspaces?page=${page}&limit=${limit}`);
  return res.json();
}

export async function createWorkspace(data: Workspace): Promise<{ workspace: Workspace }> {
  const res = await fetch(`${BASE_URL}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getWorkspace(id: string): Promise<Workspace> {
  const res = await fetch(`${BASE_URL}/workspaces/${id}`);
  return res.json();
}

export async function deleteWorkspace(id: string): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/workspaces/${id}`, { method: "DELETE" });
  return res.json();
}

// -------------------- CHAT API --------------------
export const chatApi = {
  async create(
    workspaceId: string,
    data: CreateChatRequest
  ): Promise<{ message: string; _id: string }> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/chat/new`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create chat");
    return res.json();
  },

  async getById(chatId: string): Promise<Chat> {
    const res = await fetch(`${BASE_URL}/workspace/placeholder/chat/${chatId}/`);
    if (!res.ok) throw new Error('Chat not found');
    return res.json();
  },

  async delete(chatId: string): Promise<{ message: string }> {
    const res = await fetch(`${BASE_URL}/workspace/placeholder/chat/${chatId}/`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete chat');
    return res.json();
  },

  // Streaming chat - returns an async generator
  async *sendMessage(
    workspaceId: string,
    chatId: string,
    data: SendMessageRequest
  ): AsyncGenerator<string, void, unknown> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/chat/${chatId}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        yield chunk;
      }
    } finally {
      reader.releaseLock();
    }
  },
};