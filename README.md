# LeadPilot AI

LeadPilot AI is a Streamlit workspace for organizing real estate enquiries, understanding buyer intent, and planning timely follow-ups. It combines Gemini-powered analysis with deterministic lead scoring and property recommendations grounded in a sample catalogue.

## Features

- Capture enquiries with buyer requirements, budget, location, timeline, and message.
- Generate a summary, buyer intent, requirements, concerns, missing information, next action, and suggested response.
- Score and prioritize leads using transparent Python rules.
- Chat with context from a selected lead.
- Find sample properties matching budget, location, and bedroom requirements.
- Schedule and track follow-up actions.
- Store records locally with SQLite or use Supabase for hosted persistence.

## Architecture

    Lead intake -> Pydantic validation -> LangGraph analysis workflow -> Gemini API
                                                   |                          |
                                                   +-> validate output/evidence
                                                             |
                                                             v
                                                 deterministic Python score
                                                             |
                                                             v
                                                   SQLite or Supabase

    Selected lead -> contextual chat -> Gemini API
                   -> optional property retrieval
                        -> hard filters -> semantic ranking

The analysis workflow validates Gemini output and supporting evidence before scoring and saving. Invalid model output can be retried once. Lead priority is calculated in Python, making the score repeatable and explainable. Property retrieval applies eligibility filters first; semantic ranking only orders eligible catalogue entries. If embeddings or FAISS are unavailable, the app falls back to filtered results.

## Technology

- Application: Python and Streamlit
- Analysis and chat: Google Gemini API
- Workflow and validation: LangGraph and Pydantic
- Lead scoring: deterministic Python rules
- Persistence: SQLite by default; optional Supabase REST API
- Property retrieval: Sentence Transformers, NumPy, and FAISS

## Run locally

Use Python 3.13 or another version supported by the pinned dependencies.

    python -m venv .venv

Activate the environment, install dependencies, and create a local environment file:

    # Windows PowerShell
    .venv\\Scripts\\Activate.ps1

    # macOS / Linux
    source .venv/bin/activate

    pip install -r requirements.txt
    cp .env.example .env

On Windows, use Copy-Item .env.example .env instead of cp if needed. Add your Gemini key to .env:

    GEMINI_API_KEY=your_key_here
    GEMINI_MODEL=gemini-3.5-flash-lite

Start the app:

    streamlit run app.py

Open http://localhost:8501. The first semantic property search may download the all-MiniLM-L6-v2 embedding model. Local credentials, databases, model files, and generated files are excluded from Git.

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| GEMINI_API_KEY | For AI analysis and chat | Gemini API credential |
| GEMINI_MODEL | No | Gemini model name |
| SUPABASE_URL | Optional | Supabase project URL for hosted persistence |
| SUPABASE_SERVICE_ROLE_KEY | Optional | Server-side Supabase credential |
| DATABASE_PATH | No | SQLite file path; defaults to data/leads.db |

Set both Supabase variables together or leave both unset to use SQLite. For hosted use, configure secrets in the hosting provider. Never commit credentials.

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create an app from udaykumar-3005/LeadPilotAI.
3. Select the main branch and app.py as the entry point.
4. Add GEMINI_API_KEY and optionally GEMINI_MODEL in the app's Secrets settings.
5. Add both Supabase settings if lead records must persist across cloud restarts. SQLite on hosted instances may not provide durable storage.

## Project layout

    LeadPilotAI/
    ├── app.py                       Streamlit interface and interaction flow
    ├── assets/style.css             Application styling
    ├── data/
    │   ├── sample_properties.csv    Fictional property catalogue
    │   └── hybrid_leads.json        Fictional sample enquiries
    ├── src/
    │   ├── ai.py                    Gemini client calls
    │   ├── chatbot.py               Lead-specific conversation context
    │   ├── database.py              SQLite and Supabase persistence
    │   ├── models.py                Input/output models and validation
    │   ├── prompts.py               Model prompts
    │   ├── rag.py                   Property filtering and ranking
    │   ├── scoring.py               Deterministic priority score
    │   └── workflow.py              LangGraph analysis flow
    ├── tests/                       Automated tests
    ├── requirements.txt
    └── schema.sql                   Supabase schema and access policy

## Tests

    python -m pytest -q

The included sample enquiries and property catalogue are fictional. The app currently has no user authentication; use test data and configure access appropriately before exposing it to real customer information.
