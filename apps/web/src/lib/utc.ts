const UTC_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$/;

export function isUtcIso(value: string): boolean {
  if (!UTC_RE.test(value)) {
    return false;
  }
  const date = new Date(value);
  return !Number.isNaN(date.getTime()) && date.toISOString().endsWith("Z");
}

export function isUtcZeroOffset(value: string): boolean {
  return value.endsWith("Z") || value.endsWith("+00:00");
}

export function validateUtcRange(
  start: string | undefined,
  end: string | undefined,
): string | null {
  if (start !== undefined && (!isUtcIso(start) || !isUtcZeroOffset(start))) {
    return "start must be UTC ISO-8601 with zero offset";
  }
  if (end !== undefined && (!isUtcIso(end) || !isUtcZeroOffset(end))) {
    return "end must be UTC ISO-8601 with zero offset";
  }
  if (start && end && start > end) {
    return "start must not exceed end";
  }
  return null;
}
