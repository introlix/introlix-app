"use client";
import TextEditor from "@/components/text-editor";
import ContextAgentPanel from "@/components/context-agent-panel";
import AgentStatus from "@/components/agent-status";
import { useDesk, useSetupContextAgent, useSetupDesk, useSetupExplorerAgent, useSetupPlannerAgent } from "@/hooks/use-desk";
import type { ResearchDeskContextAgentRequest } from "@/lib/types";
import { Loader2 } from "lucide-react";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, useMemo } from "react";
import DeskPlanCard from "@/components/desk-plans-card";
import { DeskAIPannel } from "@/components/desk-ai-pannel";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

const normalizeResearchScope = (
  scope: string | null
): ResearchDeskContextAgentRequest["research_scope"] => {
  const normalized = scope?.trim().toLowerCase();
  if (
    normalized === "narrow" ||
    normalized === "medium" ||
    normalized === "comprehensive"
  ) {
    return normalized;
  }
  return "medium";
};

export default function ResearchDeskDetails() {
  const params = useParams();
  const searchParams = useSearchParams();

  const [deskState, setDeskState] = useState("");

  const workspaceId = params.workspaceid as string;
  const deskId = params.deskid as string;
  const initialPrompt = searchParams.get("prompt") || undefined;
  const initialModel = searchParams.get("model") || undefined;
  const researchScope = searchParams.get("scope");
  const normalizedScope = useMemo(() => normalizeResearchScope(researchScope), [researchScope]);

  // Get desk by id
  const { data: desk, isLoading } = useDesk(workspaceId, deskId);

  // Setup hooks
  const setupDesk = useSetupDesk(workspaceId, deskId);
  const setupContextAgent = useSetupContextAgent();
  const setupPlannerAgent = useSetupPlannerAgent();
  const setupExplorerAgent = useSetupExplorerAgent();

  useEffect(() => {
    setDeskState(desk?.state || "initial");
  }, [desk?.state]);

  // Setup desk
  const setupTriggered = useRef(false);
  useEffect(() => {
    if (setupTriggered.current) return;
    if (desk?.state !== "initial") return;

    setupTriggered.current = true;
    setupDesk.mutate({
      data: {
        prompt: initialPrompt || "",
        model: initialModel || "auto",
      },
    });
  }, [desk?.state, initialPrompt, initialModel, setupDesk]);

  // Setup context agent
  const contextAgentTriggered = useRef(false);
  useEffect(() => {
    if (contextAgentTriggered.current) return;
    if (deskState !== "context_agent") return;

    contextAgentTriggered.current = true;

    // Only runing this once
    if (desk?.context_agent === null) {
      setupContextAgent.mutate({
        workspaceId,
        deskId,
        data: {
          prompt: initialPrompt?.trim() || "",
          model: initialModel?.trim() || "auto",
          research_scope: normalizedScope,
        },
      });
    }
  }, [deskState, workspaceId, deskId, initialPrompt, initialModel, normalizedScope, setupContextAgent]);

  // Setup planner agent
  const plannerAgentTriggered = useRef(false);
  useEffect(() => {
    if (plannerAgentTriggered.current) return;
    if (desk?.state !== "planner_agent") return;

    plannerAgentTriggered.current = true;
    setupPlannerAgent.mutate({
      workspaceId: workspaceId,
      deskId: deskId,
      model: initialModel || "auto",
    });
  }, [desk?.state, initialPrompt, initialModel, setupDesk]);

  // Setup explorer agent
  const explorerAgentTriggered = useRef(false);
  useEffect(() => {
    if (explorerAgentTriggered.current) return;
    if (desk?.state !== "explorer_agent") return;

    explorerAgentTriggered.current = true;
    setupExplorerAgent.mutate({
      workspaceId: workspaceId,
      deskId: deskId,
      model: initialModel || "auto",
    });
  }, [desk?.state, initialPrompt, initialModel, setupDesk]);

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

  // Desk is not ready
  if (deskState === "initial" || setupDesk.isPending) {
    return (
      <AgentStatus
        message="Initializing Research Environment"
        subMessage="Preparing your workspace..."
        type="setup"
      />
    );
  }

  // Context agent
  if (deskState === "context_agent") {
    return (
      <ContextAgentPanel
        workspaceId={workspaceId}
        deskId={deskId}
        desk={desk}
        initialPrompt={initialPrompt || ""}
        initialModel={initialModel || "auto"}
        researchScope={normalizedScope}
      />
    );
  }

  // Planner agent
  if (deskState === "planner_agent") {
    return (
      <AgentStatus
        message="Formulating Research Strategy"
        subMessage="Analyzing requirements and generating tasks..."
        type="planning"
      />
    );
  }

  // Approve plan
  if (deskState === "approve_plan") {
    return (
      <DeskPlanCard desk_data={desk} />
    )
  }

  // Explorer agent
  if (deskState === "explorer_agent") {
    return (
      <AgentStatus
        message="Conducting Deep Web Analysis"
        subMessage="Gathering relevant information sources..."
        type="searching"
      />
    );
  }

  // Everything is ready
  return (
    <ResizablePanelGroup direction="horizontal" className="h-screen w-full overflow-hidden">
      <ResizablePanel defaultSize={75} minSize={50}>
        <TextEditor workspaceId={workspaceId} deskId={deskId} />
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={25} minSize={15} maxSize={40}>
        <DeskAIPannel workspaceId={workspaceId} deskId={deskId} messages={desk?.messages || []} />
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}
