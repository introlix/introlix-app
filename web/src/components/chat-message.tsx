"use client";
import { Message } from '@/lib/types';
import { Check, ChevronDown, ChevronUp, Copy, Info, Loader2, Search } from 'lucide-react';
import React, { useMemo, useState } from 'react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from './ui/button';
import { ButtonGroup } from './ui/button-group';

interface ChatMessageProps {
    message: Message;
    isStreaming?: boolean;
}

interface ToolCall {
    name: string;
    status: "running" | "completed" | "error";
    result?: string;
}

export const ChatMessage = ({ message, isStreaming = false }: ChatMessageProps) => {
    const [copied, setCopied] = useState(false);
    const [isThinkingOpen, setIsThinkingOpen] = useState(false);
    const isUser = message.role === "user";

    const { text, thoughts, tools } = useMemo(() => {
        if (isUser) return { text: message.content, thoughts: [], tools: [] };

        const thoughts: string[] = [];
        const tools: ToolCall[] = [];
        let text = "";

        const lines = message.content.split("\n");

        lines.forEach((line, index) => {
            if (!line.trim()) return;

            try {
                // Try to parse as JSON first
                const data = JSON.parse(line);

                if (data.type === "thinking") {
                    thoughts.push(data.content);
                } else if (data.type === "tool_calls_start") {
                    if (Array.isArray(data.tools)) {
                        data.tools.forEach((t: string) =>
                            tools.push({ name: t, status: "running" })
                        );
                    }
                } else if (data.type === "tool_result") {
                    const toolIndex = tools.findIndex(
                        t => t.name === data.tool && t.status === "running"
                    );
                    if (toolIndex !== -1) {
                        tools[toolIndex].status = "completed";
                        tools[toolIndex].result = data.content;
                    } else {
                        // If we missed the start or it's a duplicate
                        tools.push({
                            name: data.tool,
                            status: data.content.startsWith("Error") ? "error" : "completed",
                            result: data.content
                        });
                    }
                } else if (data.type === "answer_chunk" || data.type === "answer") {
                    text += data.content;
                } else if (data.type === "error") {
                    text += `\n> Error: ${data.content}\n`;
                } else {
                    // Unknown JSON type, treat as text if it has content
                    if (data.content) text += data.content;
                }
            } catch (e) {
                // Not valid JSON
                if (isStreaming && index === lines.length - 1 && line.trim().startsWith('{')) {
                    return;
                }
                // Otherwise treat as plain text
                text += line + "\n";
            }
        });

        return { text, thoughts, tools };
    }, [message.content, message.role, isStreaming, isUser]);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div>
            {
                message.role === "user" ? (
                    <div className='flex flex-col gap-1 items-end'>
                        <div className='group relative inline-flex gap-2 bg-muted/50 max-w-[75ch] px-6 py-3 rounded-l-2xl rounded-tr-2xl rounded-br-lg my-6 border border-accent'>{text}</div>
                    </div>
                ) : (
                    <div>
                        <div className="">
                            {thoughts.length > 0 && (
                                <Collapsible
                                    open={isThinkingOpen}
                                    onOpenChange={setIsThinkingOpen}
                                    className="mb-4"
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        <CollapsibleTrigger asChild>
                                            <Button
                                                variant={'ghost'}
                                                className="text-sm text-primary flex items-center gap-1 cursor-pointer hover:bg-transparent"
                                            >
                                                Show Reason {isThinkingOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                            </Button>
                                        </CollapsibleTrigger>
                                        <Tooltip>
                                            <TooltipTrigger asChild>
                                                <Info className="h-4 w-4 text-muted-foreground" />
                                            </TooltipTrigger>
                                            <TooltipContent>
                                                <p>This is a plan that shows what the LLM is trying to do and what it has done.</p>
                                            </TooltipContent>
                                        </Tooltip>
                                    </div>
                                    <CollapsibleContent className="overflow-hidden data-[state=open]:animate-slide-down data-[state=closed]:animate-slide-up">
                                        <div className="p-4 ml-3 pl-4 border-l border-accent rounded-md space-y-2">
                                            {thoughts.map((thought, idx) => (
                                                <div key={idx} className="italic text-sm text-muted-foreground">
                                                    {thought}
                                                </div>
                                            ))}
                                        </div>
                                    </CollapsibleContent>
                                </Collapsible>
                            )}
                        </div>
                        <div className="mb-4 ml-4 space-y-2">
                            {tools.map((tool, i) => (
                                <div
                                    key={i}
                                    className="flex items-center gap-2 text-xs text-muted-foreground bg-background/50 border rounded-md px-3 py-2 w-fit"
                                >
                                    <Search className="h-3.5 w-3.5" />
                                    <span>Used tool: <span className="font-medium">{tool.name}</span></span>
                                    {tool.status === "running" ? (
                                        <Loader2 className="h-3 w-3 animate-spin ml-1" />
                                    ) : tool.status === "error" ? (
                                        <span className="text-destructive ml-1">Failed</span>
                                    ) : (
                                        <Check className="h-3.5 w-3.5 text-green-500 ml-1" />
                                    )}
                                </div>
                            ))}
                        </div>
                        <div className="ml-4">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {text}
                            </ReactMarkdown>
                        </div>
                        <ButtonGroup className="flex flex-wrap items-center gap-1 ml-2 my-4">
                            <Button
                                size="icon"
                                variant="ghost"
                                className="cursor-pointer"
                                onClick={handleCopy}
                            >
                                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                            </Button>
                            <Button
                                variant={"ghost"}
                                size="sm"
                                className="cursor-default text-muted-foreground"
                            >
                                { message.model && "Model: " + message.model }
                            </Button>
                        </ButtonGroup>
                    </div>
                )
            }
        </div>
    )
}
