import { en } from "./messages";

export type MessageKey = string;

function lookup(key: MessageKey): string {
  const parts = key.split(".");
  let value: unknown = en;
  for (const part of parts) {
    if (typeof value !== "object" || value === null || !(part in value)) {
      throw new Error(`missing i18n key: ${key}`);
    }
    value = (value as Record<string, unknown>)[part];
  }
  if (typeof value !== "string") {
    throw new Error(`i18n key is not a string: ${key}`);
  }
  return value;
}

export function t(key: MessageKey): string {
  return lookup(key);
}
