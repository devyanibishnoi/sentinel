# Sentinel — Portfolio Frontend

A static, Vercel-deployable showcase of the Sentinel fraud detection engine (see the [root README](../README.md) for the actual project). This is **not** the real Risk Console, that's a live FastAPI app in `../console/`, not deployable to Vercel as-is. This is a separate, static site: a case-study landing page plus an interactive mini-console, backed by real (curated, not live) result data baked in at build time.

## Data

The JSON files in `data/` are generated from the real pipeline's `results/` files, they aren't checked in by hand and shouldn't be edited directly. To regenerate them after a new pipeline run:

```bash
# from the repo root, with the venv active
python scripts/export_web_data.py
```

## Running locally

```bash
npm install
npm run dev
```

## Building the static export

```bash
npm run build
```

Output goes to `out/`, pure static files, no server required. To preview the actual exported build (not the dev server):

```bash
npx serve out
```

## Deploying to Vercel

Point a new Vercel project at this repo with **`web`** as the root directory. Vercel auto-detects Next.js and the `output: "export"` config, no extra settings needed.

Before deploying, update `lib/site.ts` with the real GitHub repo URL.
