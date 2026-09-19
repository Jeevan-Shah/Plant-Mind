# PlantMind 🌿

**An Explainable AI Plant-Care System Using Knowledge Graphs, Computer Vision and GraphRAG**

PlantMind is not just a plant-disease classifier. It is a decision-support system for the state
of an **individual plant**:

```
Image + Plant Profile + Care History + Symptoms
        ↓
    Plant State
        ↓
Plant Care Knowledge Graph
        ↓
     GraphRAG
        ↓
       LLM
        ↓
Explainable + Personalized Plant-Care Recommendation
```

> ⚠️ **Disclaimer** — PlantMind provides AI-assisted plant-care guidance for educational and
> decision-support purposes. Predictions are not guaranteed diagnoses. Verify recommendations
> with reliable agricultural sources or experts when necessary.

---

## 1. What V1 does

| Capability | Status in V1 |
|---|---|
| Plant CRUD (name, species, growth stage, age, watering, light, notes) | ✅ Real (SQLite + FastAPI) |
| Image upload / drag-drop / preview | ✅ Real |
| Computer-vision symptom detection | ⚠️ **Demo Vision Model** (heuristic colour analysis — clearly labelled) |
| Plant State engine (profile + history + image + symptoms fusion) | ✅ Real (deterministic rules) |
| Knowledge Graph (plants, diseases, symptoms, conditions, treatments) | ✅ Real (SQLite-backed graph, seeded from JSON) |
| GraphRAG-style retrieval (entity identification → graph expansion → documents → evidence) | ✅ Real pipeline, lightweight retrieval |
| LLM reasoning | ⚠️ Optional (OpenAI-compatible API if `LLM_API_KEY` is set) |
| Fallback reasoning (no API key) | ✅ Real deterministic KG-based engine |
| Explainability (why this result? evidence? limitations?) | ✅ Real |
| Personalization (per-plant recommendations from profile/history) | ✅ Real |
| Analysis history & timeline | ✅ Real |
| Knowledge Explorer UI | ✅ Real |

**No fake research numbers.** Confidence values shown by the Demo Vision Model and the fallback
reasoner are *demo values derived from evidence strength*, not measured accuracy. Nothing in the
app claims accuracy/precision/recall that was never measured.

---

## 2. Architecture

```
plantmind/
├── frontend/                  React 19 + Vite 7 + TypeScript + Tailwind 4 + Lucide
│   └── src/
│       ├── components/        Layout, UI kit, AnalysisReport, PlantModal
│       ├── pages/             Dashboard, Plants, PlantDetails, AnalyzePage,
│       │                      AnalysisReportPage, HistoryPage, KnowledgeExplorer
│       ├── hooks/             hash-based router (useRoute / navigate)
│       ├── lib/api.ts         typed API client (uses Vite proxy)
│       └── types.ts
├── backend/
│   ├── app/
│   │   ├── api/               REST routes (plants, analyses, knowledge, meta)
│   │   ├── models.py          SQLAlchemy models (PostgreSQL-ready)
│   │   ├── schemas.py         Pydantic v2 schemas
│   │   ├── services/
│   │   │   ├── analysis_service.py    orchestration of the full pipeline
│   │   │   ├── vision_service.py      ⚠️ DEMO vision model (plug real model here)
│   │   │   ├── plant_state_service.py Plant State engine
│   │   │   ├── graphrag_service.py    GraphRAG retrieval + grounded generation
│   │   │   ├── knowledge_service.py   graph abstraction layer (SQLite ↔ future Neo4j)
│   │   │   ├── llm_service.py         modular LLM provider (OpenAI-compatible)
│   │   │   ├── reasoning_engine.py    deterministic KG fallback reasoning
│   │   │   └── plant_service.py       serialization + health status
│   │   ├── config.py          env-driven configuration
│   │   ├── database.py        SQLAlchemy engine/session
│   │   └── main.py            FastAPI app

### Pipeline (one analysis)

1. **Vision** (`vision_service.analyze_image`) — DEMO model inspects colour statistics and maps
   them to KG symptom names (`model_status = 'demo'`).
2. **Plant State** (`plant_state_service.build_plant_state`) — fuses plant profile, care
   history, image symptoms, user-reported symptom text and profile-derived environmental flags
   into one structured state + risk level.
3. **GraphRAG** (`graphrag_service`):
   - *Entity identification* — matches the plant state onto KG entities (species, symptoms from
     the image AND from free text, environmental flags).
   - *Graph retrieval* — one-hop neighbourhood expansion around identified entities
     (Plant → Disease → Symptom / Treatment / Condition).
   - *Document retrieval* — keyword-scored markdown knowledge documents.
4. **Reasoning**:
   - No `LLM_API_KEY` → `reasoning_engine` (deterministic, KG-grounded, labelled
     *"Knowledge-based demo reasoning"*).
   - Key present → `llm_service` sends the **evidence context only** (never the raw question)
     with a strict grounded prompt, then merges extra suggestions.
5. **Persistence** — the full analysis (state, evidence triples, explanation, recommendations,
   preventive care, limitations) is stored and linked to the plant.

---

## 3. Knowledge Graph

Seeded on first startup from `knowledge/entities.json` + `knowledge/relationships.json` into
`KnowledgeEntity` / `KnowledgeRelationship` tables (SQLite). Relationship types include:
`susceptibleTo`, `hasSymptom`, `associatedWith`, `favors`, `managedBy`, `preventedBy`,
`requires`, `sensitiveTo`, `causes`.

Example:

```
Tomato → susceptibleTo → Early Blight
Early Blight → hasSymptom → Brown Spots
Early Blight → hasSymptom → Yellow Leaves
Early Blight → associatedWith → High Humidity
Early Blight → managedBy → Remove Affected Leaves
```

The service layer (`knowledge_service`) is backend-agnostic: setting `GRAPH_BACKEND` and adding
a Neo4j implementation is a drop-in extension (the GraphRAG service, reasoning engine and API
never touch SQL directly).

## 4. How the Demo Vision Model works (and how to replace it)

`vision_service.analyze_image` computes colour fractions (yellow/brown/white/dark/green) with
Pillow and maps strong signals to KG symptom names. It is deterministic and clearly labelled —
confidence is a **demo value**, not a trained-model metric.

To plug in a real model (YOLO / EfficientNet / PlantVillage CNN):

1. Add your weights + inference code (e.g. `backend/app/vision/model.py`).
2. Implement the same `analyze_image(image_bytes) -> {predicted_condition, symptoms, confidence, model_status}` contract.
3. Set `model_status` to something like `'efficientnet-v1'` and load the model in `main.py` startup.
4. Everything downstream (plant state, GraphRAG, reasoning) keeps working unchanged.

│   ├── seed.py                demo KG + demo plants seeding
│   └── requirements.txt
├── knowledge/
│   ├── entities.json          seed entities (4 plants, 6 diseases, 6 symptoms,
│   │                          6 environmental conditions, 6 treatments)
│   ├── relationships.json     seed triples (susceptibleTo, hasSymptom, managedBy, …)
│   └── documents/*.md         supporting knowledge documents (retrieved by GraphRAG)
├── uploads/                   uploaded leaf/plant images (served statically)
├── .env.example

## 5. Environment variables

Copy `.env.example` → `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///backend/data/plantmind.db` | PostgreSQL-ready SQLAlchemy URL |
| `SEED_DEMO` | `true` | create demo plants on first run |
| `CORS_ORIGINS` | `http://localhost:5173,…` | allowed browser origins |
| `GRAPH_BACKEND` | `sqlite` | `neo4j` reserved for the future driver |
| `LLM_API_KEY` | *(empty)* | if set, enables grounded LLM reasoning |
| `LLM_MODEL` | `gpt-4o-mini` | model name sent to the provider |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | any OpenAI-compatible endpoint |
| `LLM_TIMEOUT_SECONDS` | `20` | request timeout |

No secrets are hardcoded; the LLM call fails safe (falls back to the deterministic reasoner).

## 6. Running locally (Windows / macOS / Linux)

```bash
# 1. Backend (Python 3.11+)
python -m venv .venv
# Windows:
.venv\Scripts\pip install -r backend\requirements.txt
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
# macOS/Linux:
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 2. Frontend (Node 18+) — second terminal
npm --prefix frontend install
npm --prefix frontend run dev
```

Or the root npm scripts: `npm run setup`, `npm run dev:backend`, `npm run dev`.

> Windows note: if `python` is not on PATH, run the backend through the venv directly:
> `.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000`

### URLs

- Frontend (development): **http://localhost:5173**
- Backend API: **http://127.0.0.1:8000**
- Interactive API docs: **http://127.0.0.1:8000/docs**
- Health: **http://127.0.0.1:8000/api/health**

No authentication is required in V1 (local demo app — there are no login credentials).

├── docker-compose.yml
└── package.json               convenience scripts
```

## 7. API summary

```
POST   /api/plants                    create plant
GET    /api/plants                    list plants (+health status, latest condition)
GET    /api/plants/{id}               plant details
PUT    /api/plants/{id}               update plant
DELETE /api/plants/{id}               delete plant (cascades analyses + care events)

POST   /api/plants/{id}/analyze       full pipeline (multipart: image + symptoms)
GET    /api/plants/{id}/analyses      per-plant analysis timeline
GET    /api/plants/{id}/care          care history (GET/POST for events)
GET    /api/analyses                  all analyses (history page)
GET    /api/analyses/{id}             single analysis (full report)

GET    /api/knowledge/search          search entities (?q=&entity_type=)
GET    /api/knowledge/types           entity types + counts
GET    /api/knowledge/entity/{id}     one entity
GET    /api/knowledge/relationships/{id}  incoming + outgoing triples

GET    /api/dashboard/stats           counts + status breakdown + recent analyses
GET    /api/health                    system status (db, graph, vision, llm)
POST   /api/demo/reset                wipe plants/analyses and reseed demo data
```

## 8. Docker

```bash
docker compose up --build
# Frontend: http://localhost:5173 · API: http://localhost:8000
```

## 9. Demo scenario (30-second tour)

1. Open http://localhost:5173 — the dashboard shows 4 pre-seeded demo plants.
2. Plants → **Tomato #17** (Flowering, 42 days) → *Analyze Plant*.
3. Upload any leaf photo (a yellow/brown one works best with the demo detector), type
   `Yellow leaves and brown spots`, click **Analyze Plant**.
4. The report shows: possible condition (**Early Blight**), demo confidence, observed
   symptoms, plant state (species/stage/age/risk), **Why this result?** reasoning steps,
   **Evidence** (KG triples + retrieved documents), recommended actions (KG `managedBy`
   actions + profile-personalized steps), preventive care, and limitations.
5. The analysis is stored — see *Analysis History* and the plant timeline.

## 10. Roadmap: V1 → research-grade

1. Real disease-detection model (YOLO/EfficientNet trained on PlantVillage) behind the vision service interface.
2. Real Neo4j graph behind `knowledge_service` (`GRAPH_BACKEND=neo4j`).
3. Vector retrieval upgrade: sentence-transformers + FAISS for the document store.
4. True GraphRAG with community summaries / multi-hop path ranking.
5. Real LLM provider keys for richer grounded summaries.
6. ESP32 / IoT environmental sensors feeding live conditions into the Plant State.
7. Weather + seasonal data integration.
8. Disease progression prediction using the stored analysis timeline.
9. Native Android release build (Play-Store signing, Play Store publishing).

---

## 11. Android app (APK)

PlantMind ships as an installable Android APK built with **Capacitor** (the React UI runs in a
native Android WebView with real native plugins for camera access).

### What the Android app adds over the web version

| Feature | How it works |
|---|---|
| **Real camera access** | "Take a photo with the camera" on the Analyze screen opens the device camera; Android asks for **Camera permission** on first use (`@capacitor/camera`). A Camera/Gallery chooser is shown. |
| **Installs like a normal app** | App name "PlantMind", launcher icon, splash, app drawer entry (`com.plantmind.app`). |
| **Connect to your PC backend** | On first launch the app shows a *Connect to server* screen. Run the backend on a PC on the same Wi-Fi (`uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`) and enter `http://<PC-IP>:8000`. The address is remembered. Changeable later under **Settings** (visible in the app's nav). |
| **Same UI, mobile-tuned** | The same dashboard, plants, analysis, history, knowledge explorer and analysis-report screens, responsive and touch-friendly. |

### Two ways to get the APK

**Option A — one command on Windows (auto-installs Java 17 + Android SDK into `.tools/`, ~1 GB on first run):**

```bat
build-apk.bat
```

The APK appears at `frontend\android\app\build\outputs\apk\debug\app-debug.apk`.
Copy it to your phone and install it (allow "Install unknown apps" when asked).

**Option B — build it in the cloud for free (no Android tooling on your PC):**

1. Push this repository to GitHub.
2. The included workflow `.github/workflows/build-apk.yml` builds the APK on every push
   (also runnable manually via *Actions → Build Android APK → Run workflow*).
3. Download `plantmind-apk` from the run's **Artifacts** section and install it on your phone.

**Option C — Android Studio:** open `frontend/android` in Android Studio and press Run ▶ (or
`Build > Build APK(s)`) — useful for emulator testing and signed release builds.

### Architecture notes

- The APK bundles only the frontend web assets; the Python backend (FastAPI, SQLite,
  knowledge graph, vision demo, GraphRAG) still runs on a PC/server and is reached over HTTP.
- `frontend/capacitor.config.ts` enables cleartext HTTP to LAN addresses (`192.168.x.x`);
  production deployments should use HTTPS.
- A real trained vision model, Neo4j, or a hosted LLM would all live **server-side** — the APK
  needs no changes when those upgrades happen.

> The KG content in V1 is a small demonstration set and is **not** scientifically exhaustive.

