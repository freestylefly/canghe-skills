import path from "node:path";
import { readFile } from "node:fs/promises";
import type { CliArgs } from "../types";

type CangheContentItem =
  | { type: "text"; text: string }
  | { type: "image_url"; image_url: { url: string } };

type CangheResponse = {
  choices?: Array<{
    message?: {
      content?: string | Array<{ type?: string; text?: string }>;
    };
  }>;
};

export function getDefaultModel(): string {
  return process.env.CANGHE_IMAGE_MODEL || "gemini-3-pro-image-preview";
}

function getApiKey(): string | null {
  return process.env.CANGHE_API_KEY || null;
}

function getBaseUrl(): string {
  const base = process.env.CANGHE_BASE_URL || "https://api.canghe.ai/v1";
  return base.replace(/\/+$/g, "");
}

function isHttpUrl(value: string): boolean {
  return /^https?:\/\//i.test(value);
}

function getMimeType(filename: string): string {
  const ext = path.extname(filename).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  if (ext === ".gif") return "image/gif";
  return "image/png";
}

async function toImageUrl(ref: string): Promise<string> {
  if (isHttpUrl(ref)) return ref;

  const bytes = await readFile(ref);
  const mimeType = getMimeType(ref);
  const encoded = bytes.toString("base64");
  return `data:${mimeType};base64,${encoded}`;
}

async function buildContent(prompt: string, refs: string[]): Promise<CangheContentItem[]> {
  const content: CangheContentItem[] = [{ type: "text", text: prompt }];

  for (const ref of refs) {
    const url = await toImageUrl(ref);
    content.push({
      type: "image_url",
      image_url: { url },
    });
  }

  return content;
}

function extractBase64FromText(text: string): string | null {
  const dataUriMatch = text.match(/data:image\/[a-zA-Z0-9.+-]+;base64,([A-Za-z0-9+/=\s]+)/);
  if (dataUriMatch?.[1]) {
    return dataUriMatch[1].replace(/\s+/g, "");
  }

  const plainBase64Match = text.match(/([A-Za-z0-9+/=\s]{256,})/);
  if (plainBase64Match?.[1]) {
    return plainBase64Match[1].replace(/\s+/g, "");
  }

  return null;
}

function extractMessageContent(content: CangheResponse["choices"]): string {
  const messageContent = content?.[0]?.message?.content;
  if (typeof messageContent === "string") return messageContent;
  if (Array.isArray(messageContent)) {
    return messageContent
      .map((item) => item?.text || "")
      .filter(Boolean)
      .join("\n");
  }
  return "";
}

export async function generateImage(prompt: string, model: string, args: CliArgs): Promise<Uint8Array> {
  const apiKey = getApiKey();
  if (!apiKey) throw new Error("CANGHE_API_KEY is required");

  const content = await buildContent(prompt, args.referenceImages);

  const res = await fetch(`${getBaseUrl()}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [{ role: "user", content }],
      max_tokens: 4096,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Canghe API error (${res.status}): ${err}`);
  }

  const result = (await res.json()) as CangheResponse;
  const rawContent = extractMessageContent(result.choices);
  const base64 = extractBase64FromText(rawContent);

  if (!base64) {
    throw new Error("No base64 image found in Canghe response");
  }

  return Uint8Array.from(Buffer.from(base64, "base64"));
}
