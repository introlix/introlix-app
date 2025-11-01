"use client";

import { useParams, useRouter } from "next/navigation";
import { useWorkspace, useCreateChat } from "@/hooks/use-chat";
import { useState } from "react";
import { Loader2, Bot } from "lucide-react";
import ChatInput from "@/components/chat-input";
import { Button } from "@/components/ui/button";

export default function WorkspaceChatPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.workspaceid as string;

  const { data: workspace, isLoading } = useWorkspace(workspaceId);
  const createChat = useCreateChat(workspaceId);
  const [isCreating, setIsCreating] = useState(false);

  // Handle first message submission
  const handleSubmit = async (data: {
    prompt: string;
    model: string;
    search: boolean;
    agent: string;
    files: File[];
  }) => {
    if (!data.prompt.trim()) return;
    setIsCreating(true);

    try {
      // Create chat (backend handles title)
      const result = await createChat.mutateAsync({});
      router.push(
        `/workspaces/${workspaceId}/chat/${result._id}?prompt=${encodeURIComponent(
          data.prompt
        )}`
      );
    } catch (error) {
      console.error("Failed to create chat:", error);
    } finally {
      setIsCreating(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Workspace not found
  if (!workspace) {
    return (
      <div className="flex items-center justify-center h-screen text-center space-y-2">
        <p className="text-lg font-medium">Workspace not found</p>
        <p className="text-sm text-muted-foreground">
          This workspace may have been deleted or doesn’t exist.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full h-screen">
      {/* Center Welcome Section */}
      <div className="flex-1 flex flex-col items-center justify-center text-center px-4 space-y-6">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Bot className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Welcome to {typeof workspace.name === 'string' ? workspace.name : JSON.stringify(workspace.name)}
          </h1>
          <p className="text-base text-muted-foreground">
            What can I help you with today?
          </p>
        </div>
      </div>

      {/* Chat Input at bottom */}
      <div className="sticky bottom-0 left-0 right-0 w-full border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto p-4">
          <ChatInput onSubmit={handleSubmit} disabled={isCreating || createChat.isPending} />
        </div>
      </div>
    </div>
  );
}
