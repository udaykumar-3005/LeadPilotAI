# LeadPilot AI

A real-estate sales assistant that turns inbound enquiries into prioritized leads, useful replies and dated follow-ups.

Built with Python, Streamlit, Gemini, LangGraph and SQLite. Optional Supabase storage keeps leads across cloud restarts. Sentence Transformers and FAISS match leads against a fictional property catalogue.

## Run locally

Python 3.13 is used in this workspace.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Skip the copy command if `.env` already exists. Add your key there:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. Activation is optional because these commands use the virtual environment directly. Restart Streamlit after changing `.env`. The first semantic property search downloads the free `all-MiniLM-L6-v2` embedding model. Without it, the app clearly labels its structured-filter fallback.

Gemini 3.5 Flash-Lite currently offers free-tier text input/output, subject to account quotas. Use a free-tier API project; this app does not enable billing. Model availability can vary by account, so `GEMINI_MODEL` is configurable. See [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing).

## Assignment coverage

| Requirement | Implementation |
| --- | --- |
| Six input fields | Name, Location, Property requirement, Budget, Buying timeline, Customer message |
| AI analysis | Summary, intent, requirements, objections, next action, customer reply |
| Contextual conversation | Selected lead, its analysis, follow-up and its own chat history |
| Multiple prioritized leads | Saved dashboard with search, sorting and Hot/Warm/Cold scores |
| Scannable output | Short sections, priority score, missing details and next action |
| Original feature | Smart Follow-up Planner with due dates, overdue tasks and completion status |
| Additional feature | Grounded property suggestions from 12 fictional listings |

Budget is entered in INR lakh. Property requirements and buying timelines accept free text. Names need 2 characters, requirements 3, and customer messages 10. A positive budget is required; unknown intent, financing and timeline remain unknown in the analysis.

## How it works

```text
Intake -> Pydantic validation -> LangGraph
                               -> Gemini analysis -> validate output and evidence
                                  -> invalid: retry once, then show an error
                                  -> valid: Python score -> save -> dashboard
Selected lead -> chat context -> optional property retrieval -> Gemini answer
Selected lead -> next action + date + status -> follow-up planner
```

One Gemini call produces all analysis fields. Scoring is deterministic Python. LangGraph controls validation retries without adding extra calls on the successful path. Quota and API failures stop with a readable error. Invalid analyses are never saved.

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit forms, dashboard, chat and planner |
| `src/models.py` | Input/output validation and evidence checks |
| `src/prompts.py` | Analysis and chat instructions |
| `src/ai.py` | Gemini request, timeout and safe errors |
| `src/workflow.py` | LangGraph nodes and conditional retry |
| `src/scoring.py` | Priority rules |
| `src/database.py` | SQLite CRUD and optional Supabase REST calls |
| `src/rag.py` | Structured filters and semantic ranking |
| `src/chatbot.py` | Build context for only the selected lead |

## Explain the score

| Signal | Points |
| --- | --- |
| Intent | Buy 35, explore 10, unknown 0 |
| Buying timeline | Up to 30 days 30, 90 days 20, 180 days 10, otherwise 0 |
| Financing | Explicit funds/loan approval 25, pending financing 10, unknown 0 |
| Stated requirements | At least one requirement 10 |

Hot is 70-100, Warm is 40-69, Cold is 0-39. A large budget alone does not imply readiness. Scored intent, financing and timeline require exact supporting quotes from the lead. Quote checks catch fabricated evidence, but cannot prove that the model interpreted a quote correctly. These are transparent demo rules, not a trained conversion model.

## Property retrieval and chat

`data/hybrid_leads.json` adds eight fictional test scenarios with English and Hinglish messages, different buying stages, possession and budget mismatches, and a corrected enquiry. In **New lead**, choose a **Hybrid lead scenario**, click **Fill hybrid enquiry**, then **Analyze and save lead**. Analysis and scores come from the normal Gemini and scoring workflow; the file contains only the six input fields. The dashboard uses these hybrid examples instead of the original sample leads. Use Kavya to test financing and total-cost questions, Meera to check the possession mismatch, Sana for no affordable catalogue match, and Aarav to check whether the latest correction overrides earlier statements.

Budget, location and explicitly stated bedroom count are hard filters. Locations match a city, locality, or `locality, city`; Bangalore also matches Bengaluru. Bedroom filtering recognizes formats such as `2 BHK` and `2 bedroom`. Other property types and availability are not hard filters.

Sentence Transformers embeds property descriptions. FAISS ranks only eligible properties by cosine similarity. A query never relaxes the saved constraints. The chat's property-search checkbox explicitly selects the retrieval route; ordinary lead questions use only lead context. Retrieved records include IDs for citations such as `[P001]`. Matches are candidates, not guarantees that every preference is satisfied. No catalogue match means no invented alternative.

Chat histories are separate per lead and browser session; only the last 10 messages enter the next prompt. Histories reset on server restart. Leads and follow-ups persist in the database. The shared interview demo has no login: do not enter real customer data or publish existing customer records.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests cover scoring boundaries, invalid output retries, API errors, missing input, evidence validation, saved follow-ups, lead isolation, retrieval filters and the Streamlit intake-to-planner flow. Automated AI tests mock Gemini to stay repeatable and avoid quota usage. Test a real enquiry with your own key before recording the demo.

Local verification on 21 November 2026: all 22 automated tests passed; real Gemini analysis and chat succeeded; real semantic retrieval ranked the lake-facing apartment first; dependency checks passed and the server health endpoint returned HTTP 200. A live test exposed an invented parking claim, so the prompt was strengthened and retested successfully. Browser visual review was unavailable. Hosted Supabase and public deployment have not been exercised.

## Publish when ready

GitHub publishing is left to the project owner. Create an empty public repository named `LeadPilotAI`, then run:

```powershell
git init
git add app.py src assets data/sample_properties.csv data/hybrid_leads.json tests pytest.ini requirements.txt requirements-dev.txt README.md .env.example .gitignore .streamlit/config.toml schema.sql start.ps1
git commit -m "Build LeadPilot AI assignment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/LeadPilotAI.git
git push -u origin main
```

For a free public demo, connect that repository to [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), select `app.py`, and use Python 3.13. Add these root-level values in the deployment's Secrets settings:

```toml
GEMINI_API_KEY = "your_key_here"
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

SQLite is enough for the assignment, which permits in-memory storage. On cloud hosting, local files can disappear after redeployment. For durable storage, create a free Supabase project, run `schema.sql` in its SQL editor, and add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` to Streamlit Secrets. Both must be configured together. The service key is server-only; `.env` and `secrets.toml` are ignored by Git. The SQL denies direct anonymous access while the server accesses the demo table.

Semantic dependencies include PyTorch and may require more memory than some free hosts provide. If needed, deploy the core app without `sentence-transformers` and `faiss-cpu`; property search will explicitly use its filter-only fallback. Do not claim semantic retrieval in that deployment. The dashboard reads up to 1,000 hosted leads; pagination and multi-user authentication are outside this small assignment.

After deploying, verify the public URL in a signed-out browser: create a fictional lead, ask a follow-up question, save a task and refresh. Add the actual app URL and repository URL to your submission. Neither has been published by this local setup.

## Three-minute demo

1. 0:00-0:25: Explain the problem: many enquiries, limited time to call.
2. 0:25-1:05: Fill the sample enquiry and run a real Gemini analysis. Show the quote-backed score and suggested reply.
3. 1:05-1:40: Show multiple saved leads, then ask: "What should I emphasize on the call?" and "Make my reply more assertive without sounding pushy."
4. 1:40-2:15: Save a follow-up for tomorrow, open the planner and mark it completed. Explain that advice needs a concrete next step.
5. 2:15-2:40: Show one property match and its catalogue ID. State that the catalogue is fictional.
6. 2:40-3:00: Explain one tradeoff: deterministic scores are easy to audit; LLM evidence still needs human judgment.

For different priorities, try an exploratory buyer with an undecided timeline and no financing details, and a buyer planning a purchase within 3 months with financing still pending.

## Interview talking points

- Why Gemini? It interprets unstructured enquiries and drafts contextual replies; the product actually calls an external model.
- Why Python rules? The same extracted facts always produce the same score, making disagreements explainable.
- Why LangGraph? It makes the validation/retry path visible. A plain function would also work at this size; the graph demonstrates an explicit workflow without extra agents.
- Why the planner? Salespeople need to act after reading the analysis. Dates and completion status close that gap.
- What can fail? Model interpretation, quota limits, network requests, hosting restarts and embedding downloads. Each has a visible fallback or error, with no canned AI success response.
- What next? Authentication, edit/re-analysis, measured ranking quality, and CRM integration. Voice intake was deliberately left outside the required scope.

## AI usage disclosure

Codex (ChatGPT) was used to interpret the assignment, plan the implementation, write the Python application and prompts, configure dependencies, create automated tests, debug failures, and draft this README. Gemini is the application's runtime AI: it analyzes enquiries and answers lead-specific questions. Live Gemini testing exposed an unsupported parking claim; Codex revised the prompt and retested it.

Before the interview, walk through each module and change a scoring rule yourself. Be ready to explain the code and its limitations in your own words. Update this disclosure if you use additional AI tools.

## Final submission checklist

- [ ] Public GitHub repository with this README.
- [ ] Live app URL that reviewers can open and test without setup.
- [ ] Screen-recorded demo of no more than 3 minutes showing the full workflow, the follow-up planner, and one technical or product decision.
- [x] AI usage disclosure naming the tools and their contributions, included above.

Submit all four through the company's Google Form when its link is provided. Verify that reviewers can access every submitted link, including the video, without requesting permission. Publishing and recording remain pending.
