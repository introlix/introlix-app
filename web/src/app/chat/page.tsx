"use client";

import ChatInput from "@/components/chat-input";
import { Card } from "@/components/ui/card";

export default function ChatPage() {
    return (
        <div className="relative flex flex-col items-center justify-center h-full w-full md:p-4">
            {/* Header */}
            <div className="text-center mb-6 md:mb-8">
                <h1 className="text-3xl font-semibold tracking-tight">
                    Let’s have some fun!
                </h1>
                <p className="text-sm text-muted-foreground">
                    Workspace: <span className="font-medium text-foreground">General</span>
                </p>
            </div>

            {/* Chat Input — Center on desktop, Bottom on mobile */}
            <div className="w-full md:relative fixed bottom-0 left-0 md:bottom-auto md:left-auto md:flex md:justify-center">
                <Card className="w-full md:max-w-3xl p-4 shadow-sm border-t md:border rounded-none md:rounded-2xl">
                    <ChatInput />
                </Card>
            </div>
        </div>
    );
}
