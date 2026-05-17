import type {
  AnswerResponse,
  DocumentList,
  FarmerProfile,
  LegalDocument,
  SessionList,
  SessionWithMessages,
  TokenResponse,
  User,
} from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

const TOKEN_KEY = "agroconsult.token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  raw?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, raw, headers, ...rest } = options;
  const token = getToken();

  const finalHeaders: Record<string, string> = {
    ...(headers as Record<string, string> | undefined),
  };
  if (token) finalHeaders["Authorization"] = `Bearer ${token}`;

  let finalBody: BodyInit | undefined;
  if (body instanceof FormData) {
    finalBody = body;
  } else if (raw && typeof body === "string") {
    finalBody = body;
    finalHeaders["Content-Type"] = finalHeaders["Content-Type"] || "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    finalBody = JSON.stringify(body);
    finalHeaders["Content-Type"] = "application/json";
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: finalBody,
  });

  if (resp.status === 401) {
    clearToken();
  }

  if (!resp.ok) {
    let payload: unknown = null;
    try {
      payload = await resp.json();
    } catch {
      payload = await resp.text();
    }
    const message =
      (payload && typeof payload === "object" && "detail" in payload && typeof (payload as { detail: unknown }).detail === "string"
        ? (payload as { detail: string }).detail
        : null) || `Запрос завершился ошибкой ${resp.status}`;
    throw new ApiError(message, resp.status, payload);
  }

  if (resp.status === 204) return undefined as T;
  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return resp.json() as Promise<T>;
  return resp.text() as unknown as T;
}

// ---------- Auth ----------
export const auth = {
  async register(data: { email: string; password: string; full_name?: string }): Promise<TokenResponse> {
    return request<TokenResponse>("/api/v1/auth/register", { method: "POST", body: data });
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const form = new URLSearchParams({ username: email, password });
    return request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: form.toString(),
      raw: true,
    });
  },

  async me(): Promise<User> {
    return request<User>("/api/v1/auth/me");
  },
};

// ---------- Profile ----------
export const profile = {
  async get(): Promise<FarmerProfile> {
    return request<FarmerProfile>("/api/v1/profile");
  },
  async update(payload: Partial<FarmerProfile>): Promise<FarmerProfile> {
    return request<FarmerProfile>("/api/v1/profile", { method: "PUT", body: payload });
  },
};

// ---------- Chat ----------
export const chat = {
  async ask(question: string, session_id?: string): Promise<AnswerResponse> {
    return request<AnswerResponse>("/api/v1/chat/ask", {
      method: "POST",
      body: { question, session_id },
    });
  },
  async sessions(): Promise<SessionList> {
    return request<SessionList>("/api/v1/chat/sessions");
  },
  async session(id: string): Promise<SessionWithMessages> {
    return request<SessionWithMessages>(`/api/v1/chat/sessions/${id}`);
  },
  async deleteSession(id: string): Promise<void> {
    return request<void>(`/api/v1/chat/sessions/${id}`, { method: "DELETE" });
  },
};

// ---------- Documents ----------
export const documents = {
  async list(params: { limit?: number; offset?: number; is_active?: boolean } = {}): Promise<DocumentList> {
    const query = new URLSearchParams();
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.offset !== undefined) query.set("offset", String(params.offset));
    if (params.is_active !== undefined) query.set("is_active", String(params.is_active));
    const qs = query.toString();
    return request<DocumentList>(`/api/v1/documents${qs ? `?${qs}` : ""}`);
  },
  async get(id: string): Promise<LegalDocument> {
    return request<LegalDocument>(`/api/v1/documents/${id}`);
  },
};

// ---------- Feedback ----------
export const feedback = {
  async submit(message_id: string, kind: "positive" | "negative" | "hallucination" | "outdated", comment?: string) {
    return request("/api/v1/feedback", {
      method: "POST",
      body: { message_id, kind, comment },
    });
  },
};
