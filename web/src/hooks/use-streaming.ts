/**
 * Streaming Chat Hook
 * 
 * This module provides a React hook for handling streaming chat responses.
 * It manages the streaming state, message accumulation, and cancellation.
 * 
 * Features:
 * - Real-time message streaming
 * - Abort/cancel capability
 * - Automatic state management
 * - Error handling
 * - Completion callbacks
 */

import { chatApi } from "@/lib/api";
import { useState, useCallback, useRef } from "react";

/**
 * Options for the streaming hook
 */
interface UseStreamingOptions {
  /** Callback when streaming completes */
  onComplete?: (fullMessage: string) => void;
  /** Callback when an error occurs */
  onError?: (error: Error) => void;
}

/**
 * Hook for managing streaming chat responses
 * 
 * @param options - Configuration options
 * @param options.onComplete - Called when streaming finishes with full message
 * @param options.onError - Called when an error occurs
 * @returns Object with streaming state and control functions
 * 
 * @example
 * ```tsx
 * const { streamingMessage, isStreaming, startStreaming, stopStreaming } = useStreaming({
 *   onComplete: (msg) => console.log('Done:', msg),
 *   onError: (err) => console.error(err)
 * });
 * 
 * // Start streaming
 * await startStreaming(workspaceId, chatId, { prompt: 'Hello', model: 'auto', search: false });
 * 
 * // Stop streaming
 * stopStreaming();
 * ```
 */
export function useStreaming({ onComplete, onError }: UseStreamingOptions = {}) {
  const [streamingMessage, setStreamingMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Start streaming a chat response
   * @param workspaceId - Workspace ID
   * @param chatId - Chat ID
   * @param data - Message data (prompt, model, search, agent)
   */
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

  /**
   * Stop the current streaming operation
   */
  const stopStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    setStreamingMessage("");
  }, []);

  return {
    /** Current accumulated message */
    streamingMessage,
    /** Whether streaming is in progress */
    isStreaming,
    /** Function to start streaming */
    startStreaming,
    /** Function to stop streaming */
    stopStreaming,
  };
}