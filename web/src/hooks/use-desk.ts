import { researchDeskApi } from "@/lib/api";
import { CreateResearchDeskRequest, ResearchDeskContextAgentRequest } from "@/lib/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk"] });
        },
    });
}

// Setup a research desk
export function useSetupDesk() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, data }: { workspaceId: string; deskId: string; data: { prompt: string; model: string } }) =>
            researchDeskApi.setup(workspaceId, deskId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk"] });
        }
    });
}

// Setup a context agent
export function useSetupContextAgent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, data }: { workspaceId: string; deskId: string; data: ResearchDeskContextAgentRequest }) =>
            researchDeskApi.setupContextAgent(workspaceId, deskId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk"] });
        }
    });
}

// Setup a planner agent
export function useSetupPlannerAgent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, model }: { workspaceId: string; deskId: string; model: string }) =>
            researchDeskApi.setupPlannerAgent(workspaceId, deskId, model),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk"] });
        }
    });
}

// Edit plans created by planner agent
export function useEditPlans() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, plans }: { workspaceId: string; deskId: string; plans: Array<{ topic: string, priority: string, estimated_sources_needed: number, keywords: Array<string> }> }) =>
            researchDeskApi.editPlans(workspaceId, deskId, plans),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk"] });
        }
    });
}

// Setup an explorer agent
export function useSetupExplorerAgent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ workspaceId, deskId, model }: { workspaceId: string; deskId: string; model: string }) =>
            researchDeskApi.setupExplorerAgent(workspaceId, deskId, model),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["research-desk"] });
        }
    });
}