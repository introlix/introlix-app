"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import { Loader2 } from "lucide-react";
import { ChatMessage } from "./chat-message";
import { Skeleton } from "./ui/skeleton";

interface ChatMessagesProps {
  messages: Message[];
  streamingMessage?: string;
  isLoading?: boolean;
}

export function ChatMessages({ 
  messages, 
  streamingMessage, 
  isLoading = false 
}: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  if (messages.length === 0 && !streamingMessage && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div className="max-w-md space-y-4">
          <h2 className="text-2xl font-semibold">Start a conversation</h2>
          <p className="text-muted-foreground">
            Ask me anything! I can help with coding, writing, analysis, and more.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto scroll-smooth">
      <div className="max-w-3xl mx-auto">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {streamingMessage && (
          <ChatMessage
            message={{
              id: "streaming",
              role: "assistant",
              content: streamingMessage,
              created_at: new Date().toISOString(),
            }}
            isStreaming
          />
        )}

        {isLoading && !streamingMessage && (
          <div className="flex gap-3 px-4 py-6">
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[400px]" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
