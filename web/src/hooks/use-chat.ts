/**
 * Chat and Workspace Hooks
 * 
 * This module provides React Query hooks for managing chats and workspaces.
 * All hooks use @tanstack/react-query for caching, automatic refetching, and state management.
 * 
 * Features:
 * - Automatic caching and invalidation
 * - Optimistic updates
 * - Error handling
 * - Loading states
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatApi, getWorkspaces, getWorkspace, createWorkspace, deleteWorkspace, getAllWorkspacesItems, getWorkspaceItems } from "@/lib/api";
import { Workspace } from "@/lib/types";

/**
 * Get a chat by ID
 * @param chatId - Chat ID to fetch (null to disable query)
 * @returns React Query result with chat data
 */
export function useChat(chatId: string | null) {
  return useQuery({
    queryKey: ["chat", chatId],
    queryFn: () => chatApi.getById(chatId!),
    enabled: !!chatId,
  });
}

/**
 * Get a workspace by ID
 * @param workspaceId - Workspace ID to fetch (null to disable query)
 * @returns React Query result with workspace data
 */
export function useWorkspace(workspaceId: string | null) {
  return useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => getWorkspace(workspaceId!),
    enabled: !!workspaceId,
  });
}

/**
 * Get paginated list of workspaces
 * @param page - Page number (default: 1)
 * @param limit - Items per page (default: 10)
 * @returns React Query result with paginated workspaces
 */
export function useWorkspaces(page = 1, limit = 10) {
  return useQuery({
    queryKey: ["workspaces", page, limit],
    queryFn: () => getWorkspaces(page, limit),
  });
}

/**
 * Create a new workspace
 * @returns Mutation hook with create function and status
 */
export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Workspace) => createWorkspace(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
    }
  });
}

/**
 * Get all workspace items across all workspaces (chats, research desks, etc.)
 * @param page - Page number (default: 1)
 * @param limit - Items per page (default: 10)
 * @returns React Query result with paginated items
 */
export function useAllWorkspacesItems(page = 1, limit = 10) {
  return useQuery({
    queryKey: ["workspace-items", page, limit],
    queryFn: () => getAllWorkspacesItems(page, limit),
  })
}

/**
 * Get items for a specific workspace
 * @param workspaceId - Workspace ID
 * @param page - Page number (default: 1)
 * @param limit - Items per page (default: 10)
 * @returns React Query result with workspace items
 */
export function useWorkspaceItems(workspaceId: string, page = 1, limit = 10) {
  return useQuery({
    queryKey: ["workspace-items", workspaceId],
    queryFn: () => getWorkspaceItems(workspaceId, page, limit),
    enabled: !!workspaceId,
  });
}

/**
 * Delete a workspace
 * @returns Mutation hook with delete function and status
 */
export function useDeleteWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workspaceId: string) => deleteWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
    }
  });
}

/**
 * Create a new chat in a workspace
 * @param workspaceId - Workspace ID
 * @returns Mutation hook with create function and status
 */
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

/**
 * Delete a chat
 * @returns Mutation hook with delete function and status
 */
export function useDeleteChat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (chatId: string) => chatApi.delete(chatId),
    onSuccess: (_, chatId) => {
      queryClient.removeQueries({ queryKey: ["chat", chatId] });
    },
  });
}