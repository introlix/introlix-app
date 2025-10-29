"use client";

import { useParams, useSearchParams } from "next/navigation";
import ChatPage from "@/components/chat-page";

export default function ChatDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const workspaceId = params.workspaceid as string;
  const chatId = params.chatid as string;
  const initialPrompt = searchParams.get("prompt") || undefined;

  return (
    <ChatPage 
      workspaceId={workspaceId} 
      chatId={chatId}
      initialPrompt={initialPrompt || undefined}
    />
  );
}