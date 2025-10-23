"use client";

import React, { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from "react";
import { ChevronDown, ArrowUp, Upload, Search, Bot, Check, FileText, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type ModelType = "auto" | "gpt-5" | "claude" | "deepseek" | "gemini";
type AgentType = "verifier" | "knowledge-gap" | "research-assistant" | "code-reviewer" | null;

interface ChatInputProps {
  onSubmit: (data: {
    prompt: string;
    model: string;
    search: boolean;
    agent: string;
    files: File[];
  }) => void;
  disabled?: boolean;
}

const MODEL_DISPLAY: Record<ModelType, string> = {
  "auto": "Auto",
  "gpt-5": "GPT-5",
  "claude": "Claude",
  "deepseek": "Deepseek",
  "gemini": "Gemini",
};

const AGENT_DISPLAY: Record<Exclude<AgentType, null>, string> = {
  "verifier": "Verifier",
  "knowledge-gap": "Knowledge Gap",
  "research-assistant": "Research Assistant",
  "code-reviewer": "Code Reviewer",
};

export default function ChatInput({ onSubmit, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isComposing, setIsComposing] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelType>("auto");
  const [selectedAgent, setSelectedAgent] = useState<AgentType>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [searchEnabled, setSearchEnabled] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const models: ModelType[] = ["auto", "gpt-5", "claude", "deepseek", "gemini"];
  const agents: Exclude<AgentType, null>[] = [
    "verifier",
    "knowledge-gap",
    "research-assistant",
    "code-reviewer",
  ];

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const newHeight = Math.min(textarea.scrollHeight, 200);
    textarea.style.height = `${newHeight}px`;
  }, [message]);

  const handleSubmit = (): void => {
    const trimmed = message.trim();
    if (!trimmed || disabled) return;

    onSubmit({
      prompt: trimmed,
      model: selectedModel,
      search: searchEnabled,
      agent: selectedAgent || "",
      files: selectedFiles,
    });

    setMessage("");
    setSelectedFiles([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
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

  return (
    <div className="w-full">
      <div className="rounded-2xl border border-border bg-card shadow-sm">
        <div className="p-4">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder="How can I help you today?"
            disabled={disabled}
            rows={1}
            className="w-full min-h-[24px] max-h-[200px] resize-none border-0 bg-transparent p-0 text-base focus:outline-none placeholder:text-muted-foreground overflow-y-auto disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {selectedFiles.length > 0 && (
          <div className="px-4 pb-2 flex flex-wrap items-center gap-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-1 text-sm bg-secondary px-2 py-1 rounded-md"
              >
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="truncate max-w-[120px]">{file.name}</span>
                <button onClick={() => removeFile(index)} disabled={disabled}>
                  <X className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
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
                disabled={disabled}
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="cursor-pointer"
              >
                <Upload className="h-4 w-4" />
              </Button>
            </div>

            <Button
              variant={searchEnabled ? "default" : "outline"}
              size="icon"
              onClick={() => setSearchEnabled((prev) => !prev)}
              disabled={disabled}
              className="cursor-pointer"
            >
              <Search className="h-4 w-4" />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="relative cursor-pointer"
                  disabled={disabled}
                >
                  <Bot className="h-4 w-4" />
                  {selectedAgent && (
                    <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-primary"></span>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuLabel>Agents</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {agents.map((agent) => (
                  <DropdownMenuItem
                    key={agent}
                    onClick={() =>
                      setSelectedAgent(agent === selectedAgent ? null : agent)
                    }
                    className="flex items-center justify-between cursor-pointer"
                  >
                    <span>{AGENT_DISPLAY[agent]}</span>
                    {selectedAgent === agent && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </DropdownMenuItem>
                ))}
                {selectedAgent && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => setSelectedAgent(null)}
                      className="text-muted-foreground"
                    >
                      Clear Selection
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex items-center gap-1.5 h-8 px-3 rounded-lg text-sm text-muted-foreground cursor-pointer"
                  disabled={disabled}
                >
                  <span>{MODEL_DISPLAY[selectedModel]}</span>
                  <ChevronDown className="h-3.5 w-3.5" />
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
              disabled={!message.trim() || disabled}
              size="icon"
              className="cursor-pointer"
            >
              {disabled ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}