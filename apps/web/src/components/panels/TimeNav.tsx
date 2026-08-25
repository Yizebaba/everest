"use client";

import { useEffect, useRef, useState } from "react";

import { getForecast } from "@/api/client";
import { useApiFetch } from "@/state/useApiFetch";

export interface TimeNavProps {
  activeTime: string | null;
  onActiveTimeChange: (time: string | null) => void;
}

const STEP_MS = 750;

export function TimeNav({
  activeTime,
  onActiveTimeChange,
}: TimeNavProps): React.JSX.Element {
  const { data } = useApiFetch(() => getForecast());
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const times = [
    ...new Set((data?.records ?? []).map((record) => record.timestamp)),
  ].sort();

  const currentIndex = activeTime === null ? -1 : times.indexOf(activeTime);

  useEffect(() => {
    if (!playing) {
      return undefined;
    }
    if (times.length === 0) {
      setPlaying(false);
      return undefined;
    }
    timerRef.current = setInterval(() => {
      const index =
        activeTime === null ? 0 : Math.max(0, times.indexOf(activeTime));
      const next = (index + 1) % times.length;
      onActiveTimeChange(times[next]);
    }, STEP_MS);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, times, activeTime]);

  const step = (direction: 1 | -1): void => {
    if (times.length === 0) {
      return;
    }
    const index = activeTime === null ? -1 : times.indexOf(activeTime);
    const nextIndex =
      direction === 1
        ? (index + 1) % times.length
        : (index - 1 + times.length) % times.length;
    onActiveTimeChange(times[nextIndex]);
  };

  return (
    <section aria-label="Time navigation" className="time-nav">
      <button
        type="button"
        onClick={() => step(-1)}
        disabled={times.length === 0}
        aria-label="Previous valid time"
      >
        ‹
      </button>
      <button
        type="button"
        onClick={() => setPlaying((value) => !value)}
        disabled={times.length === 0}
        aria-pressed={playing}
      >
        {playing ? "⏸" : "▶"}
      </button>
      <button
        type="button"
        onClick={() => step(1)}
        disabled={times.length === 0}
        aria-label="Next valid time"
      >
        ›
      </button>
      <input
        type="range"
        min={0}
        max={Math.max(0, times.length - 1)}
        value={currentIndex < 0 ? 0 : currentIndex}
        aria-label="Forecast valid time"
        onChange={(event) =>
          onActiveTimeChange(times[Number(event.target.value)] ?? null)
        }
      />
      <span className="time-nav__value">{activeTime ?? "—"}</span>
      <style jsx>{`
        .time-nav {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .time-nav input {
          flex: 1;
        }
        .time-nav__value {
          font-size: 11px;
          color: #9aa5b8;
          min-width: 140px;
        }
      `}</style>
    </section>
  );
}
