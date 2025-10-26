import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatApi, getWorkspaces, getWorkspace, createWorkspace, deleteWorkspace, getAllWorkspacesItems, getWorkspaceItems } from "@/lib/api";
import { Workspace } from "@/lib/types";

// Get chat by ID
export function useChat(chatId: string | null) {
  return useQuery({
    queryKey: ["chat", chatId],
    queryFn: () => chatApi.getById(chatId!),
    enabled: !!chatId,
  });
}

// Get workspace by ID
export function useWorkspace(workspaceId: string | null) {
  return useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => getWorkspace(workspaceId!),
    enabled: !!workspaceId,
  });
}

// Get list of workspaces
export function useWorkspaces(page = 1, limit = 10) {
  return useQuery({
    queryKey: ["workspaces", page, limit],
    queryFn: () => getWorkspaces(page, limit),
  });
}

// Create a new workspace
export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Workspace) => createWorkspace(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace"]});
    }
  });
}

// Get all workspaces items (chats, deep research, research desk, etc.)
export function useAllWorkspacesItems(page = 1, limit = 10) {
  return useQuery({
    queryKey: ["workspace-items", page, limit],
    queryFn: () => getAllWorkspacesItems(page, limit),
  })
}

// Get items related to a specific workspace
export function useWorkspaceItems(workspaceId: string, page = 1, limit = 10) {
  return useQuery({
    queryKey: ["workspace-items", workspaceId],
    queryFn: () => getWorkspaceItems(workspaceId, page, limit),
    enabled: !!workspaceId,
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workspaceId: string) => deleteWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace"]});
    }
  });
}

export function useCreateChat(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { title?: string }) => 
      chatApi.create(workspaceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace", workspaceId] });
    },
  });
}

export function useDeleteChat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (chatId: string) => chatApi.delete(chatId),
    onSuccess: (_, chatId) => {
      queryClient.removeQueries({ queryKey: ["chat", chatId] });
    },
  });
}