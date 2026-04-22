import { NextResponse } from "next/server";

export const runtime = 'edge';

// Returns a short-lived WebRTC conversation token for the ElevenLabs ConvAI
// agent. The API key stays on the server — the browser never sees it.
//
// On Cloudflare Pages + next-on-pages, env vars are exposed via the async
// `getRequestContext()` import from `@cloudflare/next-on-pages`, NOT via
// `process.env` (which is not populated in the Workers edge runtime).
// We try getRequestContext first and fall back to process.env for local dev.

async function readEnv(): Promise<{ agentId?: string; apiKey?: string }> {
  try {
    // @ts-expect-error — optional dependency, only present on CF Pages build
    const { getRequestContext } = await import("@cloudflare/next-on-pages");
    const { env } = getRequestContext();
    return { agentId: env.VOICE_AGENT_ID, apiKey: env.VOICE_API_KEY };
  } catch {
    // Local dev (next dev) — process.env works
    return {
      agentId: process.env.VOICE_AGENT_ID,
      apiKey: process.env.VOICE_API_KEY,
    };
  }
}

export async function GET() {
  const { agentId, apiKey } = await readEnv();

  if (!agentId || !apiKey) {
    return NextResponse.json(
      {
        error: "VOICE_AGENT_ID or VOICE_API_KEY is not set",
        hasAgentId: !!agentId,
        hasApiKey: !!apiKey,
      },
      { status: 500 }
    );
  }

  try {
    const res = await fetch(
      `https://api.elevenlabs.io/v1/convai/conversation/token?agent_id=${agentId}`,
      { headers: { "xi-api-key": apiKey }, cache: "no-store" }
    );

    if (!res.ok) {
      const text = await res.text();
      console.error("ElevenLabs error:", res.status, text);
      return NextResponse.json(
        { error: `ElevenLabs API error: ${res.status}`, body: text.slice(0, 200) },
        { status: 502 }
      );
    }

    const data = await res.json();
    return NextResponse.json({ conversationToken: data.token });
  } catch (error) {
    console.error("Error:", error);
    return NextResponse.json(
      {
        error: "Failed to get conversation token",
        detail: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}
