# main.py
import os

from arxiv_bot import run_daily_digest
from openai_bot import summarize_pdf, summary_to_markdown


# ----------- Topics & Keywords -----------
KEYWORDS = dict()
KEYWORDS["3D reconstruction"] = ["neural rendering"]

# 每个关键词最多抓取多少篇
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
    # 运行前需提供 OPENAI_API_KEY（以及可选的 OPENAI_MODEL）
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please set OPENAI_API_KEY as a secret or environment variable.")
    main()