
"use client";

import React, { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from "react";
import { ChevronDown, ArrowUp, Upload, Bot, Check, FileText, X, MessageSquare, Edit2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { useChatDesk, useEditDocument, useDesk } from "@/hooks/use-desk";
import { Message } from "@/lib/types";
import { ChatMessages } from "@/components/chat-messages";

type ModelType = "auto" | "gpt-5" | "claude-sonnet-4" | "deepseek/deepseek-v3.2-exp" | "google/gemini-2.5-pro";
type ModeType = "ask" | "edit";

const MODEL_DISPLAY: Record<ModelType, string> = {
  "auto": "Auto",
  "gpt-5": "GPT-5",
  "claude-sonnet-4": "Claude Sonnet 4",
  "deepseek/deepseek-v3.2-exp": "Deepseek",
  "google/gemini-2.5-pro": "Gemini 2.5 Pro",
};

const MODE_DISPLAY: Record<ModeType, { label: string; icon: React.ElementType }> = {
  "ask": { label: "Ask", icon: MessageSquare },
  "edit": { label: "Edit", icon: Edit2 },
};

interface DeskAIPannelProps {
  workspaceId: string;
  deskId: string;
  messages: Message[];
}

export const DeskAIPannel = ({ workspaceId, deskId, messages }: DeskAIPannelProps) => {
  const [mode, setMode] = useState<ModeType>("ask");
  const [message, setMessage] = useState("");
  const [isComposing, setIsComposing] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelType>("auto");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const models: ModelType[] = ["auto", "gpt-5", "claude-sonnet-4", "deepseek/deepseek-v3.2-exp", "google/gemini-2.5-pro"];

  const { streamingMessage, isStreaming, startStreaming } = useChatDesk({
    onComplete: async () => {
      await queryClient.invalidateQueries({ queryKey: ["research-desk", workspaceId, deskId] });
    },
    onError: (error) => {
      console.error("Chat error:", error);
    }
  });

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const newHeight = Math.min(textarea.scrollHeight, 300);
    textarea.style.height = `${newHeight} px`;
  }, [message]);

  const { mutate: editDocument, isPending: isEditing } = useEditDocument();
  const { data: desk } = useDesk(workspaceId, deskId);

  const handleSubmit = async () => {
    const trimmed = message.trim();
    if (!trimmed) return;

    // Clear input immediately
    setMessage("");
    setSelectedFiles([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    if (mode === "ask") {
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      };

      // Optimistic update
      queryClient.setQueryData(["research-desk", workspaceId, deskId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          messages: [...(old.messages || []), userMessage],
        };
      });

      await startStreaming(workspaceId, deskId, {
        prompt: trimmed,
        model: selectedModel,
      });
    } else {
      // Edit mode      // Optimistic update
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      };

      queryClient.setQueryData(["research-desk", workspaceId, deskId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          messages: [...(old.messages || []), userMessage],
        };
      });

      editDocument({
        workspaceId,
        deskId,
        data: {
          prompt: trimmed,
          model: selectedModel
        }
      }, {
        onError: (error) => {
          console.error("Edit error:", error);
          // Optionally show error toast
        }
      });
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const newFiles = Array.from(e.target.files);
    const combined = [...selectedFiles, ...newFiles].slice(0, 4);
    setSelectedFiles(combined);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const CurrentModeIcon = MODE_DISPLAY[mode].icon;

  return (
    <div className="w-full bg-background flex flex-col h-full shrink-0">
      {/* Chat History / Content Area */}
      {messages.length === 0 && !isStreaming ? (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 text-muted-foreground/50">
            <div className="p-4 bg-muted/20 rounded-full">
              <Bot className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground/80">
                {mode === "ask" ? "Research Assistant" : "Editor Assistant"}
              </p>
              <p className="text-xs max-w-[200px] mx-auto">
                {mode === "ask"
                  ? "Ask questions about your research, sources, or data."
                  : "Describe changes to edit your research document."}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <ChatMessages
          messages={messages}
          streamingMessage={streamingMessage}
          isLoading={isStreaming && !streamingMessage}
        />
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-background/50 backdrop-blur-sm">
        <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden transition-all duration-200 ease-in-out hover:shadow-md">
          <div className="p-4">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onCompositionStart={() => setIsComposing(true)}
              onCompositionEnd={() => setIsComposing(false)}
              placeholder={mode === "ask" ? "Ask a question..." : "Describe changes..."}
              rows={1}
              className="w-full min-h-[24px] max-h-[300px] resize-none border-0 bg-transparent p-0 text-base focus:outline-none placeholder:text-muted-foreground overflow-y-auto"
            />
          </div>

          {selectedFiles.length > 0 && (
            <div className="px-4 pb-2 flex flex-wrap items-center gap-2">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-1 text-sm bg-secondary px-2 py-1 rounded-md animate-in fade-in zoom-in duration-200"
                >
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="truncate max-w-[120px]">{file.name}</span>
                  <button onClick={() => removeFile(index)} className="ml-1">
                    <X className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between px-4 pb-3 pt-2">
            <div className="flex items-center gap-2">
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileSelect}
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => fileInputRef.current?.click()}
                  className="cursor-pointer h-8 w-8 rounded-lg transition-colors hover:bg-muted"
                  title="Attach files"
                >
                  <Upload className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>

              {/* Search and Agent buttons removed */}

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="relative cursor-pointer h-8 w-8 rounded-lg transition-colors hover:bg-muted"
                    title="Select mode"
                  >
                    <CurrentModeIcon className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-40">
                  <DropdownMenuLabel>Mode</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => setMode("ask")}
                    className="flex items-center justify-between cursor-pointer"
                  >
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4" />
                      <span>Ask</span>
                    </div>
                    {mode === "ask" && <Check className="h-4 w-4 text-primary" />}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setMode("edit")}
                    className="flex items-center justify-between cursor-pointer"
                  >
                    <div className="flex items-center gap-2">
                      <Edit2 className="h-4 w-4" />
                      <span>Edit</span>
                    </div>
                    {mode === "edit" && <Check className="h-4 w-4 text-primary" />}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                  >
                    <span>{MODEL_DISPLAY[selectedModel]}</span>
                    <ChevronDown className="h-3 w-3 opacity-50" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuLabel>Models</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {models.map((model) => (
                    <DropdownMenuItem
                      key={model}
                      onClick={() => setSelectedModel(model)}
                      className="flex items-center justify-between cursor-pointer"
                    >
                      <span>{MODEL_DISPLAY[model]}</span>
                      {selectedModel === model && (
                        <Check className="h-4 w-4 text-primary" />
                      )}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                onClick={handleSubmit}
                disabled={!message.trim() || isStreaming || isEditing}
                size="icon"
                className={cn(
                  "h-8 w-8 rounded-lg transition-all duration-200 cursor-pointer",
                  message.trim()
                    ? "bg-primary text-primary-foreground shadow-sm hover:bg-primary/90"
                    : "bg-muted text-muted-foreground cursor-not-allowed"
                )}
              >
                {isStreaming || isEditing ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                ) : (
                  <ArrowUp className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
