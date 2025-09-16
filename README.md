# DialogueDNA Backend (FastAPI)

AI-powered conversation analysis backend for **DialogueDNA** — handles audio upload, secure storage, transcription with speaker diarization, dual‑channel emotion analysis (text + tone), multi‑style summarization with Azure OpenAI, and PDF export. Built with **FastAPI**, **Azure** (Speech, OpenAI, Blob), **Supabase**, and **Transformers**.

> This README explains the architecture, required environment variables, how to run locally, and the REST API (with examples).

---

## ✨ Key Features

- **Audio intake**: Upload raw audio; automatically normalized to 16 kHz, mono, PCM s16le WAV.
- **Secure storage**: Azure Blob Storage per‑session folder layout with short‑lived SAS URLs.
- **Transcription (Azure Speech v3.1)**: Async job with **speaker diarization**, duration extraction and basic metadata.
- **Emotion analysis (hybrid)**:
  - **Text‑based (7 classes)** via Transformers (default: `j-hartmann/emotion-english-distilroberta-base`).
  - **Tone‑based (4 classes)** on audio segments (default: `superb/hubert-large-superb-er`) + **backchannel** detection.
  - **Mixer strategy** fuses text+tone into unified 7‑class scores per utterance.
- **Summarization (Azure OpenAI)**: Robust Chat Completions with **prompt presets** (business, clinical, per‑speaker, customer service, educational coaching, etc.). Includes retry handling and token/temperature controls.
- **PDF export**: Unicode‑safe (Hebrew/Arabic/Emoji) summary PDF using embedded TTF.
- **Auth**: Supabase JWT (HTTP Bearer). Backend validates tokens using `SUPABASE_JWT_SECRET`.
- **DB**: Session lifecycle/status persisted in Supabase (insert/update/select), including blob URLs & status flags.
- **Background processing**: Upload triggers an end‑to‑end pipeline via FastAPI `BackgroundTasks`; auto‑summary runs when transcript & emotions are ready.
- **Clean modular design**: `app/services/*` for pipeline logic, `app/storage/*` for blob I/O, `app/db/*` for Supabase DAL, `app/api/*` for HTTP layer.

---

## 🧭 Repository Layout

```
app/
  api/
    dependencies/auth.py      # Supabase JWT bearer parsing
    endpoints/sessions/       # All session routes (upload, transcript, emotions, summary, audio, speakers, delete, metadata)
  core/
    config.py                 # Env + global knobs (models, Azure/Supabase clients, paths)
    security.py               # Hashing, JWT helpers (internal)
  db/
    session_db.py             # Sessions table DAL (create/update/get/delete/bulk)
    superbase/supabase_db.py  # Thin wrapper over supabase-py
  services/
    transcript/transcriber.py             # Azure Speech v3.1 polling + diarization
    emotions/...                          # text_base, tone_base, mixer
    summary/{prompts.py, summarizer.py, runner.py}  # prompt presets + Azure OpenAI client + auto-run
    facade.py                              # DialogueProcessor orchestrating the whole pipeline
  storage/
    azure/blob/{service,fetcher,uploader,deleter}.py # Blob ops + SAS URLs + WAV normalization
    session_storage.py                     # High-level per-session storage API
  utils/pdf.py                             # Summary → PDF (Unicode-safe)
main.py                                    # FastAPI app + CORS + router registration
run.py                                     # Convenience launcher (uvicorn)
```

---

## 🧩 Architecture

```mermaid
flowchart LR
  FE[React/Vite Frontend] -- Bearer JWT --> API{{FastAPI}}
  
  subgraph API Layer
    UP[/POST upload/] --> BG[BackgroundTasks]
    MET[/GET metadata/] --> DB[(Supabase)]
    SUM[/summary/] --> STOR[(Azure Blob)]
    EMO[/emotions/] --> STOR
    TRN[/transcript/] --> STOR
    AUD[/audio/] --> STOR
    SPK[/speakers/] --> DB
    DEL[/delete/] --> DB & STOR
  end

  BG --> TRZ[Azure Speech v3.1]
  BG --> TXT[Text Emotion (Transformers)]
  BG --> TONE[Tone Emotion (HF)]
  TXT & TONE --> MIX[MixerStrategy]
  MIX --> STOR
  TRZ --> STOR
  STOR --> RUN[Summary Runner]
  RUN --> OAI[Azure OpenAI]
  OAI --> STOR
  STOR --> PDF[PDF Generator]
  DB <--> API


### Storage Layout (Azure Blob)

```
{session_id}/
  audio          # normalized WAV
  transcript     # transcript.json (SAS-fetched by client)
  emotions       # emotions.json (per-utterance 7-class)
  summary        # summary.txt (final), used by /summary and PDF
```

---

## 🔒 Authentication

All routes (except health) expect **Authorization: Bearer <JWT>**. The backend decodes Supabase JWTs with `SUPABASE_JWT_SECRET` and expects `aud="authenticated"` and `sub=<user_id>`. Session access is enforced: users can only fetch their own sessions/blobs.

---

## ⚙️ Environment Variables

Create a `.env` at repo root:

```bash
# --- Azure Blob Storage ---
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=...;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_CONTAINER_NAME=audiorecordstorage

# (Optional, for absolute links shown in UI)
AZURE_CONTAINER_URL=https://<account>.blob.core.windows.net/${AZURE_CONTAINER_NAME}

# --- Azure Speech (Transcription) ---
SPEECH_KEY=xxxxx
REGION=westeurope

# --- Azure OpenAI ---
AZURE_OPENAI_API_KEY=xxxxx
AZURE_OPENAI_ENDPOINT=https://<your-aoai>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini  # or your deployed model
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# --- Supabase ---
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxxxx
SUPABASE_JWT_SECRET=xxxxx

# --- Emotion Models (optional overrides) ---
TEXT_EMOTION_MODEL=j-hartmann/emotion-english-distilroberta-base
AUDIO_EMOTION_MODEL=superb/hubert-large-superb-er
TOP_K_EMOTIONS=6  # integers accepted

# --- Audio normalization ---
# 16 kHz, mono, 16-bit PCM WAV is enforced by the uploader
```

> The backend constructs a Supabase client via `create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)` and also uses `SUPABASE_JWT_SECRET` to verify incoming Bearer JWTs.

---

## 🧪 Local Development

### 1) Python & deps

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> On first run, HuggingFace models will be downloaded to your cache.

### 2) Environment

Create `.env` as above and ensure your Azure resources + Supabase project are reachable.

### 3) Run

```bash
uvicorn app.main:app --reload --port 8000
# or: python -m app.run
```

CORS is permissive in dev (`allow_origins=["*"]`). For production, restrict it to your frontend domain.

---

## 🧠 Processing Pipeline (End-to-End)

1. **Upload** (`POST /api/sessions/upload`)
   - Saves session row in Supabase.
   - Uploads audio → Azure Blob (`{session}/audio`) with forced WAV normalization.
   - Starts background processing: transcription → emotions → auto‑summary.

2. **Transcription**
   - Azure Speech v3.1 job created with SAS URL to `{session}/audio`.
   - Polls until completion; extracts diarized utterances, duration, participants.
   - Stores transcript JSON → Blob `{session}/transcript`. Updates statuses in DB.

3. **Emotion Analysis**
   - **Text**: 7‑class scores per utterance from transcript lines.
   - **Tone**: 4‑class scores on aligned audio spans (+ backchannel QC, duration).
   - **Mixer**: smart weighting (confidence/duration‑aware) + 4→7 soft mapping producing final 7‑class distribution; stored to `{session}/emotions`.

4. **Summarization**
   - Auto‑triggered only when transcript & emotions are **completed** and a `summary_preset` is set.
   - Calls Azure OpenAI with robust retry and preset‑specific prompt scaffolding.
   - Stores summary text → `{session}/summary` + updates DB status/URL.

5. **PDF Export**
   - `GET /api/sessions/summary/{id}/download` renders a Unicode‑safe PDF using `utils/pdf.py`.

---

## 🧾 REST API

> Base path in code: routes are registered under `/api/sessions/*` via `app/api/endpoints/sessions/__init__.py`.

### Upload

```
POST /api/sessions/upload
Content-Type: multipart/form-data
Authorization: Bearer <JWT>

Fields:
  - file: <audio>
  - title: string
  - summary_preset: string (optional; one of presets below)
  - local_src: bool (optional, for dev local audio read)
```

**Response**: `{ "session_id": "uuid" }`

### Metadata

```
GET /api/sessions/metadata
Authorization: Bearer <JWT>
```
Return a list of sessions (id, title, duration, participants, created/updated, per‑stage statuses).

```
GET /api/sessions/metadata/{id}
Authorization: Bearer <JWT>
```

### Transcript

```
GET /api/sessions/transcript/{id}
Authorization: Bearer <JWT>
```
Returns `{ "status": "<pending|completed|failed>", "data": <sas_url_or_null> }`.

### Emotions

```
GET /api/sessions/emotions/{id}
Authorization: Bearer <JWT>
```
Returns `{ "status": "<pending|completed|failed>", "data": <sas_url_or_null> }`.

### Summary

```
GET /api/sessions/summary/presets
Authorization: Bearer <JWT>
```
Returns label map for UI (see **Presets** below).

```
POST /api/sessions/summary/{id}/run
Authorization: Bearer <JWT>
Query: ?preset=<preset_key>
```
Idempotent trigger; will only run when eligible.

```
GET /api/sessions/summary/{id}
Authorization: Bearer <JWT>
```
Returns `{ "status": "<pending|completed|failed>", "data": <sas_url_or_null> }`.

```
GET /api/sessions/summary/{id}/download
Authorization: Bearer <JWT>
```
Returns a generated **PDF** (attachment).

### Audio (normalized WAV)

```
GET /api/sessions/audio/{id}
Authorization: Bearer <JWT>
```
Returns `{ "status": "<pending|completed|failed>", "data": <sas_url_or_null> }`.

### Speakers mapping

```
GET /api/sessions/speakers/{id}
PUT /api/sessions/speakers/{id}
Authorization: Bearer <JWT>
Body (PUT):
  { "map": { "1":"Amal", "2":"Yarden" } }
```
Updates `speaker_map` and also recalculates `participants` for display order.

### Delete

```
DELETE /api/sessions/delete/{id}
POST   /api/sessions/delete/bulk
Authorization: Bearer <JWT>

Body (bulk):
  { "session_ids": ["...", "..."] }
```

### Sample JSON Shapes

**Transcript line**
```json
{
  "speaker": 1,
  "text": "I apologize for the inconvenience.",
  "start_time": 13.0,
  "end_time": 16.2
}
```

**Emotions (per utterance, final 7-class sorted)**
```json
{
  "speaker": 2,
  "text": "I'm really upset about the wait.",
  "start_time": 4.0,
  "end_time": 9.1,
  "emotions": [
    { "label": "anger", "score": 0.78 },
    { "label": "sadness", "score": 0.11 }
  ]
}
```

---

## 🧱 Prompt Presets (keys → UI labels)

- `business_meeting_summary` → **Business Meeting Summary**
- `customer_service_summary` → **Customer Service Summary**
- `emotional_story` → **Emotional Story**
- `clinical_summary` → **Clinical Summary**
- `analytical_report` → **Analytical Report**
- `per_speaker_summary` → **Per Speaker Reflections**
- `all_in_one` → **All‑in‑One Narrative**
- `educational_coaching` → **Educational Coaching**
- `instructional_explainer` → **Instructional Explainer (Grounded)**
- `personal_interests_summary` → **Personal Interests Chat**
- `coaching_grow` → **GROW Coaching**

> See `app/services/summary/prompts.py` for full, structured prompt text and formatting rules for each style.

---

## 🛡️ Reliability & Quality Notes

- **Idempotency**: Summary runner checks transcript/emotions status to avoid duplicate summaries.
- **Rate limiting**: Summarizer retries Azure OpenAI on 429 with delays; aborts on API errors cleanly.
- **QC (tone)**: Backchannel detector flags super‑short utterances and prevents over‑confident tone signals.
- **WAV normalization**: Any incoming audio is re‑encoded to 16 kHz / mono / 16‑bit before model use.
- **SAS URLs**: All client fetches use short‑lived links (never expose account keys).

---

## 🧰 Troubleshooting

- **Summary never runs**: Ensure `summary_preset` is set **and** `transcript_status == "completed"` **and** `emotion_breakdown_status == "completed"`.
- **403/401**: Check `Authorization: Bearer <JWT>` and `SUPABASE_JWT_SECRET` (audience must be `"authenticated"`).
- **Azure Speech polling fails**: Verify `SPEECH_KEY`, `REGION`, and that the SAS URL generated for `{session}/audio` is valid.
- **Model downloads**: First run may take time to pull HF models; ensure network access.
- **CORS**: Set `allow_origins` appropriately in `main.py` for your frontend domain in production.

---

## 📄 License & Credits

Internal academic project backend for the DialogueDNA system. Built with ♥ by the DialogueDNA team (MTA). Uses Azure Speech & OpenAI, HuggingFace Transformers, FastAPI, and Supabase.
