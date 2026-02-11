import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nao Translation Bridge",
  description: "Doctor-patient translation bridge with text and audio.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
