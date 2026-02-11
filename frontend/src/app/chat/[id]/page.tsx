"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { api, Conversation, Message, Role } from "@/lib/api";

function fmtDate(value: string): string {
  const dt = new Date(value);
  return dt.toLocaleString();
}

function isFallbackTranslation(msg: Message): boolean {
  if (msg.modality !== "text") {
    return false;
  }
  const original = (msg.original_text || "").trim();
  const translated = (msg.translated_text || "").trim();
  return Boolean(original) && original === translated;
}

function displayTextForViewer(msg: Message, viewerRole: Role): string {
  const isOwn = msg.role === viewerRole;
  if (msg.modality === "audio") {
    if (isOwn) {
      return msg.transcript_text || "[Audio message]";
    }
    return msg.translated_text || msg.transcript_text || "[Audio message]";
  }
  if (isOwn) {
    return msg.original_text || msg.transcript_text || "";
  }
  return msg.translated_text || msg.original_text || msg.transcript_text || "";
}

export default function ChatPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const conversationId = params.id;
  const roleParam = searchParams.get("role");
  const role = (roleParam === "doctor" || roleParam === "patient" ? roleParam : "doctor") as Role;

  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [summary, setSummary] = useState<{ summary: string; extracted: Record<string, string[]> } | null>(null);

  const [recording, setRecording] = useState(false);
  const [uploadingAudio, setUploadingAudio] = useState(false);
  const [copied, setCopied] = useState<"" | "doctor" | "patient">("");

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const stopRef = useRef(false);
  const failureRef = useRef(0);

  const lastMessageId = messages.length ? messages[messages.length - 1].id : undefined;

  const sourceLanguage = useMemo(() => (role === "doctor" ? conversation?.doctor_language : conversation?.patient_language), [role, conversation]);
  const targetLanguage = useMemo(() => (role === "doctor" ? conversation?.patient_language : conversation?.doctor_language), [role, conversation]);
  const alternateRole: Role = role === "doctor" ? "patient" : "doctor";

  useEffect(() => {
    let mounted = true;
    async function boot() {
      try {
        setLoading(true);
        const [conv, initial] = await Promise.all([
          api.getConversation(conversationId),
          api.listMessages(conversationId),
        ]);
        if (!mounted) {
          return;
        }
        setConversation(conv);
        setMessages(initial.items);
      } catch (e) {
        if (mounted) {
          setError(e instanceof Error ? e.message : "Failed to load conversation");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    boot();
    return () => {
      mounted = false;
      stopRef.current = true;
    };
  }, [conversationId]);

  useEffect(() => {
    if (!conversation) {
      return;
    }
    stopRef.current = false;

    const poll = async () => {
      if (stopRef.current) {
        return;
      }
      try {
        const latestId = lastMessageId;
        const result = await api.listMessages(conversationId, latestId);
        if (result.items.length > 0) {
          setMessages((prev) => {
            const seen = new Set(prev.map((m) => m.id));
            const next = [...prev];
            for (const item of result.items) {
              if (!seen.has(item.id)) {
                next.push(item);
              }
            }
            return next;
          });
        }
        failureRef.current = 0;
      } catch {
        failureRef.current += 1;
      }

      const delay = failureRef.current >= 3 ? 4000 : 2000;
      window.setTimeout(poll, delay);
    };

    const timer = window.setTimeout(poll, 2000);
    return () => {
      stopRef.current = true;
      clearTimeout(timer);
    };
  }, [conversation, conversationId, lastMessageId]);

  const sendText = async () => {
    if (!text.trim() || !sourceLanguage || !targetLanguage) {
      return;
    }
    setSending(true);
    setError("");
    try {
      const msg = await api.sendTextMessage({
        conversation_id: conversationId,
        role,
        text: text.trim(),
        source_language: sourceLanguage,
        target_language: targetLanguage,
      });
      setMessages((prev) => [...prev, msg]);
      setText("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const startRecording = async () => {
    setError("");
    if (!navigator.mediaDevices || typeof MediaRecorder === "undefined") {
      setError("Audio recording is not supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      rec.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      rec.onstop = async () => {
        try {
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          if (blob.size === 0 || !sourceLanguage || !targetLanguage) {
            return;
          }
          setUploadingAudio(true);

          const presign = await api.presignAudio({ conversation_id: conversationId, mime_type: "audio/webm" });

          const uploadRes = await fetch(presign.upload_url, {
            method: "PUT",
            headers: { "Content-Type": "audio/webm" },
            body: blob,
          });

          if (!uploadRes.ok) {
            throw new Error("Audio upload failed");
          }

          const msg = await api.finalizeAudio({
            conversation_id: conversationId,
            role,
            audio_url: presign.file_url,
            source_language: sourceLanguage,
            target_language: targetLanguage,
          });
          setMessages((prev) => [...prev, msg]);
        } catch (e) {
          setError(e instanceof Error ? e.message : "Failed to process audio message");
        } finally {
          setUploadingAudio(false);
          for (const track of stream.getTracks()) {
            track.stop();
          }
        }
      };

      rec.start();
      recorderRef.current = rec;
      setRecording(true);
    } catch {
      setError("Microphone permission denied or unavailable");
    }
  };

  const stopRecording = () => {
    if (recorderRef.current && recording) {
      recorderRef.current.stop();
      setRecording(false);
    }
  };

  const generateSummary = async () => {
    setSummarizing(true);
    setError("");
    try {
      const result = await api.summarize(conversationId);
      setSummary(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Summary failed");
    } finally {
      setSummarizing(false);
    }
  };

  const copyRoleLink = async (pickedRole: Role) => {
    const url = `${window.location.origin}/chat/${conversationId}?role=${pickedRole}`;
    await navigator.clipboard.writeText(url);
    setCopied(pickedRole);
    window.setTimeout(() => setCopied(""), 1200);
  };

  if (loading) {
    return <main className="container">Loading conversation...</main>;
  }

  if (!conversation) {
    return <main className="container">Conversation not found.</main>;
  }

  return (
    <main className="container column">
      <section className="card column">
        <div className="row wrap" style={{ justifyContent: "space-between" }}>
          <div className="column" style={{ gap: 4 }}>
            <h2 style={{ margin: 0 }}>{conversation.title || "Conversation"}</h2>
            <span className="badge">Role: {role}</span>
            <span className="badge">
              {conversation.doctor_language} -&gt; {conversation.patient_language}
            </span>
            <code className="mono">{conversationId}</code>
          </div>
          <div className="row wrap">
            <Link className="button secondary" href={`/search?conversation_id=${conversationId}`}>
              Search
            </Link>
            <button className="button ghost" onClick={() => copyRoleLink(role)}>
              {copied === role ? "Copied" : `Copy ${role} link`}
            </button>
            <button className="button ghost" onClick={() => copyRoleLink(alternateRole)}>
              {copied === alternateRole ? "Copied" : `Copy ${alternateRole} link`}
            </button>
            <button className="button secondary" onClick={() => router.push("/")}>Exit</button>
          </div>
        </div>

        <div className="messages card" style={{ padding: 10 }}>
          {messages.map((msg) => (
            <article className={`msg ${msg.role}`} key={msg.id} id={`msg-${msg.id}`}>
              <div className="msg-meta">
                {msg.role} | {msg.modality} | {fmtDate(msg.created_at)}
              </div>
              <p className="msg-main">
                <strong>{msg.role === role ? "Sent:" : "Received:"}</strong>{" "}
                {displayTextForViewer(msg, role)}
              </p>
              <details className="details-box">
                <summary>View Original / Translated</summary>
                {msg.original_text ? (
                  <p><strong>Original ({msg.source_language}):</strong> {msg.original_text}</p>
                ) : null}
                {msg.transcript_text ? (
                  <p><strong>Transcript ({msg.source_language}):</strong> {msg.transcript_text}</p>
                ) : null}
                {msg.translated_text ? (
                  <p><strong>Translated ({msg.target_language}):</strong> {msg.translated_text}</p>
                ) : null}
                {msg.audio_url ? (
                  <audio controls preload="none" style={{ width: "100%" }}>
                    <source src={msg.audio_url} type="audio/webm" />
                  </audio>
                ) : null}
              </details>
              {isFallbackTranslation(msg) ? (
                <p className="fallback-note">
                  Translation fallback used (provider unavailable/rate-limited).
                </p>
              ) : null}
            </article>
          ))}
        </div>

        <div className="column">
          <label className="column">
            <span>Type message</span>
            <textarea
              className="textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={3}
              placeholder="Enter a message"
            />
          </label>
          <div className="row wrap">
            <button className="button" disabled={sending || uploadingAudio} onClick={sendText}>
              {sending ? "Sending..." : "Send Text"}
            </button>
            {!recording ? (
              <button className="button secondary" disabled={uploadingAudio} onClick={startRecording}>
                {uploadingAudio ? "Processing audio..." : "Start Recording"}
              </button>
            ) : (
              <button className="button secondary" onClick={stopRecording}>Stop Recording</button>
            )}
            <button className="button secondary" disabled={summarizing} onClick={generateSummary}>
              {summarizing ? "Generating..." : "Generate Summary"}
            </button>
          </div>
          {error ? <p className="error">{error}</p> : null}
        </div>
      </section>

      {summary ? (
        <section className="card column">
          <h3>Conversation Summary</h3>
          <p>{summary.summary}</p>
          <div className="grid-2">
            <div>
              <h4>Symptoms</h4>
              <ul>{(summary.extracted.symptoms || []).map((item, idx) => <li key={`s-${idx}`}>{item}</li>)}</ul>
            </div>
            <div>
              <h4>Diagnoses</h4>
              <ul>{(summary.extracted.diagnoses || []).map((item, idx) => <li key={`d-${idx}`}>{item}</li>)}</ul>
            </div>
            <div>
              <h4>Medications</h4>
              <ul>{(summary.extracted.medications || []).map((item, idx) => <li key={`m-${idx}`}>{item}</li>)}</ul>
            </div>
            <div>
              <h4>Follow-up</h4>
              <ul>{(summary.extracted.follow_up || []).map((item, idx) => <li key={`f-${idx}`}>{item}</li>)}</ul>
            </div>
          </div>
        </section>
      ) : null}

      <p style={{ color: "#6b7280", fontSize: 12 }}>
        This tool assists communication and is not a diagnostic system.
      </p>
    </main>
  );
}
