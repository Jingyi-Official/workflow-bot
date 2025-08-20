import os
import re
import json
import math
import tempfile
from typing import List, Dict, Any
from urllib.parse import urlparse
from urllib.request import urlopen, Request

from tqdm import tqdm
from pypdf import PdfReader
from openai import OpenAI

# ------------ Config ------------
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # change to a model you have access to
CHUNK_CHAR_LEN = 8000
OVERLAP = 500
TIMEOUT = 90

SYSTEM_INSTRUCTIONS = (
    "You are a meticulous academic reading assistant. "
    "Extract factual content from the paper text. If a field is unknown, write 'N/A'. "
    "Be concise and bullet-friendly. Return English."
)

JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "paper_title": {"type": "string"},
        "task": {"type": "string"},
        "motivation_and_gaps": {
            "type": "object",
            "properties": {
                "overview": {"type": "string"},
                "related_work_challenges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "work": {"type": "string"},
                            "challenge": {"type": "string"}
                        },
                        "required": ["work", "challenge"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["overview"],
            "additionalProperties": False
        },
        "core_idea": {"type": "string"},
        "method": {
            "type": "object",
            "properties": {
                "pipeline": {"type": "string"},
                "architecture_loss_training": {"type": "string"},
                "complexity_resources": {"type": "string"}
            },
            "required": ["pipeline"],
            "additionalProperties": False
        },
        "experiments": {
            "type": "object",
            "properties": {
                "datasets_and_metrics": {"type": "string"},
                "baselines": {"type": "array", "items": {"type": "string"}},
                "main_results": {"type": "string"},
                "ablations": {"type": "string"},
                "limitations_tests": {"type": "string"}
            },
            "required": ["main_results"],
            "additionalProperties": False
        },
        "takeaways": {
            "type": "object",
            "properties": {
                "pros_3": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
                "cons_3": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
                "future_3": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3}
            },
            "required": ["pros_3", "cons_3", "future_3"],
            "additionalProperties": False
        },
        "resources": {
            "type": "object",
            "properties": {
                "code_links": {"type": "array", "items": {"type": "string"}},
                "model_or_data_links": {"type": "array", "items": {"type": "string"}}
            },
            "additionalProperties": False
        }
    },
    "required": ["paper_title", "task", "motivation_and_gaps", "core_idea", "method", "experiments", "takeaways"],
    "additionalProperties": False
}


# ------------ Helpers ------------
def _download_if_url(path_or_url: str) -> str:
    parsed = urlparse(path_or_url)
    if parsed.scheme in ("http", "https"):
        req = Request(path_or_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=TIMEOUT) as resp, tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resp.read())
            return tmp.name
    return path_or_url

def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    txts = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        txts.append(txt)
    return "\n".join(txts)

def chunk_text(text: str, chunk_size: int = CHUNK_CHAR_LEN, overlap: int = OVERLAP) -> List[str]:
    text = re.sub(r"\n{3,}", "\n\n", text)
    chunks = []
    i, n = 0, len(text)
    while i < n:
        end = min(i + chunk_size, n)
        chunks.append(text[i:end])
        if end == n:
            break
        i = max(0, end - overlap)
    return chunks

def _client() -> OpenAI:
    return OpenAI()


# ------------ OpenAI calls ------------
def summarize_chunk(chunk: str) -> dict:
    """
    Summarize one chunk of paper text into a structured JSON dict.
    Robust against non-JSON responses.
    """
    import json
    cli = _client()
    schema_hint = {
        "paper_title": "string",
        "task": "string",
        "motivation_and_gaps": {
            "overview": "string",
            "related_work_challenges": [{"work": "string", "challenge": "string"}]
        },
        "core_idea": "string",
        "method": {
            "pipeline": "string",
            "architecture_loss_training": "string",
            "complexity_resources": "string"
        },
        "experiments": {
            "datasets_and_metrics": "string",
            "baselines": ["string"],
            "main_results": "string",
            "ablations": "string",
            "limitations_tests": "string"
        },
        "takeaways": {
            "pros_3": ["string","string","string"],
            "cons_3": ["string","string","string"],
            "future_3": ["string","string","string"]
        },
        "resources": {
            "code_links": ["string"],
            "model_or_data_links": ["string"]
        }
    }

    resp = cli.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a meticulous academic assistant. "
                    "Always output a valid single JSON object with all keys. "
                    "If a field is missing in the text, fill it with 'N/A'."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Return JSON exactly in this shape:\n"
                    f"{json.dumps(schema_hint, ensure_ascii=False)}\n\n"
                    f"Paper content chunk:\n{chunk}"
                ),
            },
        ],
    )

    text = resp.choices[0].message.content or ""
    text = text.strip()

    # Try parsing strictly
    try:
        return json.loads(text)
    except Exception:
        # Try to salvage JSON inside text
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        # If still bad, return skeleton with N/A
        return {
            "paper_title": "N/A",
            "task": "N/A",
            "motivation_and_gaps": {"overview": "N/A", "related_work_challenges": []},
            "core_idea": "N/A",
            "method": {"pipeline": "N/A", "architecture_loss_training": "N/A", "complexity_resources": "N/A"},
            "experiments": {
                "datasets_and_metrics": "N/A",
                "baselines": [],
                "main_results": "N/A",
                "ablations": "N/A",
                "limitations_tests": "N/A"
            },
            "takeaways": {
                "pros_3": ["N/A","N/A","N/A"],
                "cons_3": ["N/A","N/A","N/A"],
                "future_3": ["N/A","N/A","N/A"]
            },
            "resources": {"code_links": [], "model_or_data_links": []}
        }

def merge_partials(parts: List[Dict[str, Any]]) -> Dict[str, Any]:
    result = {
        "paper_title": "N/A",
        "task": "N/A",
        "motivation_and_gaps": {"overview": "N/A", "related_work_challenges": []},
        "core_idea": "N/A",
        "method": {"pipeline": "N/A", "architecture_loss_training": "N/A", "complexity_resources": "N/A"},
        "experiments": {
            "datasets_and_metrics": "N/A",
            "baselines": [],
            "main_results": "N/A",
            "ablations": "N/A",
            "limitations_tests": "N/A"
        },
        "takeaways": {
            "pros_3": ["N/A"] * 3,
            "cons_3": ["N/A"] * 3,
            "future_3": ["N/A"] * 3
        },
        "resources": {"code_links": [], "model_or_data_links": []}
    }
    for p in parts:
        for k in ["paper_title", "task", "core_idea"]:
            if p.get(k) and p[k] != "N/A":
                result[k] = p[k]
        if "motivation_and_gaps" in p:
            mo = p["motivation_and_gaps"]
            if isinstance(mo.get("overview"), str) and mo["overview"] != "N/A":
                result["motivation_and_gaps"]["overview"] = mo["overview"]
            rws = mo.get("related_work_challenges") or []
            if isinstance(rws, list):
                result["motivation_and_gaps"]["related_work_challenges"].extend(rws)
        if "method" in p:
            for k in ["pipeline", "architecture_loss_training", "complexity_resources"]:
                v = p["method"].get(k)
                if isinstance(v, str) and v and v != "N/A":
                    result["method"][k] = v
        if "experiments" in p:
            e = p["experiments"]
            for k in ["datasets_and_metrics", "main_results", "ablations", "limitations_tests"]:
                v = e.get(k)
                if isinstance(v, str) and v and v != "N/A":
                    result["experiments"][k] = v
            bl = e.get("baselines") or []
            if isinstance(bl, list):
                result["experiments"]["baselines"].extend([x for x in bl if isinstance(x, str)])
        if "takeaways" in p:
            for arr in ["pros_3", "cons_3", "future_3"]:
                cand = p["takeaways"].get(arr)
                if isinstance(cand, list) and any(x and x != "N/A" for x in cand):
                    if all(x == "N/A" for x in result["takeaways"][arr]):
                        result["takeaways"][arr] = [x for x in cand if x and x != "N/A"][:3]
        if "resources" in p:
            for k in ["code_links", "model_or_data_links"]:
                arr = p["resources"].get(k) or []
                if isinstance(arr, list):
                    result["resources"][k].extend([x for x in arr if isinstance(x, str)])

    # dedupe
    result["experiments"]["baselines"] = sorted(set(result["experiments"]["baselines"]))
    for k in ["code_links", "model_or_data_links"]:
        result["resources"][k] = sorted(set(result["resources"][k]))
    return result


# ------------ Public API ------------
def summarize_pdf(pdf_path_or_url: str) -> Dict[str, Any]:
    local = _download_if_url(pdf_path_or_url)
    text = extract_text(local)
    chunks = chunk_text(text, CHUNK_CHAR_LEN, OVERLAP)
    parts: List[Dict[str, Any]] = []
    for ch in tqdm(chunks, desc="Summarizing PDF"):
        parts.append(summarize_chunk(ch))
    return merge_partials(parts)


def summary_to_markdown(s: Dict[str, Any]) -> str:
    md = f"""
    <details>
    <summary>📄 Paper Summary (click to expand)</summary>

    ### 1. Task / Problem
    {s['task']}

    ### 2. Motivation & Gaps
    {s['motivation_and_gaps']['overview']}
    """

    # Related work challenges
    rws = s['motivation_and_gaps'].get('related_work_challenges') or []
    if rws:
        md += "\n**Related work challenges:**\n"
        for item in rws:
            md += f"- {item.get('work','?')}: {item.get('challenge','')}\n"

    md += f"""
    ### 3. Core Idea
    {s['core_idea']}

    ### 4. Method
    - **Pipeline**: {s['method']['pipeline']}
    - **Architecture / Loss / Training**: {s['method']['architecture_loss_training']}
    - **Complexity / Resources**: {s['method']['complexity_resources']}

    ### 5. Experiments
    - **Datasets & Metrics**: {s['experiments']['datasets_and_metrics']}
    - **Baselines**: {", ".join(s['experiments']['baselines']) if s['experiments']['baselines'] else "N/A"}
    - **Main Results**: {s['experiments']['main_results']}
    - **Ablations**: {s['experiments']['ablations']}
    - **Limitations / Stress Tests**: {s['experiments']['limitations_tests']}

    ### 6. Takeaways
    - **Pros**: {", ".join(s['takeaways']['pros_3'])}
    - **Cons**: {", ".join(s['takeaways']['cons_3'])}
    - **Future Work**: {", ".join(s['takeaways']['future_3'])}

    </details>
    """
    return md