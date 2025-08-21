# main.py
import os

from arxiv_bot import run_daily_digest
from openai_bot import summarize_pdf, summary_to_markdown


# ----------- Topics & Keywords -----------
KEYWORDS = dict()
KEYWORDS["3D reconstruction"] = ["neural rendering"]

MAX_RESULTS = 1


def main():
    out_md = run_daily_digest(
        keywords_by_topic=KEYWORDS,
        max_results_per_query=MAX_RESULTS,
        summarize_pdf_fn=summarize_pdf,
        summary_to_markdown_fn=summary_to_markdown,
    )
    print(f"[OK] Updated {out_md}")


if __name__ == "__main__":
    main()