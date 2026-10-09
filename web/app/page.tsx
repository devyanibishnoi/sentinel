import Link from "next/link";
import { StatTile } from "@/components/StatTile";
import { PipelineDiagram } from "@/components/PipelineDiagram";
import { BarChart } from "@/components/BarChart";
import { SplitBar } from "@/components/SplitBar";
import comparisonData from "@/data/comparison.json";
import { HEADLINE } from "@/lib/headline-stats";
import { GITHUB_REPO_URL, GITHUB_PROFILE_URL, AUTHOR_NAME } from "@/lib/site";

const prAucChartData = [...comparisonData.results]
  .sort((a, b) => b.pr_auc_full_test - a.pr_auc_full_test)
  .map((r, i) => ({
    label: r.method
      .replace("isolation_forest (population-only)", "IsolationForest, population-only")
      .replace("isolation_forest (population + entity-deviation)", "IsolationForest, +entity-deviation")
      .replace(/\s*\(.*\)/, ""),
    value: r.pr_auc_full_test,
    emphasis: i === 0,
  }));

const findings = [
  {
    title: "A pandas version bug, caught three times, fixed properly each time",
    body:
      "pandas 3.0's string dtype silently changed how missing values behave under astype(str), the same root cause surfaced through three unrelated operations (entity fingerprinting, a ring-membership check, and a column passed to a web template). Traced each one to source instead of patching around the symptom.",
  },
  {
    title: "A live-safe ring rule that excluded the exact ring it was built to catch",
    body:
      "Designed a ground-truth-free credibility check for live data, reasonable on paper. Ran it against a deliberately-planted test ring and watched it get filtered out: the rule required individually-anomalous amounts, but a real evasive ring uses normal-looking amounts on purpose. Fixed the actual reasoning, not just the number.",
  },
  {
    title: "Rebuilt the entity fingerprint after the original deadline passed",
    body:
      "The original submission deadline came and went. Instead of shipping what existed, went back and fixed two things deliberately deferred under time pressure: a sharper entity fingerprint and a time-based (not random) evaluation split. The second fix alone surfaced a real finding, fraud rate drifts upward over time in this dataset.",
  },
];

export default function LandingPage() {
  return (
    <>
      <header className="border-b border-border">
        <div className="mx-auto max-w-5xl px-6 h-16 flex items-center justify-between">
          <span className="font-semibold tracking-tight">Sentinel</span>
          <div className="flex items-center gap-5 text-sm">
            <Link href="/demo" className="text-text-muted hover:text-text transition-colors">
              Live demo
            </Link>
            <a href={GITHUB_REPO_URL} target="_blank" rel="noreferrer" className="text-text-muted hover:text-text transition-colors">
              Source ↗
            </a>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="mx-auto max-w-5xl px-6 pt-20 pb-16">
          <p className="text-accent text-sm font-medium mb-4 font-mono">BEHAVIORAL FRAUD DETECTION</p>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight leading-[1.1] max-w-3xl">
            Learn what&apos;s normal for this account. Flag what isn&apos;t. Explain every flag.
          </h1>
          <p className="text-text-muted text-lg mt-6 max-w-2xl leading-relaxed">
            A UEBA-style fraud engine built on IEEE-CIS&apos;s 590K real transactions: per-entity behavioral
            baselines, abuse-ring detection, and a gated auto-responder, every result honestly measured against
            four required baselines, including the result that turned out negative.
          </p>
          <div className="flex gap-4 mt-8">
            <Link
              href="/demo"
              className="rounded-md bg-accent text-bg font-medium px-5 py-2.5 text-sm hover:opacity-90 transition-opacity"
            >
              Explore the live demo →
            </Link>
            <a
              href={GITHUB_REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="rounded-md border border-border px-5 py-2.5 text-sm hover:border-border-strong transition-colors"
            >
              View source
            </a>
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-10 text-xs font-mono text-text-faint">
            <span className="mr-1 text-text-muted">Built with</span>
            {["Python", "pandas", "scikit-learn", "FastAPI", "Jinja2", "HTMX", "Next.js", "TypeScript", "Tailwind"].map(
              (t) => (
                <span key={t} className="rounded-full border border-border px-2.5 py-1">
                  {t}
                </span>
              )
            )}
          </div>
        </section>

        {/* Why */}
        <section className="mx-auto max-w-5xl px-6 py-14 border-t border-border">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted mb-4">Why this exists</h2>
          <p className="text-text leading-relaxed max-w-3xl">
            A flat &ldquo;is this transaction fraud&rdquo; classifier misses the cases that matter most: a stolen
            card used for an ordinary-looking amount, or a new account behaving identically to nine other
            &ldquo;new&rdquo; accounts sharing one device. Both look fine at the population level. Neither looks
            fine once you ask &ldquo;is this normal for this entity specifically.&rdquo; This is a security
            technique, UEBA (User and Entity Behavior Analytics), applied to payments, built to answer, at a glance,
            why any given transaction was flagged.
          </p>
        </section>

        {/* Pipeline */}
        <section id="how-it-works" className="mx-auto max-w-5xl px-6 py-14 border-t border-border scroll-mt-16">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted mb-5">How it works</h2>
          <PipelineDiagram />
        </section>

        {/* Results */}
        <section className="mx-auto max-w-5xl px-6 py-14 border-t border-border">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted mb-5">Results</h2>
          <p className="text-text-muted text-sm mb-6 max-w-2xl">
            Everything below is from the real, held-out IEEE-CIS test split ({HEADLINE.testRows.toLocaleString()}{" "}
            transactions), never the synthetic demo stream. Full methodology in the{" "}
            <a
              href={`${GITHUB_REPO_URL}/blob/main/docs/LEARNING_LOG.md`}
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              Learning Log
            </a>
            , and the exact same table live on the{" "}
            <Link href="/demo/metrics" className="text-accent hover:underline">
              metrics page
            </Link>
            .
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            <StatTile value={`${HEADLINE.liftMultiple}x`} accent label="PR-AUC vs. the best of four required baselines" />
            <Link href="/demo/ring">
              <StatTile value={`${HEADLINE.ringCount}`} label="credible abuse-ring clusters found →" accent clickable />
            </Link>
            <StatTile
              value={`${(HEADLINE.bestRing.fraudRate * 100).toFixed(0)}%`}
              label={`proxy fraud rate in the strongest ring (${HEADLINE.bestRing.entities} accounts, baseline ≈ ${(HEADLINE.baselineFraudRate * 100).toFixed(0)}%)`}
            />
            <Link href="/demo/audit">
              <StatTile value={HEADLINE.autoResponder.decline.toLocaleString()} label="transactions auto-declined, every one audited →" clickable />
            </Link>
          </div>

          <h3 className="font-medium mb-4">The detector vs. all four required baselines (PR-AUC)</h3>
          <div className="rounded-lg border border-border bg-surface p-6 mb-10">
            <BarChart data={prAucChartData} />
          </div>

          <h3 className="font-medium mb-1">The honest negative result</h3>
          <p className="text-sm text-text-muted leading-relaxed max-w-3xl mb-4">
            The central hypothesis, that knowing an account&apos;s own history improves detection, did{" "}
            <strong className="text-text">not</strong> hold up: population-only beat population+entity-deviation on
            PR-AUC, even restricted to accounts with real history. Root-caused, not hand-waved: most fraud in this
            dataset happens on an account&apos;s very first transaction, where there&apos;s no history to deviate
            from by construction, see{" "}
            <a
              href={`${GITHUB_REPO_URL}/blob/main/docs/ADR_LOG.md`}
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              ADR-0007
            </a>{" "}
            for what this changed about the design.
          </p>
          <div className="rounded-lg border border-border bg-surface p-6 max-w-2xl">
            <SplitBar
              segments={[
                { label: "Fraud on an account's first-ever transaction", value: HEADLINE.coldStartFraudShare, emphasis: true },
                { label: "Fraud on an account with prior history", value: 1 - HEADLINE.coldStartFraudShare },
              ]}
            />
          </div>
        </section>

        {/* Engineering judgment */}
        <section className="mx-auto max-w-5xl px-6 py-14 border-t border-border">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted mb-2">Engineering judgment, not just a working model</h2>
          <p className="text-text-muted text-sm mb-6 max-w-2xl">
            A sample of real bugs caught and fixed along the way, not sanded down after the fact. The full, raw,
            dated log (30+ entries) lives in{" "}
            <a
              href={`${GITHUB_REPO_URL}/blob/main/docs/LEARNING_LOG.md`}
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              docs/LEARNING_LOG.md
            </a>
            .
          </p>
          <div className="grid gap-4">
            {findings.map((f) => (
              <div key={f.title} className="rounded-lg border border-border bg-surface p-5">
                <h3 className="font-medium mb-1.5">{f.title}</h3>
                <p className="text-sm text-text-muted leading-relaxed">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-5xl px-6 py-16 border-t border-border text-center">
          <h2 className="text-2xl font-semibold mb-3">See it running</h2>
          <p className="text-text-muted mb-6 max-w-xl mx-auto">
            The live demo below is the real Risk Console&apos;s interface, backed by the actual result data from
            this project, not a mockup.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/demo"
              className="rounded-md bg-accent text-bg font-medium px-5 py-2.5 text-sm hover:opacity-90 transition-opacity"
            >
              Open the live demo →
            </Link>
            <a
              href={GITHUB_REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="rounded-md border border-border px-5 py-2.5 text-sm hover:border-border-strong transition-colors"
            >
              Read the code
            </a>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-5xl px-6 flex items-center justify-between text-sm text-text-muted">
          <a href={GITHUB_PROFILE_URL} target="_blank" rel="noreferrer" className="hover:text-text transition-colors">
            {AUTHOR_NAME}
          </a>
          <a href={GITHUB_REPO_URL} target="_blank" rel="noreferrer" className="hover:text-text transition-colors">
            View code ↗
          </a>
        </div>
      </footer>
    </>
  );
}
