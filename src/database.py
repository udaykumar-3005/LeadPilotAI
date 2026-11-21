import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx

from src.models import Followup


def hosted():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if bool(url) != bool(key):
        raise RuntimeError("Set both Supabase settings, or leave both blank for local storage.")
    return bool(url)


def remote(method, **kwargs):
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/leads"
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Prefer": "return=representation"}
    try:
        response = httpx.request(method, url, headers=headers, timeout=15, **kwargs)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        raise RuntimeError("Database unavailable. Check Supabase settings and run schema.sql.") from None


@contextmanager
def connection():
    path = Path(os.getenv("DATABASE_PATH", "data/leads.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS leads (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        with db:
            yield db
    except sqlite3.Error:
        raise RuntimeError("Could not access the local database. Check the data folder.") from None
    finally:
        db.close()


def list_leads():
    if hosted():
        return remote("GET", params={"select": "*", "order": "created_at.desc", "limit": "1000"})
    with connection() as db:
        return [json.loads(row[0]) for row in db.execute("SELECT payload FROM leads")]


def save_lead(lead, analysis):
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "lead": lead.model_dump(),
        "analysis": analysis,
        "followup": None,
    }
    if hosted():
        remote("POST", json=record)
    else:
        with connection() as db:
            db.execute("INSERT INTO leads VALUES (?, ?)", (record["id"], json.dumps(record)))
    return record


def save_followup(lead_id, followup):
    data = Followup.model_validate(followup).model_dump()
    if hosted():
        rows = remote("PATCH", params={"id": f"eq.{lead_id}"}, json={"followup": data})
        if not rows:
            raise RuntimeError("Lead no longer exists. Refresh the dashboard.")
    else:
        with connection() as db:
            row = db.execute("SELECT payload FROM leads WHERE id = ?", (lead_id,)).fetchone()
            if not row:
                raise RuntimeError("Lead no longer exists. Refresh the dashboard.")
            record = json.loads(row[0])
            record["followup"] = data
            db.execute("UPDATE leads SET payload = ? WHERE id = ?", (json.dumps(record), lead_id))


def delete_lead(lead_id):
    if hosted():
        remote("DELETE", params={"id": f"eq.{lead_id}"})
    else:
        with connection() as db:
            db.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
