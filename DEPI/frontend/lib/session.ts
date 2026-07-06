import type { User } from "@/types/user";

const USER_KEY = "medcortex_user";

export function persistSession(token: string, user: User): void {
  localStorage.setItem("token", token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  localStorage.removeItem("token");
  localStorage.removeItem(USER_KEY);
}

export function firstNameFromUser(user: User | null): string {
  if (!user?.name?.trim()) return "there";
  return user.name.trim().split(/\s+/)[0] ?? "there";
}
