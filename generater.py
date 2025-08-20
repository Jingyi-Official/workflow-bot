# generate_daily_digest.py
import os
import arxiv
from datetime import datetime, timezone
from textwrap import dedent

from summarizer import summarize_pdf, summary_to_markdown

# ----------- Topics & Keywords -----------
KEYWORDS = dict()
KEYWORDS["3D reconstruction"] = ["neural rendering"]

MAX_RESULTS = 1

# ----------- arXiv client -----------
client = arxiv.Client(
    page_size=MAX_RESULTS,
    delay_seconds=3,
    num_retries=3,
)

def get_papers(query: str, max_results: int = 100):
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    return list(client.results(search))

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def read_text(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def append_text(path: str, content: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please set OPENAI_API_KEY as a secret or environment variable.")

    now = datetime.now(timezone.utc).astimezone()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    # Daily digest path: YYYY/MM/DD.md
    out_dir = os.path.join(".", year, month)
    ensure_dir(out_dir)
    out_md = os.path.join(out_dir, f"{day}.md")

    # Header (create if missing)
    if not os.path.exists(out_md):
        today_full = now.strftime("%Y-%m-%d")
        header = dedent(f"""\
        # Daily Paper Digest · {today_full}
        > Auto-generated: Recent submissions from arXiv are fetched by topic and keyword (up to {MAX_RESULTS} papers per query).
        """)
        write_text(out_md, header)

    # Dedup guard: skip if arXiv entry_id already present in the file
    existing = read_text(out_md)

    for topic, keywords in KEYWORDS.items():
        # append_text(out_md, f"\n## {topic}\n")
        for kw in keywords:
            append_text(out_md, f"\n## {kw}\n")
            results = get_papers(query=kw, max_results=MAX_RESULTS)
            if not results:
                append_text(out_md, "- (No results)\n")
                continue

            for r in results:
                entry_id = getattr(r, "entry_id", None) or ""
                pdf_url = getattr(r, "pdf_url", None) or entry_id
                title = r.title.replace("\n", " ").strip()
                published = r.published.strftime("%Y-%m-%d") if r.published else "N/A"

                # Skip if already in digest (simple ID check)
                if entry_id and entry_id in existing:
                    continue

                # Summarize PDF
                try:
                    summary = summarize_pdf(pdf_url)
                    summary_md = summary_to_markdown(summary)

                    # Prepend a small paper header with link/date
                    paper_head = f"### {title} [PDF]({pdf_url})\n\n"
                    append_text(out_md, paper_head + summary_md)

                    # Update existing cache to avoid duplicates in the same run
                    existing += entry_id
                except Exception as e:
                    append_text(out_md, f"### {title} [PDF]({pdf_url})\n  (summary failed: {e})\n\n")

    # Optional: update README with a link to today's digest
    readme_path = "README.md"
    rel_link = f"{year}/{month}/{day}.md"
    link_line = f"- [{year}-{month}-{day} Digest]({rel_link})\n"
    if os.path.exists(readme_path):
        txt = read_text(readme_path)
        if link_line not in txt:
            append_text(readme_path, "\n" + link_line)
    else:
        write_text(readme_path, "# Daily ArXiv Digest\n\n" + link_line)

    print(f"[OK] Updated {out_md}")

if __name__ == "__main__":
    main()