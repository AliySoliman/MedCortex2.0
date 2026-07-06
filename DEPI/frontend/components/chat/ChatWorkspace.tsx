"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { LayoutDashboard, LogOut, MoreVertical, Plus, Search, PanelLeftClose, PanelLeft } from "lucide-react";

import {
  exportThreadSummaryAsPdf,
  exportVisitNotes,
} from "@/lib/chat-export";
import { loadChatState, saveChatState } from "@/lib/chat-storage";
import { clearSession, firstNameFromUser, getStoredUser } from "@/lib/session";
import type { ChatThread } from "@/services/chat";
import type { User } from "@/types/user";

import ChatBox from "./ChatBox";
import Dashboard from "./Dashboard";

const DRAFT_THREAD_ID = "__draft__";

const DRAFT_THREAD: ChatThread = {
  id: DRAFT_THREAD_ID,
  title: "New chat",
  messages: [],
  updatedAt: 0,
};

function newThread(): ChatThread {
  const id = crypto.randomUUID();
  return { id, title: "New chat", messages: [], updatedAt: Date.now(), pinned: false };
}

function createDraftThread(): ChatThread {
  return { ...DRAFT_THREAD };
}

function getRealThreads(threads: ChatThread[]): ChatThread[] {
  return threads.filter((thread) => thread.id !== DRAFT_THREAD_ID);
}

function getInitialWorkspaceState(): {
  user: User | null;
  threads: ChatThread[];
  activeThreadId: string;
} {
  return {
    user: null,
    threads: [createDraftThread()],
    activeThreadId: DRAFT_THREAD_ID,
  };
}

function groupThreadsByRecency(threads: ChatThread[]) {
  const now = new Date();
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startYesterday = startToday - 86400000;
  const startWeek = startToday - 7 * 86400000;
  const sorted = [...threads].sort((a, b) => b.updatedAt - a.updatedAt);
  const today: ChatThread[] = [];
  const yesterday: ChatThread[] = [];
  const week: ChatThread[] = [];
  const older: ChatThread[] = [];
  for (const t of sorted) {
    if (t.id === DRAFT_THREAD_ID) continue;
    if (t.updatedAt >= startToday) today.push(t);
    else if (t.updatedAt >= startYesterday) yesterday.push(t);
    else if (t.updatedAt >= startWeek) week.push(t);
    else older.push(t);
  }
  const groups: { label: string; items: ChatThread[] }[] = [];
  if (today.length) groups.push({ label: "Today", items: today });
  if (yesterday.length) groups.push({ label: "Yesterday", items: yesterday });
  if (week.length) groups.push({ label: "7 days", items: week });
  if (older.length) groups.push({ label: "Older", items: older });
  return groups;
}

function sortPinnedThreads(threads: ChatThread[]) {
  return [...threads]
    .filter((thread) => thread.pinned)
    .sort((a, b) => b.updatedAt - a.updatedAt);
}

export default function ChatWorkspace() {
  const router = useRouter();
  const skipSaveOnce = useRef(true);
  const draftThreadIdRef = useRef<string | null>(null);
  const [initialWorkspaceState] = useState(getInitialWorkspaceState);
  const [user, setUser] = useState<User | null>(initialWorkspaceState.user);
  const [threads, setThreads] = useState<ChatThread[]>(initialWorkspaceState.threads);
  const [activeThreadId, setActiveThreadId] = useState<string>(initialWorkspaceState.activeThreadId);
  const [search, setSearch] = useState("");
  const [menuThreadId, setMenuThreadId] = useState<string | null>(null);
  const [view, setView] = useState<"chat" | "dashboard">("chat");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    const storedUser = getStoredUser();
    if (!storedUser) {
      return;
    }

    const saved = loadChatState(storedUser.id);
    const timeoutId = window.setTimeout(() => {
      setUser(storedUser);
      setThreads([createDraftThread(), ...(saved?.threads ?? []).filter((t) => t.messages.length > 0)]);
      setActiveThreadId(DRAFT_THREAD_ID);
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, []);

  useEffect(() => {
    if (skipSaveOnce.current) {
      skipSaveOnce.current = false;
      return;
    }
    if (user) {
      saveChatState(user.id, getRealThreads(threads), activeThreadId);
    }
  }, [threads, activeThreadId, user]);

  useEffect(() => {
    if (!menuThreadId) return;
    const close = () => setMenuThreadId(null);
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [menuThreadId]);

  const activeThread = useMemo(() => {
    if (activeThreadId === DRAFT_THREAD_ID) {
      return threads.find((thread) => thread.id === DRAFT_THREAD_ID) ?? createDraftThread();
    }
    return threads.find((thread) => thread.id === activeThreadId) ?? null;
  }, [threads, activeThreadId]);

  const filteredThreads = useMemo(() => {
    const q = search.trim().toLowerCase();
    const list = getRealThreads(threads);
    if (!q) return list;
    return list.filter((t) => t.title.toLowerCase().includes(q));
  }, [threads, search]);

  const pinnedThreads = useMemo(() => sortPinnedThreads(filteredThreads), [filteredThreads]);
  const grouped = useMemo(
    () => groupThreadsByRecency(filteredThreads.filter((thread) => !thread.pinned)),
    [filteredThreads],
  );
  const realThreadCount = useMemo(() => getRealThreads(threads).length, [threads]);

  const handleNewChat = useCallback(() => {
    draftThreadIdRef.current = null;
    setThreads((prev) => [createDraftThread(), ...getRealThreads(prev)]);
    setActiveThreadId(DRAFT_THREAD_ID);
    setSearch("");
    setView("chat");
  }, []);

  const handleSelectThread = useCallback((id: string) => {
    setActiveThreadId(id);
    setView("chat");
  }, []);

  const commitMessages = useCallback((threadId: string, messages: ChatThread["messages"]) => {
    const resolvedThreadId =
      threadId === DRAFT_THREAD_ID ? draftThreadIdRef.current ?? DRAFT_THREAD_ID : threadId;

    setThreads((prev) => {
      const timestamp = Date.now();
      const realThreads = getRealThreads(prev);
      const existingIndex = realThreads.findIndex((thread) => thread.id === resolvedThreadId);

      if (existingIndex >= 0) {
        const nextThreads = [...realThreads];
        nextThreads[existingIndex] = {
          ...nextThreads[existingIndex]!,
          messages,
          updatedAt: timestamp,
        };
        return [createDraftThread(), ...nextThreads];
      }

      if (messages.length === 0) {
        return [createDraftThread(), ...realThreads];
      }

      const fallbackTitle = messages[0]?.content.trim().slice(0, 56) || "New chat";
      return [
        createDraftThread(),
        {
          id: resolvedThreadId,
          title: fallbackTitle,
          messages,
          updatedAt: timestamp,
          pinned: false,
        },
        ...realThreads,
      ];
    });
  }, []);

  const setThreadTitle = useCallback((threadId: string, title: string) => {
    const trimmed = title.trim().slice(0, 56) || "New chat";
    if (threadId === DRAFT_THREAD_ID) {
      const createdThread = newThread();
      draftThreadIdRef.current = createdThread.id;
      setActiveThreadId(createdThread.id);
      setThreads((prev) => [
        createDraftThread(),
        { ...createdThread, title: trimmed },
        ...getRealThreads(prev),
      ]);
      return;
    }

    setThreads((prev) => [
      createDraftThread(),
      ...getRealThreads(prev).map((thread) =>
        thread.id === threadId ? { ...thread, title: trimmed, updatedAt: Date.now() } : thread,
      ),
    ]);
  }, []);

  const renameThread = useCallback((id: string) => {
    const thread = getRealThreads(threads).find((item) => item.id === id);
    if (!thread) return;

    const nextTitle = window.prompt("Rename this conversation", thread.title)?.trim();
    if (!nextTitle) return;

    setThreads((prev) => [
      createDraftThread(),
      ...getRealThreads(prev).map((item) =>
        item.id === id ? { ...item, title: nextTitle.slice(0, 56), updatedAt: item.updatedAt } : item,
      ),
    ]);
    setMenuThreadId(null);
  }, [threads]);

  const togglePinThread = useCallback((id: string) => {
    setThreads((prev) => [
      createDraftThread(),
      ...getRealThreads(prev).map((item) =>
        item.id === id ? { ...item, pinned: !item.pinned } : item,
      ),
    ]);
    setMenuThreadId(null);
  }, []);

  const deleteThread = useCallback((id: string) => {
    setMenuThreadId(null);
    setThreads((prev) => {
      const filtered = getRealThreads(prev).filter((thread) => thread.id !== id);
      setActiveThreadId((currentId) => (currentId === id ? DRAFT_THREAD_ID : currentId));
      return [createDraftThread(), ...filtered];
    });
  }, []);

  const handleLogout = useCallback(() => {
    clearSession();
    router.push("/login");
  }, [router]);

  const handleExportPdf = useCallback(() => {
    if (activeThread && activeThread.messages.length > 0) {
      exportThreadSummaryAsPdf(activeThread);
    }
  }, [activeThread]);

  const handleExportVisitNotes = useCallback(() => {
    if (activeThread && activeThread.messages.length > 0) {
      exportVisitNotes(activeThread);
    }
  }, [activeThread]);

  const firstName = firstNameFromUser(user);

  return (
    <div className="flex relative h-screen flex-col overflow-hidden bg-[#fafafa] text-[#1a1a1a] md:flex-row">
      <aside
        className={`flex max-h-[38vh] shrink-0 flex-col border-b border-[#ebebef] bg-[#f3f3f4] transition-all duration-300 overflow-hidden md:max-h-none md:h-full md:border-b-0 md:border-r ${isSidebarOpen ? "w-full md:w-[260px] p-4" : "hidden md:flex md:w-[68px] py-4 px-2"
          }`}
      >
        {!isSidebarOpen ? (
          // --- MINI SIDEBAR (COLLAPSED STATE) ---
          <div className="flex h-full w-full flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => setIsSidebarOpen(true)}
              className="flex h-12 w-12 shrink-0 cursor-pointer items-center justify-center rounded-xl text-[#8f8f95] hover:bg-[#e4e4ea] hover:text-[#111] transition-colors"
              title="Open sidebar"
              aria-label="Open sidebar"
            >
              <PanelLeft className="h-5 w-5 pointer-events-none" />
            </button>

            <button
              type="button"
              onClick={() => {
                handleNewChat();
                setIsSidebarOpen(true);
              }}
              className="flex flex-col h-14 w-14 shrink-0 cursor-pointer items-center justify-center rounded-xl bg-[#0d0d0d] text-white hover:bg-[#222] transition-colors mt-2"
              title="New chat"
              aria-label="New chat"
            >
              <Plus className="h-4 w-4 pointer-events-none mb-1" strokeWidth={2.5} />
              <span className="text-[10px] font-medium leading-none pointer-events-none text-center px-1 text-white">New chat</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setView("dashboard");
                setIsSidebarOpen(true);
              }}
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg transition-colors mt-2 ${view === "dashboard" ? "bg-[#f4eeff] text-[#6f4ef2]" : "text-[#8f8f95] hover:bg-[#e4e4ea] hover:text-[#111]"
                }`}
              title="Dashboard"
              aria-label="Dashboard"
            >
              <LayoutDashboard className="h-5 w-5 pointer-events-none" />
            </button>

            <button
              type="button"
              onClick={() => setIsSidebarOpen(true)}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-[#8f8f95] hover:bg-[#e4e4ea] hover:text-[#111] transition-colors"
              title="Search and Recent Chats"
              aria-label="Search and Recent Chats"
            >
              <Search className="h-5 w-5 pointer-events-none" />
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="mt-auto flex h-10 w-10 shrink-0 items-center justify-center rounded-full hover:opacity-80 transition-opacity"
              title="Log out"
              aria-label="Log out"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#0d0d0d] text-sm font-semibold text-white pointer-events-none">
                {(user?.name?.trim()?.[0] ?? user?.email?.[0] ?? "?").toUpperCase()}
              </div>
            </button>
          </div>
        ) : (
          // --- FULL SIDEBAR (OPEN STATE) ---
          <div className="flex h-full w-full flex-col min-w-[228px]">
            <div className="mb-5 flex items-center justify-between gap-2 px-1">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#f4eeff] text-sm text-[#6f4ef2]">
                  ✦
                </div>
                <span className="text-[1.65rem] font-medium tracking-tight text-[#111]">MedCortex</span>
              </div>
              <button
                type="button"
                onClick={() => setIsSidebarOpen(false)}
                className="flex h-12 w-12 shrink-0 cursor-pointer items-center justify-center rounded-xl text-[#8f8f95] hover:bg-[#e4e4ea] hover:text-[#111] transition-colors z-50"
                title="Close sidebar"
                aria-label="Close sidebar"
              >
                <PanelLeftClose className="h-5 w-5 pointer-events-none" />
              </button>
            </div>

            {/* Dashboard button */}
            <button
              type="button"
              onClick={() => setView("dashboard")}
              className={`mb-2 flex h-11 w-full shrink-0 items-center gap-2.5 rounded-xl px-3.5 text-sm font-medium transition ${view === "dashboard"
                ? "bg-[#f4eeff] text-[#6f4ef2] shadow-inner"
                : "text-[#3a3a42] hover:bg-white/80 hover:text-[#6f4ef2]"
                }`}
            >
              <LayoutDashboard className="h-4 w-4 shrink-0" strokeWidth={2} />
              <span className="truncate">Dashboard</span>
              <span className="ml-auto rounded-full bg-[#6f4ef2] px-1.5 py-0.5 text-[10px] font-semibold text-white leading-none shrink-0">
                NEW
              </span>
            </button>

            <button
              type="button"
              onClick={handleNewChat}
              className="mb-3 flex h-11 w-full shrink-0 cursor-pointer items-center justify-center gap-2 rounded-xl bg-[#0d0d0d] text-sm font-medium text-white transition hover:bg-[#222]"
            >
              <Plus className="h-4 w-4 shrink-0 pointer-events-none text-white" strokeWidth={2} />
              <span className="pointer-events-none text-white">New chat</span>
            </button>

            <div className="relative mb-4 shrink-0">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8f8f95]" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search"
                className="w-full rounded-lg border border-[#e4e4ea] bg-[#fafafb] py-2.5 pl-9 pr-3 text-sm text-[#1a1a1a] placeholder:text-[#b4b4bc] outline-none transition focus:border-[#c5a6ff] focus:ring-1 focus:ring-[#c5a6ff]/40"
                aria-label="Search chat history"
              />
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto w-full">
              <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-[#8f8f95]">
                History
              </p>
              {pinnedThreads.length === 0 && grouped.length === 0 ? (
                <p className="px-2 text-sm text-[#8f8f95]">
                  {search.trim() && realThreadCount > 0
                    ? "No chats match your search."
                    : "No chats yet. Start with New chat."}
                </p>
              ) : (
                <div className="space-y-4">
                  {pinnedThreads.length > 0 && (
                    <div>
                      <p className="mb-1.5 px-2 text-[11px] font-medium uppercase tracking-wide text-[#a8a8b0]">
                        Pinned
                      </p>
                      <div className="space-y-0.5 w-full">
                        {pinnedThreads.map((t) => (
                          <div
                            key={t.id}
                            className={`group relative flex items-center gap-0.5 rounded-lg pl-2.5 pr-1 transition ${t.id === activeThreadId ? "bg-white shadow-sm" : "hover:bg-white/70"
                              }`}
                          >
                            <button
                              type="button"
                              onClick={() => handleSelectThread(t.id)}
                              className={`min-w-0 flex-1 truncate py-2 pr-1 text-left text-[14px] ${t.id === activeThreadId
                                ? "font-medium text-[#111]"
                                : "text-[#3a3a42]"
                                }`}
                            >
                              📌 {t.title}
                            </button>
                            <div className="relative shrink-0">
                              <button
                                type="button"
                                className="flex h-8 w-8 items-center justify-center rounded-lg text-[#8f8f95] transition hover:bg-[#f0f0f3] hover:text-[#111]"
                                aria-haspopup="menu"
                                aria-expanded={menuThreadId === t.id}
                                aria-label={`More options for ${t.title}`}
                                onPointerDown={(e) => e.stopPropagation()}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setMenuThreadId((cur) => (cur === t.id ? null : t.id));
                                }}
                              >
                                <MoreVertical className="h-4 w-4 pointer-events-none" strokeWidth={2} />
                              </button>
                              {menuThreadId === t.id && (
                                <div
                                  role="menu"
                                  className="absolute right-0 top-full z-30 mt-0.5 w-40 overflow-hidden rounded-xl border border-[#ebebef] bg-white py-1 shadow-lg"
                                  onPointerDown={(e) => e.stopPropagation()}
                                >
                                  <button
                                    type="button"
                                    role="menuitem"
                                    className="w-full px-3 py-2 text-left text-sm text-[#3a3a42] transition hover:bg-[#f7f7fb] cursor-pointer"
                                    onPointerDown={(e) => {
                                      e.stopPropagation();
                                      renameThread(t.id);
                                    }}
                                  >
                                    Rename chat
                                  </button>
                                  <button
                                    type="button"
                                    role="menuitem"
                                    className="w-full px-3 py-2 text-left text-sm text-[#3a3a42] transition hover:bg-[#f7f7fb] cursor-pointer"
                                    onPointerDown={(e) => {
                                      e.stopPropagation();
                                      togglePinThread(t.id);
                                    }}
                                  >
                                    Unpin chat
                                  </button>
                                  <button
                                    type="button"
                                    role="menuitem"
                                    className="w-full px-3 py-2 text-left text-sm text-red-600 transition hover:bg-red-50 cursor-pointer"
                                    onPointerDown={(e) => {
                                      e.stopPropagation();
                                      deleteThread(t.id);
                                    }}
                                  >
                                    Delete chat
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {grouped.map((group) => (
                    <div key={group.label}>
                      <p className="mb-1.5 px-2 text-[11px] font-medium uppercase tracking-wide text-[#a8a8b0]">
                        {group.label}
                      </p>
                      <div className="space-y-0.5 w-full">
                        {group.items.map((t) => (
                          <div
                            key={t.id}
                            className={`group relative flex items-center gap-0.5 rounded-lg pl-2.5 pr-1 transition ${t.id === activeThreadId ? "bg-white shadow-sm" : "hover:bg-white/70"
                              }`}
                          >
                            <button
                              type="button"
                              onClick={() => handleSelectThread(t.id)}
                              className={`min-w-0 flex-1 truncate py-2 pr-1 text-left text-[14px] ${t.id === activeThreadId
                                ? "font-medium text-[#111]"
                                : "text-[#3a3a42]"
                                }`}
                            >
                              {t.title}
                            </button>
                            <div className="relative shrink-0">
                              <button
                                type="button"
                                className="flex h-8 w-8 items-center justify-center rounded-lg text-[#8f8f95] transition hover:bg-[#f0f0f3] hover:text-[#111]"
                                aria-haspopup="menu"
                                aria-expanded={menuThreadId === t.id}
                                aria-label={`More options for ${t.title}`}
                                onPointerDown={(e) => e.stopPropagation()}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setMenuThreadId((cur) => (cur === t.id ? null : t.id));
                                }}
                              >
                                <MoreVertical className="h-4 w-4 pointer-events-none" strokeWidth={2} />
                              </button>
                              {menuThreadId === t.id && (
                                <div
                                  role="menu"
                                  className="absolute right-0 top-full z-30 mt-0.5 w-40 overflow-hidden rounded-xl border border-[#ebebef] bg-white py-1 shadow-lg"
                                  onPointerDown={(e) => e.stopPropagation()}
                                >
                                  <button
                                    type="button"
                                    role="menuitem"
                                    className="w-full px-3 py-2 text-left text-sm text-[#3a3a42] transition hover:bg-[#f7f7fb] cursor-pointer"
                                    onPointerDown={(e) => {
                                      e.stopPropagation();
                                      renameThread(t.id);
                                    }}
                                  >
                                    Rename chat
                                  </button>
                                  <button
                                    type="button"
                                    role="menuitem"
                                    className="w-full px-3 py-2 text-left text-sm text-[#3a3a42] transition hover:bg-[#f7f7fb] cursor-pointer"
                                    onPointerDown={(e) => {
                                      e.stopPropagation();
                                      togglePinThread(t.id);
                                    }}
                                  >
                                    Pin chat
                                  </button>
                                  <button
                                    type="button"
                                    role="menuitem"
                                    className="w-full px-3 py-2 text-left text-sm text-red-600 transition hover:bg-red-50 cursor-pointer"
                                    onPointerDown={(e) => {
                                      e.stopPropagation();
                                      deleteThread(t.id);
                                    }}
                                  >
                                    Delete chat
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-auto border-t border-[#ebebef] pt-3 shrink-0">
              <div className="flex items-center gap-2.5 rounded-xl px-2 py-2">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#0d0d0d] text-sm font-semibold text-white">
                  {(user?.name?.trim()?.[0] ?? user?.email?.[0] ?? "?").toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-[#111]">
                    {user?.name?.trim() || "Signed in"}
                  </p>
                  <p className="truncate text-xs text-[#8f8f95]">{user?.email ?? ""}</p>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="shrink-0 rounded-lg p-2 text-[#8f8f95] transition hover:bg-white hover:text-[#111]"
                  title="Log out"
                  aria-label="Log out"
                >
                  <LogOut className="h-4 w-4 pointer-events-none" />
                </button>
              </div>
            </div>
          </div>
        )}
      </aside>

      <main className="flex min-w-0 flex-1 flex-col relative w-full h-full bg-white">
        {view === "dashboard" ? (
          <Dashboard user={user} threads={getRealThreads(threads)} />
        ) : activeThread ? (
          <ChatBox
            threadId={activeThread.id}
            threadTitle={activeThread.title}
            messages={activeThread.messages}
            firstName={firstName}
            onCommitMessages={commitMessages}
            onFirstUserMessageTitle={setThreadTitle}
            onExportPdf={handleExportPdf}
            onExportVisitNotes={handleExportVisitNotes}
          />
        ) : null}
      </main>
    </div>
  );
}
