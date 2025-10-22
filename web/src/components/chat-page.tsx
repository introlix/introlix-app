"use client";

import { useCallback, useEffect, useRef } from "react";
import { useChat, useWorkspace } from "@/hooks/use-chat";
import { useStreaming } from "@/hooks/use-streaming";
import { type Message } from "@/lib/types";
import ChatInput from "@/components/chat-input";
import { ChatMessages } from "@/components/chat-messages";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, StopCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface ChatPageProps {
    workspaceId: string;
    chatId: string;
    initialPrompt?: string;
}

export default function ChatPage({ workspaceId, chatId, initialPrompt }: ChatPageProps) {
    const { data: chat, isLoading: chatLoading, error: chatError } = useChat(chatId);
    const { data: workspace } = useWorkspace(workspaceId);
    const queryClient = useQueryClient();
    const router = useRouter();
    const hasSubmittedInitialRef = useRef(false);

    const { streamingMessage, isStreaming, startStreaming, stopStreaming } = useStreaming({
        onComplete: async () => {
            await queryClient.invalidateQueries({ queryKey: ["chat", chatId] });
        },
        onError: (error) => {
            console.log(error);
            queryClient.invalidateQueries({ queryKey: ["chat", chatId] });
        },
    });

    const handleSendMessage = useCallback(
        async (data: {
            prompt: string;
            model: string;
            search: boolean;
            agent: string;
            files: File[];
        }) => {
            if (!chatId || !workspaceId) return;

            const userMessage: Message = {
                id: `temp-${Date.now()}`,
                role: "user",
                content: data.prompt,
                created_at: new Date().toISOString(),
            };

            queryClient.setQueryData(["chat", chatId], (old: any) => {
                if (!old) return old;
                return {
                    ...old,
                    messages: [...old.messages, userMessage],
                };
            });

            await startStreaming(workspaceId, chatId, {
                prompt: data.prompt,
                model: data.model,
                search: data.search,
                agent: data.agent,
            });
        },
        [chatId, workspaceId, queryClient, startStreaming]
    );

    // Auto-submit initial prompt
    useEffect(() => {
        if (
            initialPrompt && 
            !hasSubmittedInitialRef.current && 
            chat && 
            chat.messages.length === 0 &&
            !isStreaming
        ) {
            hasSubmittedInitialRef.current = true;
            
            // Remove prompt from URL
            router.replace(`/workspaces/${workspaceId}/chat/${chatId}`);
            
            // Submit the initial prompt
            handleSendMessage({
                prompt: initialPrompt,
                model: "auto",
                search: false,
                agent: "",
                files: [],
            });
        }
    }, [initialPrompt, chat, isStreaming, handleSendMessage, router, workspaceId, chatId]);

    if (chatLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (chatError || !chat) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center space-y-2">
                    <p className="text-lg font-medium">Chat not found</p>
                    <p className="text-sm text-muted-foreground">
                        This chat may have been deleted or doesn't exist.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full">
            <div className="border-b px-4 py-3 bg-background/95 backdrop-blur">
                <div className="max-w-3xl mx-auto flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                        <h1 className="text-lg font-semibold truncate">
                            {typeof chat.title === 'string' ? chat.title : JSON.stringify(chat.title) || "New Chat"}
                        </h1>
+                        {workspace && (
                            <p className="text-sm text-muted-foreground">
                                {typeof workspace.name === 'string' ? workspace.name : JSON.stringify(workspace.name)}
                            </p>
                        )}
                    </div>

                    {isStreaming && (
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={stopStreaming}
                            className="ml-4"
                        >
                            <StopCircle className="h-4 w-4 mr-2" />
                            Stop
                        </Button>
                    )}
                </div>
            </div>

            <ChatMessages
                messages={chat.messages}
                streamingMessage={streamingMessage}
                isLoading={isStreaming && !streamingMessage}
            />

            <div className="border-t bg-background p-4">
                <div className="max-w-3xl mx-auto">
                    <ChatInput onSubmit={handleSendMessage} disabled={isStreaming} />
                </div>
            </div>
        </div>
    );
}