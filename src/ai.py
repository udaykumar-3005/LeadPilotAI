import os

from google import genai
from google.genai import errors, types

def generate(prompt, system, schema=None):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Add GEMINI_API_KEY to .env, then restart the app.")
    config = {"system_instruction": system, "temperature": 0.2}
    if schema:
        config.update(response_mime_type="application/json", response_schema=schema)
    try:
        options = types.HttpOptions(timeout=30000, retry_options=types.HttpRetryOptions(attempts=1))
        with genai.Client(api_key=key, http_options=options) as client:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                contents=prompt,
                config=types.GenerateContentConfig(**config),
            )
        if not response.text:
            raise RuntimeError("Gemini returned no answer. Try rephrasing the enquiry.")
        return response.text
    except errors.APIError as exc:
        messages = {
            400: "Gemini rejected the request. Check your key and model setting.",
            401: "Gemini authentication failed. Check your API key.",
            403: "Gemini access was denied. Check your key and model access.",
            404: "Gemini model unavailable. Update GEMINI_MODEL in .env.",
            429: "Gemini quota reached. Wait and try again, or check your free-tier quota.",
        }
        raise RuntimeError(messages.get(exc.code, "Gemini is unavailable. Please try again shortly.")) from None
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError("Could not reach Gemini. Check your connection and try again.") from None
