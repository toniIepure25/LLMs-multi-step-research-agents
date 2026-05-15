import type { Metadata } from "next";
import "./globals.css";
import { NeuralBackground } from "@/components/NeuralBackground";

export const metadata: Metadata = {
  title: "ASAR — Agentic Structured Autonomous Researcher",
  description:
    "Run the v0 ASAR research pipeline (plan → execute → memory → synthesize → verify) " +
    "backed by a locally fine-tuned Qwen-0.5B + LoRA adapter.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NeuralBackground />
        {children}
      </body>
    </html>
  );
}
