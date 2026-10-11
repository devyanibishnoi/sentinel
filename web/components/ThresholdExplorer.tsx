"use client";

import { useMemo, useState } from "react";
import { ThresholdCurveData } from "@/lib/types";
import { StatTile } from "@/components/StatTile";

const WIDTH = 640;
const HEIGHT = 320;
const PAD_LEFT = 52;
const PAD_BOTTOM = 36;
const PAD_TOP = 16;
const PAD_RIGHT = 16;
const Y_MAX = 0.5; // fixed headroom above the observed max precision, keeps the axis stable

const plotW = WIDTH - PAD_LEFT - PAD_RIGHT;
const plotH = HEIGHT - PAD_TOP - PAD_BOTTOM;

function xOf(recall: number) {
  return PAD_LEFT + recall * plotW;
}
function yOf(precision: number) {
  return PAD_TOP + (1 - precision / Y_MAX) * plotH;
}

export function ThresholdExplorer({ data }: { data: ThresholdCurveData }) {
  const { curve, deployed_confidence_threshold, n_total, n_fraud } = data;

  const deployedIndex = useMemo(() => {
    let best = 0;
    let bestDiff = Infinity;
    curve.forEach((c, i) => {
      const diff = Math.abs(c.threshold - deployed_confidence_threshold);
      if (diff < bestDiff) {
        bestDiff = diff;
        best = i;
      }
    });
    return best;
  }, [curve, deployed_confidence_threshold]);

  const [index, setIndex] = useState(deployedIndex);
  const current = curve[index];
  const deployedPoint = curve[deployedIndex];

  const pathD = curve
    .map((c, i) => `${i === 0 ? "M" : "L"} ${xOf(c.recall).toFixed(2)} ${yOf(c.precision).toFixed(2)}`)
    .join(" ");

  return (
    <div className="rounded-lg border border-border bg-surface p-6 mb-10">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-medium">Try it: precision/recall at any confidence threshold</h3>
        <span className="text-xs font-mono text-text-faint">threshold = {current.threshold.toFixed(4)}</span>
      </div>
      <p className="text-xs text-text-muted mb-4">
        Drag to pick any population-score cutoff and watch the tradeoff, computed live from the real held-out test
        set, not illustrative numbers.
      </p>

      <input
        type="range"
        min={0}
        max={curve.length - 1}
        value={index}
        onChange={(e) => setIndex(Number(e.target.value))}
        className="w-full mb-6"
        style={{ accentColor: "var(--accent)" }}
        aria-label="Confidence threshold"
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatTile value={current.precision.toFixed(3)} label="precision" accent />
        <StatTile value={current.recall.toFixed(3)} label="recall" accent />
        <StatTile value={current.fpr.toFixed(4)} label="false positive rate" />
        <StatTile
          value={current.n_flagged.toLocaleString()}
          label={`of ${n_total.toLocaleString()} flagged`}
        />
      </div>

      <svg width="100%" height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="overflow-visible">
        <line x1={PAD_LEFT} y1={PAD_TOP} x2={PAD_LEFT} y2={HEIGHT - PAD_BOTTOM} stroke="var(--border)" strokeWidth={1} />
        <line
          x1={PAD_LEFT}
          y1={HEIGHT - PAD_BOTTOM}
          x2={WIDTH - PAD_RIGHT}
          y2={HEIGHT - PAD_BOTTOM}
          stroke="var(--border)"
          strokeWidth={1}
        />

        {[0, 0.25, 0.5].map((v) => (
          <g key={v}>
            <line x1={PAD_LEFT - 4} y1={yOf(v)} x2={PAD_LEFT} y2={yOf(v)} stroke="var(--border)" strokeWidth={1} />
            <text x={PAD_LEFT - 8} y={yOf(v) + 3} textAnchor="end" fontSize={10} fill="var(--text-faint)">
              {v.toFixed(2)}
            </text>
          </g>
        ))}
        {[0, 0.5, 1].map((v) => (
          <g key={v}>
            <line
              x1={xOf(v)}
              y1={HEIGHT - PAD_BOTTOM}
              x2={xOf(v)}
              y2={HEIGHT - PAD_BOTTOM + 4}
              stroke="var(--border)"
              strokeWidth={1}
            />
            <text x={xOf(v)} y={HEIGHT - PAD_BOTTOM + 16} textAnchor="middle" fontSize={10} fill="var(--text-faint)">
              {v.toFixed(1)}
            </text>
          </g>
        ))}
        <text x={(PAD_LEFT + WIDTH - PAD_RIGHT) / 2} y={HEIGHT - 4} textAnchor="middle" fontSize={11} fill="var(--text-muted)">
          recall
        </text>
        <text
          x={14}
          y={(PAD_TOP + HEIGHT - PAD_BOTTOM) / 2}
          textAnchor="middle"
          fontSize={11}
          fill="var(--text-muted)"
          transform={`rotate(-90 14 ${(PAD_TOP + HEIGHT - PAD_BOTTOM) / 2})`}
        >
          precision
        </text>

        <path d={pathD} fill="none" stroke="var(--accent)" strokeWidth={2} strokeLinecap="round" />

        <circle
          cx={xOf(deployedPoint.recall)}
          cy={yOf(deployedPoint.precision)}
          r={4}
          fill="var(--bg)"
          stroke="var(--text-muted)"
          strokeWidth={1.5}
        />
        <text x={xOf(deployedPoint.recall) + 8} y={yOf(deployedPoint.precision) - 8} fontSize={10} fill="var(--text-muted)">
          deployed system
        </text>

        <line
          x1={xOf(current.recall)}
          y1={yOf(current.precision)}
          x2={xOf(current.recall)}
          y2={HEIGHT - PAD_BOTTOM}
          stroke="var(--accent)"
          strokeWidth={1}
          strokeDasharray="3 3"
          opacity={0.5}
        />
        <line
          x1={PAD_LEFT}
          y1={yOf(current.precision)}
          x2={xOf(current.recall)}
          y2={yOf(current.precision)}
          stroke="var(--accent)"
          strokeWidth={1}
          strokeDasharray="3 3"
          opacity={0.5}
        />
        <circle cx={xOf(current.recall)} cy={yOf(current.precision)} r={5} fill="var(--accent)" />
      </svg>

      <p className="text-xs text-text-faint mt-4 max-w-2xl">
        This curve sweeps only the population-score confidence threshold, computed from the real{" "}
        {n_total.toLocaleString()}-row held-out test set ({n_fraud.toLocaleString()} fraud transactions). It
        doesn&apos;t reproduce the full gated decision: the deployed Orchestrator also triggers independently on ring
        membership and separately gates decline-vs-review by exposure (transaction amount), neither of which this
        chart varies.
      </p>
    </div>
  );
}
