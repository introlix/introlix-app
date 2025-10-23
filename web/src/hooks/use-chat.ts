import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatApi, getWorkspaces, getWorkspace, createWorkspace, deleteWorkspace } from "@/lib/api";
import { Workspace } from "@/lib/types";

export function useChat(chatId: string | null) {
  return useQuery({
    queryKey: ["chat", chatId],
    queryFn: () => chatApi.getById(chatId!),
    enabled: !!chatId,
  });
}

export function useWorkspace(workspaceId: string | null) {
  return useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => getWorkspace(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useWorkspaces(page = 1, limit = 10) {
  return useQuery({
    queryKey: ["workspaces", page, limit],
    queryFn: () => getWorkspaces(page, limit),
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Workspace) => createWorkspace(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace"]});
    }
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