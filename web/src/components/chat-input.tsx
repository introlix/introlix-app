"use client";

import React, { useState, useRef, useEffect, KeyboardEvent, ChangeEvent, JSX } from "react";
import { ChevronDown, ArrowUp, Upload, Search, Bot, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// --- Types ---
type ModelType = "Auto" | "GPT-5" | "Claude" | "Deepseek" | "Gemini";
type AgentType = "Verifier" | "Knowledge Gap" | "Research Assistant" | "Code Reviewer" | null;

export default function ChatInput(): JSX.Element {
  const [message, setMessage] = useState<string>("");
  const [isComposing, setIsComposing] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<ModelType>("Auto");
  const [selectedAgent, setSelectedAgent] = useState<AgentType>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const models: ModelType[] = ["Auto", "GPT-5", "Claude", "Deepseek", "Gemini"];
  const agents: Exclude<AgentType, null>[] = ["Verifier", "Knowledge Gap", "Research Assistant", "Code Reviewer"];

  // --- Auto-resize textarea ---
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const newHeight = Math.min(textarea.scrollHeight, 200);
    textarea.style.height = `${newHeight}px`;
  }, [message]);

  // --- Handlers ---
  const handleSubmit = (): void => {
    const trimmed = message.trim();
    if (!trimmed || isComposing) return;

    console.log("Sending message:", trimmed);
    console.log("Model:", selectedModel);
    console.log("Agent:", selectedAgent);

    setMessage("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>): void => {
    setMessage(e.target.value);
  };

  // --- Render ---
  return (
    <div className="w-full h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-3xl">
        {/* Input Container */}
        <div className="rounded-2xl border border-border bg-card shadow-sm">
          {/* Textarea */}
          <div className="p-4">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              onCompositionStart={() => setIsComposing(true)}
              onCompositionEnd={() => setIsComposing(false)}
              placeholder="How can I help you today?"
              rows={1}
              className="w-full min-h-[24px] max-h-[200px] resize-none border-0 bg-transparent p-0 text-base focus:outline-none placeholder:text-muted-foreground overflow-y-auto"
            />
          </div>

          {/* Bottom Bar */}
          <div className="flex items-center justify-between px-4 pb-3 pt-2">
            {/* Left Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                aria-label="Upload Files"
                title="Upload Files"
              >
                <Upload className="h-4 w-4" />
              </Button>

              <Button
                variant="outline"
                size="icon"
                aria-label="Search"
                title="Search"
              >
                <Search className="h-4 w-4" />
              </Button>

              {/* Agent Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    aria-label="Select Agent"
                    title="Select Agent"
                    className="relative"
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
                      onClick={() => setSelectedAgent(agent === selectedAgent ? null : agent)}
                      className="flex items-center justify-between"
                    >
                      <span>{agent}</span>
                      {selectedAgent === agent && <Check className="h-4 w-4 text-primary" />}
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

            {/* Right Actions */}
            <div className="flex items-center gap-2">
              {/* Model Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label="Select Model"
                    className="flex items-center gap-1.5 h-8 px-3 rounded-lg text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition"
                  >
                    <span>{selectedModel}</span>
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
                      className="flex items-center justify-between"
                    >
                      <span>{model}</span>
                      {selectedModel === model && <Check className="h-4 w-4 text-primary" />}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Send Button */}
              <Button
                onClick={handleSubmit}
                disabled={!message.trim()}
                size="icon"
                aria-label="Send Message"
              >
                <ArrowUp className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
