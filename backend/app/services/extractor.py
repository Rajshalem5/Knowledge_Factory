import json
import re
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

EXTRACTOR_SYSTEM_PROMPT = """\
You are an expert AI recruitment assistant specialized in resume parsing for the Knowledge Factory platform.
Extract structured candidate information from the provided raw resume text.
Output ONLY a single valid JSON object. No markdown, no code fences, no explanation.

The JSON must follow this EXACT schema:
{
  "name": "Candidate Full Name",
  "email": "candidate@example.com",
  "phone": "Phone number with country code",
  "degree": "B.Tech | B.E. | M.Tech | MCA | BCA | B.Sc | M.Sc | MBA | Diploma",
  "branch": "Computer Science | Information Technology | AI | Electronics | etc.",
  "specialization": "Specialization within branch (e.g., Data Science, Cyber Security)",
  "college": "Full name of College/Institute",
  "university": "Affiliated University Name",
  "cgpa": 8.5,
  "percentage": "85.0%",
  "graduation_year": 2024,
  "academic_status": "Final Year | Passed Out | Pursuing",
  "skills": ["Skill 1", "Skill 2"],
  "experience_summary": "Brief summary of work and internship experience",
  "links": {
    "linkedin": "url",
    "github": "url"
  }
}

MAPPING RULES:
1. Degree: Normalize to the closest standard value (e.g., "Bachelor of Technology" -> "B.Tech").
2. Branch: Normalize common names (e.g., "CSE" -> "Computer Science", "ECE" -> "Electronics").
3. CGPA: Convert to a 10-point scale if expressed differently. If only percentage is present, calculate equivalent or set to null.
4. Percentage: Extract if explicitly mentioned (e.g., "Aggregate: 82%").
5. Graduation Year: Extract the year of completion or expected completion.
6. Academic Status: Determine if they are still studying or have graduated.
7. Skills: Extract technical and soft skills as a list of strings.

RULES:
1. If a field is missing, use null or an empty list/object as appropriate.
2. Output ONLY the JSON object."""

async def extract_candidate_info(text: str) -> dict:
    """Send raw resume text to LLM and return structured JSON."""
    if not text or not text.strip():
        return {}

    # Limit text size to avoid token overflow
    truncated_text = text[:8000]

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Extract information from this resume text:\n\n{truncated_text}"},
        ],
        "max_tokens": 3000,
        "temperature": 0.1, # Low temperature for extraction accuracy
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                settings.AI_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"LLM Extraction failed: {e}")
            return {}

    raw = resp.json()["choices"][0]["message"]["content"].strip()
    
    # Clean and parse JSON
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        logger.error(f"No JSON found in LLM response: {raw[:300]}")
        return {}

    try:
        data = json.loads(match.group(0))
        # Basic normalization: ensure email and name exist at top level for candidate creation
        if not data.get("name"):
            data["name"] = "Unknown Candidate"
        return data
    except Exception as e:
        logger.error(f"Failed to parse LLM extraction JSON: {e}")
        return {}
