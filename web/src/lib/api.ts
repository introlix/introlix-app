import { Workspace, WorkspaceItem, PaginatedResponse } from "./types";

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

// -------------------- WORKSPACE ITEMS --------------------
export async function getWorkspaceItems(
  workspaceId: string,
  page = 1,
  limit = 10
): Promise<PaginatedResponse<WorkspaceItem>> {
  const res = await fetch(`${BASE_URL}/workspaces/${workspaceId}/items?page=${page}&limit=${limit}`);
  return res.json();
}

export async function createWorkspaceItem(workspaceId: string, data: WorkspaceItem) {
  const res = await fetch(`${BASE_URL}/workspaces/${workspaceId}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getWorkspaceItem(workspaceId: string, itemId: string): Promise<WorkspaceItem> {
  const res = await fetch(`${BASE_URL}/workspaces/${workspaceId}/items/${itemId}`);
  return res.json();
}

export async function updateWorkspaceItem(workspaceId: string, itemId: string, data: WorkspaceItem) {
  const res = await fetch(`${BASE_URL}/workspaces/${workspaceId}/items/${itemId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteWorkspaceItem(workspaceId: string, itemId: string) {
  const res = await fetch(`${BASE_URL}/workspaces/${workspaceId}/items/${itemId}`, { method: "DELETE" });
  return res.json();
}