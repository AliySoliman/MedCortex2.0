import type { ChatMessage, ChatThread } from "@/services/chat";

const STORAGE_KEY_PREFIX = "medcortex_chat_v1_user_";

type SerializedMessage = Omit<ChatMessage, "timestamp"> & { timestamp: string };

type SerializedThread = Omit<ChatThread, "messages"> & { messages: SerializedMessage[] };

function storageKey(userId: number | string): string {
  return `${STORAGE_KEY_PREFIX}${userId}`;
}

export function saveChatState(
  userId: number | string,
  threads: ChatThread[],
  activeThreadId: string | null,
): void {
  if (typeof window === "undefined") return;
  const persistedThreads = threads.filter(
    (t) => t.id !== "__draft__" && t.messages.length > 0,
  );
  const serialized: SerializedThread[] = persistedThreads.map((t) => ({
    ...t,
    messages: t.messages.map((m) => ({
      ...m,
      timestamp:
        m.timestamp instanceof Date ? m.timestamp.toISOString() : String(m.timestamp),
    })),
  }));
  localStorage.setItem(
    storageKey(userId),
    JSON.stringify({
      threads: serialized,
      activeThreadId:
        activeThreadId && activeThreadId !== "__draft__" ? activeThreadId : null,
    }),
  );
}

export function loadChatState(userId: number | string): {
  threads: ChatThread[];
  activeThreadId: string | null;
} | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(storageKey(userId));
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as {
      threads: SerializedThread[];
      activeThreadId: string | null;
    };
    return {
      threads: (parsed.threads ?? []).map((t) => ({
        ...t,
        messages: (t.messages ?? []).map((m) => ({
          ...m,
          timestamp: new Date(m.timestamp),
        })),
      })),
      activeThreadId: parsed.activeThreadId ?? null,
    };
  } catch {
    return null;
  }
}

export function clearChatState(userId?: number | string): void {
  if (userId !== undefined) {
    localStorage.removeItem(storageKey(userId));
  } else {
    // Fallback: clear all keys belonging to any user (e.g. on logout when user id is not available)
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k?.startsWith(STORAGE_KEY_PREFIX)) keysToRemove.push(k);
    }
    keysToRemove.forEach((k) => localStorage.removeItem(k));
  }
}
