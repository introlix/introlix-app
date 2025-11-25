/**
 * API Client Module
 * 
 * This module provides a centralized API client for interacting with the backend server.
 * It includes functions for managing workspaces, chats, and research desks.
 * 
 * Features:
 * - Workspace CRUD operations
 * - Chat creation and streaming messages
 * - Research desk workflow management
 * - Type-safe API calls with TypeScript
 * - Streaming support for real-time responses
 * 
 * Base URL: http://localhost:8000
 */

import { Workspace, PaginatedResponse, Chat, CreateChatRequest, SendMessageRequest, WorkspaceItem, ResearchDesk, CreateResearchDeskRequest, ResearchDeskContextAgentRequest, ContextAgentStep } from "./types";

const BASE_URL = "http://localhost:8000";

// -------------------- WORKSPACES --------------------

/**
 * Get all workspaces with pagination
 * @param page - Page number (default: 1)
 * @param limit - Number of items per page (default: 10)
 * @returns Paginated list of workspaces
 */
export async function getWorkspaces(page = 1, limit = 10): Promise<PaginatedResponse<Workspace>> {
  const res = await fetch(`${BASE_URL}/workspaces?page=${page}&limit=${limit}`);
  return res.json();
}

/**
 * Create a new workspace
 * @param data - Workspace data
 * @returns Created workspace object
 */
export async function createWorkspace(data: Workspace): Promise<{ workspace: Workspace }> {
  const res = await fetch(`${BASE_URL}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

/**
 * Get all workspace items across all workspaces
 * @param page - Page number (default: 1)
 * @param limit - Number of items per page (default: 10)
 * @returns Paginated list of workspace items
 * @throws Error if fetch fails
 */
export async function getAllWorkspacesItems(page = 1, limit = 10): Promise<PaginatedResponse<WorkspaceItem>> {
  const res = await fetch(`${BASE_URL}/workspaces/items?page=${page}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch all workspaces items");
  return res.json();
}

/**
 * Get a specific workspace by ID
 * @param id - Workspace ID
 * @returns Workspace object
 */
export async function getWorkspace(id: string): Promise<Workspace> {
  const res = await fetch(`${BASE_URL}/workspaces/${id}`);
  return res.json();
}

/**
 * Delete a workspace
 * @param id - Workspace ID to delete
 * @returns Success message
 * @throws Error if deletion fails
 */
export async function deleteWorkspace(id: string): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/workspaces/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete workspace");
  return res.json();
}

/**
 * Get all items within a specific workspace
 * @param workspaceId - Workspace ID
 * @param page - Page number (default: 1)
 * @param limit - Number of items per page (default: 10)
 * @returns Paginated list of workspace items
 * @throws Error if fetch fails
 */
export async function getWorkspaceItems(workspaceId: string, page = 1, limit = 10): Promise<PaginatedResponse<WorkspaceItem>> {
  const res = await fetch(`${BASE_URL}/workspaces/${workspaceId}/items?page=${page}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch workspace items");
  return res.json();
}

// -------------------- CHAT API --------------------
/**
 * Chat API
 * 
 * Provides methods for managing chat conversations including creation,
 * retrieval, deletion, and streaming message sending.
 */
export const chatApi = {
  /**
   * Create a new chat in a workspace
   * @param workspaceId - Workspace ID
   * @param data - Chat creation data
   * @returns Created chat ID and success message
   * @throws Error if creation fails
   */
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

  /**
   * Get a chat by ID
   * @param chatId - Chat ID
   * @returns Chat object with messages
   * @throws Error if chat not found
   */
  async getById(chatId: string): Promise<Chat> {
    const res = await fetch(`${BASE_URL}/workspace/placeholder/chat/${chatId}/`);
    if (!res.ok) throw new Error('Chat not found');
    return res.json();
  },

  /**
   * Delete a chat
   * @param chatId - Chat ID to delete
   * @returns Success message
   * @throws Error if deletion fails
   */
  async delete(chatId: string): Promise<{ message: string }> {
    const res = await fetch(`${BASE_URL}/workspace/placeholder/chat/${chatId}/`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete chat');
    return res.json();
  },

  /**
   * Send a message and receive streaming response
   * @param workspaceId - Workspace ID
   * @param chatId - Chat ID
   * @param data - Message data (prompt, model, search flag)
   * @yields Streamed response chunks
   * @throws Error if request fails
   */
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


// -------------------- RESEARCH DESK API --------------------
/**
 * Research Desk API
 * 
 * Provides methods for managing research desk workflows including creation,
 * setup, context gathering, planning, exploration, and document management.
 */
export const researchDeskApi = {
  /**
   * Create a new research desk
   * @param workspaceId - Workspace ID
   * @param data - Research desk creation data
   * @returns Created desk ID and success message
   * @throws Error if creation fails
   */
  async create(workspaceId: string, data: CreateResearchDeskRequest): Promise<{ message: string; _id: string }> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/new`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data }),
    });
    if (!res.ok) throw new Error("Failed to create research desk");
    return res.json();
  },

  // Setup a research desk
  async setup(workspaceId: string, deskId: string, data: { prompt: string, model: string }): Promise<{ message: string }> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/setup`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to setup research desk");
    return res.json();
  },

  // Setup a context agent
  async setupContextAgent(workspaceId: string, deskId: string, data: ResearchDeskContextAgentRequest): Promise<ContextAgentStep> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/setup/context-agent`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to setup context agent");
    return res.json();
  },

  // Setup a planner agent
  async setupPlannerAgent(workspaceId: string, deskId: string, model: string): Promise<{ message: string }> {
    const uri = new URL(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/setup/planner-agent`)
    uri.searchParams.set('model', model)
    const res = await fetch(uri, {
      method: "PATCH",
    });
    if (!res.ok) throw new Error("Failed to setup planner agent");
    return res.json();
  },

  // Edit plans created by planner agent
  async editPlans(workspaceId: string, deskId: string, plans: Array<{ topic: string, priority: string, estimated_sources_needed: number, keywords: Array<string> }>): Promise<{ message: string }> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/setup/planner-agent/edit`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(plans),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Failed to edit plans: ${res.status} ${err}`);
    }
    return res.json();
  },

  // Setup explorer agent
  async setupExplorerAgent(workspaceId: string, deskId: string, model: string): Promise<{ message: string }> {
    const uri = new URL(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/setup/explorer-agent`);
    uri.searchParams.set('model', model)
    const res = await fetch(uri, {
      method: "PATCH",
    });
    if (!res.ok) throw new Error("Failed to setup explorer agent");
    return res.json();
  },

  // Write documents to the research desk
  async add_document(
    workspaceId: string,
    deskId: string,
    document: object
  ): Promise<{ message: string }> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/docs`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document }),
    });
    if (!res.ok) throw new Error("Failed to add document to research desk");
    return res.json();
  },

  // Edit document using AI agent
  async editDocument(
    workspaceId: string,
    deskId: string,
    data: { prompt: string; model: string }
  ): Promise<{ status: string; message: string }> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/edit-doc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Failed to edit document: ${res.status} ${err}`);
    }
    return res.json();
  },

  // Streaming chat - Chat with assistant
  async *chat(
    workspaceId: string,
    deskId: string,
    data: { prompt: string, model: string }
  ): AsyncGenerator<string, void, unknown> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}/chat`, {
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


  // Get a research desk by id
  async getById(workspaceId: string, deskId: string): Promise<ResearchDesk> {
    const res = await fetch(`${BASE_URL}/workspace/${workspaceId}/research-desk/${deskId}`);
    if (!res.ok) throw new Error('Research Desk not found');
    return res.json();
  }
}