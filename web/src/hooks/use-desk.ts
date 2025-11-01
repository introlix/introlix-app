import { researchDeskApi } from "@/lib/api";
import { CreateResearchDeskRequest } from "@/lib/types";
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