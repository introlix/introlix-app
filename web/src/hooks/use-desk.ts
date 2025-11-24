import { researchDeskApi } from "@/lib/api";
import { CreateResearchDeskRequest, ResearchDeskContextAgentRequest } from "@/lib/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

interface UseStreamingOptions {
    onComplete?: (fullMessage: string) => void;
    onError?: (error: Error) => void;
}

// Get desk by ID
export function useDesk(workspaceId: string, deskId: string) {
    return useQuery({
        queryKey: ["research-desk", workspaceId, deskId],
        queryFn: () => researchDeskApi.getById(workspaceId!, deskId!),
        enabled: !!workspaceId && !!deskId,
    });
}

// Create a new research desk
export function useCreateDesk(workspaceId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: CreateResearchDeskRequest) => researchDeskApi.create(workspaceId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk"] });
        },
    });
}

// Add document to research desk
export function useAddDocumentToDesk() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, document }: { workspaceId: string; deskId: string; document: object }) =>
            researchDeskApi.add_document(workspaceId, deskId, document),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["research-desk", variables.workspaceId, variables.deskId] });
        },
    });
}

// Setup a research desk
export function useSetupDesk(workspaceId: string, deskId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ data }: { data: { prompt: string; model: string } }) =>
            researchDeskApi.setup(workspaceId, deskId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk", workspaceId, deskId] });
        }
    });
}

// Setup a context agent
export function useSetupContextAgent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, data }: { workspaceId: string; deskId: string; data: ResearchDeskContextAgentRequest }) =>
            researchDeskApi.setupContextAgent(workspaceId, deskId, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["research-desk", variables.workspaceId, variables.deskId] });
        }
    });
}

// Setup a planner agent
export function useSetupPlannerAgent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, model }: { workspaceId: string; deskId: string; model: string }) =>
            researchDeskApi.setupPlannerAgent(workspaceId, deskId, model),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["research-desk", variables.workspaceId, variables.deskId] });
        }
    });
}

// Edit plans created by planner agent
export function useEditPlans() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, plans }: { workspaceId: string; deskId: string; plans: Array<{ topic: string, priority: string, estimated_sources_needed: number, keywords: Array<string> }> }) =>
            researchDeskApi.editPlans(workspaceId, deskId, plans),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["research-desk", variables.workspaceId, variables.deskId] });
        }
    });
}

// Setup an explorer agent
export function useSetupExplorerAgent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, model }: { workspaceId: string; deskId: string; model: string }) =>
            researchDeskApi.setupExplorerAgent(workspaceId, deskId, model),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["research-desk", variables.workspaceId, variables.deskId] });
        }
    });
}

// Edit document using AI agent
export function useEditDocument() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, data }: { workspaceId: string; deskId: string; data: { prompt: string; model: string } }) =>
            researchDeskApi.editDocument(workspaceId, deskId, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["research-desk", variables.workspaceId, variables.deskId] });
        }
    });
}

// Chat with assistant
export function useChatDesk({ onComplete, onError }: UseStreamingOptions = {}) {
    const [streamingMessage, setStreamingMessage] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    const startStreaming = useCallback(
        async (
            workspaceId: string,
            deskId: string,
            data: {
                prompt: string;
                model: string;
            }
        ) => {
            try {
                setIsStreaming(true);
                setStreamingMessage("");

                // Create abort controller for cancellation
                abortControllerRef.current = new AbortController();

                let fullResponse = "";
                const stream = researchDeskApi.chat(workspaceId, deskId, data);

                for await (const chunk of stream) {
                    // Check if aborted
                    if (abortControllerRef.current?.signal.aborted) {
                        break;
                    }

                    fullResponse += chunk;
                    setStreamingMessage(fullResponse);
                }

                onComplete?.(fullResponse);
                setStreamingMessage("");
            } catch (error) {
                console.error("Streaming error:", error);
                onError?.(error as Error);
            } finally {
                setIsStreaming(false);
                abortControllerRef.current = null;
            }
        },
        [onComplete, onError]
    );

    const stopStreaming = useCallback(() => {
        abortControllerRef.current?.abort();
        setIsStreaming(false);
        setStreamingMessage("");
    }, []);

    return {
        streamingMessage,
        isStreaming,
        startStreaming,
        stopStreaming,
    };
}