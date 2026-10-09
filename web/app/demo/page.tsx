"use client";

import { useState } from "react";
import benchmarkDetections from "@/data/detections.json";
import demoDetections from "@/data/demo_detections.json";
import { Detection, Source } from "@/lib/types";
import { formatInr, formatScore, truncate } from "@/lib/format";
import { DecisionBadge } from "@/components/Badge";
import { Caveat } from "@/components/Caveat";
import { DecisionLegend } from "@/components/DecisionLegend";
import { SourceToggle } from "@/components/SourceToggle";
import { ExplainPanel } from "@/components/ExplainPanel";
import Link from "next/link";

const benchmark = benchmarkDetections as Detection[];
const demo = demoDetections as Detection[];

export default function DetectionFeedPage() {
  const [source, setSource] = useState<Source>("benchmark");
  const [selected, setSelected] = useState<Detection | null>(null);

  const rows = source === "benchmark" ? benchmark : demo;
  const shown = source === "benchmark" ? rows.filter((d) => d.decision !== "allow") : rows;
  const flaggedCount = benchmark.filter((d) => d.decision !== "allow").length;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="text-2xl font-semibold mb-1">Detection Feed</h1>
      <p className="text-text-muted text-sm mb-5">
        A curated excerpt of the real results, not the full 85,004-row file. See the{" "}
        <Link href="/" className="text-accent hover:underline">
          case study
        </Link>{" "}
        for how to run the full pipeline yourself.
      </p>
      <SourceToggle source={source} onChange={(s) => { setSource(s); setSelected(null); }} />
      {source === "benchmark" ? (
        <Caveat>
          Showing flagged detections (decline/review) from the <strong className="text-text">benchmark</strong>{" "}
          (held-out test) stream only: {flaggedCount.toLocaleString()} of 85,004 total test transactions were
          flagged.
        </Caveat>
      ) : (
        <Caveat tone="warning">
          Synthetic, illustrative transactions. Never used for training, never contributes to any reported metric.
          Showing all {demo.length} demo transactions.
        </Caveat>
      )}
      <DecisionLegend />
      <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-6 items-start">
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-text-muted border-b border-border">
                <th className="px-3 py-2.5 font-medium">Entity</th>
                <th className="px-3 py-2.5 font-medium">Pop. score</th>
                <th className="px-3 py-2.5 font-medium">Amount</th>
                <th className="px-3 py-2.5 font-medium">Decision</th>
                <th className="px-3 py-2.5 font-medium">Typology</th>
                <th className="px-3 py-2.5 font-medium">Ring</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((d) => (
                <tr
                  key={d.TransactionID}
                  onClick={() => setSelected(d)}
                  className={`cursor-pointer border-b border-border last:border-0 hover:bg-surface-raised transition-colors ${
                    selected?.TransactionID === d.TransactionID ? "bg-surface-raised" : ""
                  }`}
                >
                  <td className="px-3 py-2.5 font-mono text-xs text-text-muted">{truncate(d.entity_id, 22)}</td>
                  <td className="px-3 py-2.5 font-mono tabular-nums">{formatScore(d.score_population)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{formatInr(d.TransactionAmt)}</td>
                  <td className="px-3 py-2.5">
                    <DecisionBadge decision={d.decision} />
                  </td>
                  <td className="px-3 py-2.5 text-text-muted text-xs">{d.typology_tag ?? "–"}</td>
                  <td className="px-3 py-2.5 text-xs">
                    {d.ring_cluster_id ? (
                      <span className="text-accent">{d.ring_cluster_id}</span>
                    ) : (
                      <span className="text-text-faint">–</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ExplainPanel d={selected} />
      </div>
    </div>
  );
}
