const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";
const TOKEN_KEY = "comintern.token";
export const UNAUTHORIZED_EVENT = "comintern:unauthorized";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage unavailable (private mode); the session just won't persist.
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
  }
}

function errorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return fallback;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const res = await fetch(`${API_URL}${API_PREFIX}${path}`, { ...init, headers });
  if (res.status === 401 && token) {
    setToken(null);
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, errorMessage(body.detail, res.statusText), body.detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const json = (body: unknown) => JSON.stringify(body);

export async function downloadDocument(id: number, filename: string) {
  const res = await fetch(`${API_URL}${API_PREFIX}/documents/${id}/download`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) throw new ApiError(res.status, "Download failed");
  const url = URL.createObjectURL(await res.blob());
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

export interface ChatSource {
  title: string;
  score: number;
}

export type ChatEvent =
  | { event: "progress"; data: { step: string } }
  | { event: "delta"; data: { text: string } }
  | { event: "payload"; data: { type: "sources"; value: ChatSource[] } }
  | { event: "final"; data: { conversation_id: number; message_id: number } }
  | { event: "error"; data: { code: string; detail: string } };

/** Ask the assistant and hand each server-sent event to `onEvent` as it arrives.
 * EventSource cannot POST or send the Authorization header, so the stream is read by hand. */
export async function streamChat(body: unknown, onEvent: (event: ChatEvent) => void) {
  const headers = new Headers({ "Content-Type": "application/json" });
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}${API_PREFIX}/chat/stream`, { method: "POST", headers, body: json(body) });
  if (!res.ok || !res.body) {
    const errorBody = await res.json().catch(() => ({}));
    throw new ApiError(res.status, errorMessage(errorBody.detail, res.statusText), errorBody.detail);
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    buffer += value.replaceAll("\r", "");
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      const event = block.match(/^event: (.*)$/m)?.[1];
      const data = block.match(/^data: (.*)$/m)?.[1];
      if (event && data) onEvent({ event, data: JSON.parse(data) } as ChatEvent);
    }
  }
}
