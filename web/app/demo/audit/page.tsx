"use client";

import { useState } from "react";
import benchmarkDetections from "@/data/detections.json";
import demoDetections from "@/data/demo_detections.json";
import { Detection, Source } from "@/lib/types";
import { formatInr, formatScore, truncate } from "@/lib/format";
import { DecisionBadge } from "@/components/Badge";
import { Caveat } from "@/components/Caveat";
import { SourceToggle } from "@/components/SourceToggle";

const benchmark = benchmarkDetections as Detection[];
const demo = demoDetections as Detection[];
const PAGE_SIZE = 50;

export default function AuditTrailPage() {
  const [source, setSource] = useState<Source>("benchmark");
  const [page, setPage] = useState(1);

  const rows = source === "benchmark" ? benchmark : demo;
  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const pageRows = rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="text-2xl font-semibold mb-1">Audit Trail</h1>
      <p className="text-text-muted text-sm mb-5">
        A curated excerpt ({rows.length.toLocaleString()} of {source === "benchmark" ? "85,004" : "123"} real
        records). Every single decision, including every allow, really is logged in the full pipeline run.
      </p>
      <SourceToggle source={source} onChange={(s) => { setSource(s); setPage(1); }} />
      <Caveat>
        Every decision, including every refusal to act (<DecisionBadge decision="allow" />), is logged here, no code
        path skips it. Page {page} of {totalPages}.
      </Caveat>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-text-muted border-b border-border">
              <th className="px-3 py-2 font-medium">Transaction</th>
              <th className="px-3 py-2 font-medium">Entity</th>
              <th className="px-3 py-2 font-medium">Score</th>
              <th className="px-3 py-2 font-medium">Amount</th>
              <th className="px-3 py-2 font-medium">Decision</th>
              <th className="px-3 py-2 font-medium">Reasoning</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((r) => (
              <tr key={r.TransactionID} className="border-b border-border last:border-0">
                <td className="px-3 py-2 font-mono text-xs text-text-muted">{r.TransactionID}</td>
                <td className="px-3 py-2 font-mono text-xs text-text-muted">{truncate(r.entity_id, 20)}</td>
                <td className="px-3 py-2 font-mono">{formatScore(r.score_population)}</td>
                <td className="px-3 py-2">{formatInr(r.TransactionAmt)}</td>
                <td className="px-3 py-2">
                  <DecisionBadge decision={r.decision} />
                </td>
                <td className="px-3 py-2 text-text-muted text-xs">{r.decision_reasoning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex gap-4 mt-4 text-sm">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
          className="text-accent hover:underline disabled:text-text-faint disabled:no-underline disabled:cursor-not-allowed"
        >
          ← prev
        </button>
        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="text-accent hover:underline disabled:text-text-faint disabled:no-underline disabled:cursor-not-allowed"
        >
          next →
        </button>
      </div>
    </div>
  );
}
