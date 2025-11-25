"use client";
import { Bot, User, Copy, Check } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "@/lib/types";

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "group relative flex gap-3 px-4 py-6 hover:bg-accent/50 transition-colors",
        isUser ? "bg-transparent" : "bg-muted/30"
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold">
            {isUser ? "You" : "Assistant"}
          </span>
          {message.model && (
            <span className="text-xs text-muted-foreground">
              · {message.model}
            </span>
          )}
        </div>

        <div className="prose prose-sm dark:prose-invert max-w-none break-words">
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
          {isStreaming && (
            <span className="inline-block w-1.5 h-4 bg-primary animate-pulse ml-1" />
          )}
        </div>
      </div>

      {!isUser && !isStreaming && (
        <button
          onClick={handleCopy}
          className="absolute right-4 top-6 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-accent"
          aria-label="Copy message"
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-500" />
          ) : (
            <Copy className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
      )}
    </div>
  );
}