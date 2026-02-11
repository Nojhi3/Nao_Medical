export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type Role = "doctor" | "patient";
export type Modality = "text" | "audio";

export type Conversation = {
  id: string;
  title: string | null;
  doctor_language: string;
  patient_language: string;
  created_at: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: Role;
  modality: Modality;
  original_text: string | null;
  translated_text: string | null;
  transcript_text: string | null;
  audio_url: string | null;
  source_language: string;
  target_language: string;
  created_at: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers || {});
  if (!(options?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export const api = {
  createConversation: (payload: { doctor_language: string; patient_language: string; title?: string }) =>
    request<Conversation>("/api/conversations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getConversation: (id: string) => request<Conversation>(`/api/conversations/${id}`),

  listMessages: (id: string, afterId?: string) =>
    request<{ items: Message[] }>(
      `/api/conversations/${id}/messages?limit=50${afterId ? `&after_id=${encodeURIComponent(afterId)}` : ""}`,
    ),

  sendTextMessage: (payload: {
    conversation_id: string;
    role: Role;
    text: string;
    source_language: string;
    target_language: string;
  }) =>
    request<Message>("/api/messages/text", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  presignAudio: (payload: { conversation_id: string; mime_type: string }) =>
    request<{ upload_url: string; file_url: string; object_key: string }>("/api/audio/presign", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  finalizeAudio: (payload: {
    conversation_id: string;
    role: Role;
    audio_url: string;
    source_language: string;
    target_language: string;
  }) =>
    request<Message>("/api/messages/audio/finalize", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  search: (q: string, conversationId?: string) =>
    request<{ items: Array<{ message_id: string; conversation_id: string; role: Role; created_at: string; snippet: string }> }>(
      `/api/search?q=${encodeURIComponent(q)}${conversationId ? `&conversation_id=${encodeURIComponent(conversationId)}` : ""}`,
    ),

  summarize: (conversationId: string, style: "concise" | "clinical" = "concise") =>
    request<{ summary: string; extracted: Record<string, string[]> }>(`/api/conversations/${conversationId}/summary`, {
      method: "POST",
      body: JSON.stringify({ style }),
    }),
};
