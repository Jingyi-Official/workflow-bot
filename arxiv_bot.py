# arxiv_bot.py
import os
from datetime import datetime, timezone
from textwrap import dedent
from typing import Dict, List

import arxiv


# ----------- arXiv client -----------
def make_client(page_size: int = 3, delay_seconds: int = 3, num_retries: int = 3) -> arxiv.Client:
    return arxiv.Client(
        page_size=page_size,
        delay_seconds=delay_seconds,
        num_retries=num_retries,
    )


def get_papers(client: arxiv.Client, query: str, max_results: int = 100) -> List[arxiv.Result]:
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    return list(client.results(search))


# ----------- File I/O utils -----------
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


# ----------- Digest runner -----------
def run_daily_digest(
    keywords_by_topic: Dict[str, List[str]],
    max_results_per_query: int,
    summarize_pdf_fn,
    summary_to_markdown_fn,
) -> str:
    """
    执行一次“每日摘要”生成。
    - keywords_by_topic: 主题 -> 关键词列表
    - max_results_per_query: 每个关键词最多取多少篇
    - summarize_pdf_fn: 函数(pdf_url) -> 结构化摘要dict
    - summary_to_markdown_fn: 函数(summary_dict) -> markdown字符串

    返回值：生成/更新的 Markdown 文件路径（YYYY/MM/DD.md）
    """
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
        > Auto-generated: Recent submissions from arXiv are fetched by topic and keyword (up to {max_results_per_query} papers per query).
        """)
        write_text(out_md, header)

    # Dedup guard: skip if arXiv entry_id already present in the file
    existing = read_text(out_md)

    client = make_client(page_size=max_results_per_query)

    for topic, keywords in keywords_by_topic.items():
        # 你可以将 topic 也写入分组（如果想显示 topic 标题，把下面一行取消注释）
        # append_text(out_md, f"\n## {topic}\n")
        for kw in keywords:
            append_text(out_md, f"\n## {kw}\n")
            results = get_papers(client, query=kw, max_results=max_results_per_query)
            if not results:
                append_text(out_md, "- (No results)\n")
                continue

            for r in results:
                entry_id = getattr(r, "entry_id", None) or ""
                pdf_url = getattr(r, "pdf_url", None) or entry_id
                title = r.title.replace("\n", " ").strip()
                # published = r.published.strftime("%Y-%m-%d") if r.published else "N/A"  # 如需显示日期可启用

                # Skip if already in digest (simple ID check)
                if entry_id and entry_id in existing:
                    continue

                # Summarize PDF
                try:
                    summary = summarize_pdf_fn(pdf_url)
                    summary_md = summary_to_markdown_fn(summary)
                    paper_head = f"### [{title}]({pdf_url})\n\n"
                    append_text(out_md, paper_head + summary_md)
                    # Update existing cache to avoid duplicates in the same run
                    existing += entry_id
                except Exception as e:
                    append_text(out_md, f"### [{title}]({pdf_url})\n  (summary failed: {e})\n\n")

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

    return out_md