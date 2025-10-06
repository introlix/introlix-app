"use client";

import ChatInput from "@/components/chat-input";

export default function ChatPage() {
    const handleSend = (message: string) => {
        console.log("Message sent:", message);
    }
    
    return (
        <div className="flex h-full w-full items-center">
            {/* Input at bottom */}
            <ChatInput />
        </div>
    );
}