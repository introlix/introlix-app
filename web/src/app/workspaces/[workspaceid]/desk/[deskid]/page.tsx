"use client";
import TextEditor from "@/components/text-editor";
import { useDesk, useSetupDesk } from "@/hooks/use-desk";
import { Loader2 } from "lucide-react";
import { useParams, useSearchParams } from "next/navigation";

export default function ResearchDeskDetails() {
    const params = useParams();
    const searchParams = useSearchParams();

    const workspaceId = params.workspaceid as string;
    const deskId = params.deskid as string;
    const initialPrompt = searchParams.get("prompt") || undefined;

    // Get desk by id
    const { data: desk, isLoading } = useDesk(workspaceId, deskId);

    // Setup desk
    const setupDesk = useSetupDesk();

    // Loading state
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    // Desk not found
    if (!desk) {
        return (
            <div className="flex items-center justify-center h-screen">
                <p className="text-lg font-medium">Desk not found</p>
            </div>
        );
    }

    // If desk not setup add title and everything
    if (desk.state === "initial") {

      return (
        <div className="flex items-center justify-center h-screen">
          <span>Setting up your research desk...</span>
        </div>
      );
    }
  return (
    <main className="flex flex-1">
      <TextEditor workspaceId={workspaceId} deskId={deskId} />
      <div className="">AI Pannel</div>
    </main>
  )
}
