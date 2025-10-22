import { chatApi } from "@/lib/api";
import { useState, useCallback, useRef } from "react";

interface UseStreamingOptions {
  onComplete?: (fullMessage: string) => void;
  onError?: (error: Error) => void;
}

export function useStreaming({ onComplete, onError }: UseStreamingOptions = {}) {
  const [streamingMessage, setStreamingMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStreaming = useCallback(
    async (
      workspaceId: string,
      chatId: string,
      data: {
        prompt: string;
        model: string;
        search: boolean;
        agent: string;
      }
    ) => {
      try {
        setIsStreaming(true);
        setStreamingMessage("");

        // Create abort controller for cancellation
        abortControllerRef.current = new AbortController();

        let fullResponse = "";
        const stream = chatApi.sendMessage(workspaceId, chatId, data);

        for await (const chunk of stream) {
          // Check if aborted
          if (abortControllerRef.current?.signal.aborted) {
            break;
          }

          fullResponse += chunk;
          setStreamingMessage(fullResponse);
        }

        onComplete?.(fullResponse);
        setStreamingMessage("");
      } catch (error) {
        console.error("Streaming error:", error);
        onError?.(error as Error);
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [onComplete, onError]
  );

  const stopStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    setStreamingMessage("");
  }, []);

  return {
    streamingMessage,
    isStreaming,
    startStreaming,
    stopStreaming,
  };
}