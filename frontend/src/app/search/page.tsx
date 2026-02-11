"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useMemo, useState } from "react";
import { api } from "@/lib/api";

type SearchItem = {
  message_id: string;
  conversation_id: string;
  role: "doctor" | "patient";
  created_at: string;
  snippet: string;
};

function mark(text: string, needle: string): string {
  if (!needle.trim()) {
    return text;
  }
  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return text.replace(new RegExp(`(${escaped})`, "ig"), "<mark>$1</mark>");
}

function SearchPageInner() {
  const params = useSearchParams();
  const defaultConversation = params.get("conversation_id") || "";

  const [query, setQuery] = useState("");
  const [conversationId, setConversationId] = useState(defaultConversation);
  const [items, setItems] = useState<SearchItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const hasItems = useMemo(() => items.length > 0, [items]);

  const onSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setError("Search query is required");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const result = await api.search(query.trim(), conversationId.trim() || undefined);
      setItems(result.items as SearchItem[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container column">
      <section className="card column">
        <div className="row wrap" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>Search Conversations</h2>
          <Link href="/" className="button secondary">Home</Link>
        </div>

        <form className="column" onSubmit={onSearch}>
          <input
            className="input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search symptom, diagnosis, medication..."
          />
          <input
            className="input"
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
            placeholder="Optional conversation UUID filter"
          />
          <button className="button" type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        {error ? <p className="error">{error}</p> : null}

        {hasItems ? (
          <div className="column">
            {items.map((item) => (
              <article key={item.message_id} className={`msg ${item.role}`}>
                <div className="msg-meta">
                  {item.role} | {new Date(item.created_at).toLocaleString()}
                </div>
                <div dangerouslySetInnerHTML={{ __html: mark(item.snippet, query) }} />
                <div style={{ marginTop: 10 }}>
                  <Link className="button secondary" href={`/chat/${item.conversation_id}#msg-${item.message_id}`}>
                    Open Message Context
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : (
          !loading && <p>No results yet.</p>
        )}
      </section>
    </main>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<main className="container">Loading search...</main>}>
      <SearchPageInner />
    </Suspense>
  );
}
