export type TimeRangePreset =
  | "24h"
  | "7d"
  | "30d"
  | "90d"
  | "custom";

export type ResolvedTimeRange = {
  preset: TimeRangePreset;
  start: string;
  end: string;
};

type ResolveTimeRangeOptions = {
  now?: Date;
  customStart?: Date | string;
  customEnd?: Date | string;
};

const PRESET_DURATION_MS: Record<
  Exclude<TimeRangePreset, "custom">,
  number
> = {
  "24h": 24 * 60 * 60 * 1000,
  "7d": 7 * 24 * 60 * 60 * 1000,
  "30d": 30 * 24 * 60 * 60 * 1000,
  "90d": 90 * 24 * 60 * 60 * 1000,
};

function parseDate(
  value: Date | string | undefined,
  fieldName: string,
): Date {
  if (value === undefined) {
    throw new Error(`${fieldName} is required.`);
  }

  const date = value instanceof Date
    ? new Date(value.getTime())
    : new Date(value);

  if (Number.isNaN(date.getTime())) {
    throw new Error(`${fieldName} must be a valid date.`);
  }

  return date;
}

export function resolveTimeRange(
  preset: TimeRangePreset,
  options: ResolveTimeRangeOptions = {},
): ResolvedTimeRange {
  if (preset === "custom") {
    const start = parseDate(
      options.customStart,
      "Custom start",
    );
    const end = parseDate(
      options.customEnd,
      "Custom end",
    );

    if (start >= end) {
      throw new Error(
        "Custom start must be earlier than custom end.",
      );
    }

    return {
      preset,
      start: start.toISOString(),
      end: end.toISOString(),
    };
  }

  const end = options.now
    ? new Date(options.now.getTime())
    : new Date();

  if (Number.isNaN(end.getTime())) {
    throw new Error("Current time must be valid.");
  }

  const start = new Date(
    end.getTime() - PRESET_DURATION_MS[preset],
  );

  return {
    preset,
    start: start.toISOString(),
    end: end.toISOString(),
  };
}
