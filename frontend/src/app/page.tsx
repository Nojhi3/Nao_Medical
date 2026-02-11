"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "es", label: "Spanish" },
  { code: "zh", label: "Mandarin Chinese" },
  { code: "ar", label: "Arabic" },
  { code: "hi", label: "Hindi" },
  { code: "bn", label: "Bengali" },
  { code: "pt", label: "Portuguese" },
  { code: "ru", label: "Russian" },
];

export default function Home() {
  const router = useRouter();
  const [doctorLanguage, setDoctorLanguage] = useState("en");
  const [patientLanguage, setPatientLanguage] = useState("es");
  const [title, setTitle] = useState("");
  const [conversationId, setConversationId] = useState("");
  const [joinRole, setJoinRole] = useState<"doctor" | "patient">("patient");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [createdConversationId, setCreatedConversationId] = useState("");

  const saveSession = (id: string, pickedRole: "doctor" | "patient", doctorLang: string, patientLang: string) => {
    localStorage.setItem(
      "nao_session",
      JSON.stringify({ conversationId: id, role: pickedRole, doctorLanguage: doctorLang, patientLanguage: patientLang }),
    );
  };

  const openAsRole = (id: string, pickedRole: "doctor" | "patient") => {
    saveSession(id, pickedRole, doctorLanguage, patientLanguage);
    router.push(`/chat/${id}?role=${pickedRole}`);
  };

  const copyLink = async (id: string, pickedRole: "doctor" | "patient") => {
    const url = `${window.location.origin}/chat/${id}?role=${pickedRole}`;
    await navigator.clipboard.writeText(url);
  };

  const onCreate = async () => {
    setError("");
    setLoading(true);
    try {
      const conversation = await api.createConversation({
        doctor_language: doctorLanguage,
        patient_language: patientLanguage,
        title: title || undefined,
      });
      setCreatedConversationId(conversation.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create conversation");
    } finally {
      setLoading(false);
    }
  };

  const onJoin = () => {
    if (!conversationId.trim()) {
      setError("Conversation ID is required");
      return;
    }
    setError("");
    openAsRole(conversationId.trim(), joinRole);
  };

  return (
    <main className="container column">
      <section className="card column hero">
        <h1>Nao Translation Bridge</h1>
        <p className="muted">Doctor-patient translation with text and recorded audio.</p>

        <div className="grid-2">
          <label className="column">
            <span>Doctor language</span>
            <select className="select" value={doctorLanguage} onChange={(e) => setDoctorLanguage(e.target.value)}>
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label}
                </option>
              ))}
            </select>
          </label>

          <label className="column">
            <span>Patient language</span>
            <select className="select" value={patientLanguage} onChange={(e) => setPatientLanguage(e.target.value)}>
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="column">
          <span>Optional conversation title</span>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Follow-up visit" />
        </label>

        <button className="button" onClick={onCreate} disabled={loading}>
          {loading ? "Creating..." : "Create Conversation"}
        </button>

        {createdConversationId ? (
          <section className="card column info-block">
            <h3 style={{ margin: 0 }}>Conversation Ready</h3>
            <p className="muted" style={{ margin: 0 }}>
              Share a role-specific link to avoid UUID confusion.
            </p>
            <code className="mono">{createdConversationId}</code>
            <div className="grid-2">
              <div className="column">
                <span className="badge">Doctor Access</span>
                <div className="row wrap">
                  <button className="button secondary" onClick={() => openAsRole(createdConversationId, "doctor")}>
                    Open as Doctor
                  </button>
                  <button className="button ghost" onClick={() => copyLink(createdConversationId, "doctor")}>
                    Copy Doctor Link
                  </button>
                </div>
              </div>
              <div className="column">
                <span className="badge">Patient Access</span>
                <div className="row wrap">
                  <button className="button secondary" onClick={() => openAsRole(createdConversationId, "patient")}>
                    Open as Patient
                  </button>
                  <button className="button ghost" onClick={() => copyLink(createdConversationId, "patient")}>
                    Copy Patient Link
                  </button>
                </div>
              </div>
            </div>
          </section>
        ) : null}

        <hr style={{ borderColor: "var(--border)", width: "100%" }} />

        <label className="column">
          <span>Join existing conversation ID</span>
          <input
            className="input"
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
            placeholder="Paste conversation UUID"
          />
        </label>
        <label className="column">
          <span>Join as</span>
          <select className="select" value={joinRole} onChange={(e) => setJoinRole(e.target.value as "doctor" | "patient")}>
            <option value="patient">Patient</option>
            <option value="doctor">Doctor</option>
          </select>
        </label>
        <button className="button secondary" onClick={onJoin}>Join Conversation</button>

        {error ? <p className="error">{error}</p> : null}
      </section>
    </main>
  );
}
