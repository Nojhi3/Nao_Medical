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
  const [role, setRole] = useState<"doctor" | "patient">("doctor");
  const [title, setTitle] = useState("");
  const [conversationId, setConversationId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const saveSession = (id: string, pickedRole: "doctor" | "patient", doctorLang: string, patientLang: string) => {
    localStorage.setItem(
      "nao_session",
      JSON.stringify({ conversationId: id, role: pickedRole, doctorLanguage: doctorLang, patientLanguage: patientLang }),
    );
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
      saveSession(conversation.id, role, doctorLanguage, patientLanguage);
      router.push(`/chat/${conversation.id}?role=${role}`);
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
    saveSession(conversationId.trim(), role, doctorLanguage, patientLanguage);
    router.push(`/chat/${conversationId.trim()}?role=${role}`);
  };

  return (
    <main className="container column">
      <section className="card column">
        <h1>Nao Translation Bridge</h1>
        <p>Doctor-patient translation with text and recorded audio.</p>

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
          <span>Your role</span>
          <select className="select" value={role} onChange={(e) => setRole(e.target.value as "doctor" | "patient") }>
            <option value="doctor">Doctor</option>
            <option value="patient">Patient</option>
          </select>
        </label>

        <label className="column">
          <span>Optional conversation title</span>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Follow-up visit" />
        </label>

        <div className="row wrap">
          <button className="button" onClick={onCreate} disabled={loading}>
            {loading ? "Creating..." : "Create Conversation"}
          </button>
        </div>

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
        <button className="button secondary" onClick={onJoin}>Join Conversation</button>

        {error ? <p className="error">{error}</p> : null}
      </section>
    </main>
  );
}
