# arxiv_bot.py
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import arxiv

from . import PROJECT_DIR
from .paper_filter import CONFIG_PATH, PaperRanker, paper_id


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
    preferences_path: str | Path = CONFIG_PATH,
) -> str:
    """
    执行一次“每日摘要”生成。
    - keywords_by_topic: 主题 -> 关键词列表
    - max_results_per_query: 每个关键词最多取多少篇
    - summarize_pdf_fn: 函数(pdf_url) -> 结构化摘要dict
    - summary_to_markdown_fn: 函数(summary_dict) -> markdown字符串
    - preferences_path: 机构、会议期刊及排序规则的 JSON 配置路径

    返回值：本地 Markdown 文件的绝对路径（digests/YYYY/MM/DD.md）
    """
    if max_results_per_query < 1:
        raise ValueError("max_results_per_query must be positive.")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please set OPENAI_API_KEY as a secret or environment variable.")

    project_dir = PROJECT_DIR
    ranker = PaperRanker(project_dir / "digests" / ".cache" / "affiliations", preferences_path)
    candidate_count = ranker.candidate_count(max_results_per_query)

    now = datetime.now(timezone.utc).astimezone()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    # Keep generated reports in a Git-ignored directory beside this module.
    out_dir = str(project_dir / "digests" / year / month)
    ensure_dir(out_dir)
    out_md = os.path.join(out_dir, f"{day}.md")

    # Topic headings replace the redundant daily report title.
    if not os.path.exists(out_md):
        write_text(out_md, "")

    # Compare canonical IDs so PDF/abstract links and different versions deduplicate.
    existing = read_text(out_md)
    seen = {
        re.sub(r"v\d+$", "", value.removesuffix(".pdf"))
        for value in re.findall(r"https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/([^\s)]+)", existing)
    }
    client = make_client(page_size=candidate_count)

    for topic, keywords in keywords_by_topic.items():
        append_text(out_md, f"\n## {topic}\n")
        for kw in keywords:
            append_text(out_md, f"\n### {kw}\n")
            results = get_papers(client, query=kw, max_results=candidate_count)
            ranker.note_api_request()
            if not results:
                append_text(out_md, "- (No results)\n")
                continue

            candidates = []
            candidate_ids = set()
            for result in results:
                identity = paper_id(result)
                if identity not in seen and identity not in candidate_ids:
                    candidates.append(result)
                    candidate_ids.add(identity)
            if not candidates:
                append_text(out_md, "- (No new papers)\n")
                continue

            selected = 0
            for ranked in ranker.rank(candidates):
                if selected >= max_results_per_query:
                    break
                r = ranked.result
                identity = paper_id(r)
                pdf_url = getattr(r, "pdf_url", None) or getattr(r, "entry_id", "")
                title = r.title.replace("\n", " ").strip()
                # Summarize PDF
                try:
                    summary = summarize_pdf_fn(pdf_url)
                    summary["paper_title"] = title
                    summary["paper_url"] = pdf_url
                    summary_md = summary_to_markdown_fn(summary)
                    append_text(out_md, "\n" + summary_md)
                    seen.add(identity)
                    selected += 1
                    print(f"[SELECT] {title}: {ranked.reason()}")
                except Exception as e:
                    append_text(out_md, f"\n### [{title}]({pdf_url})\n  (summary failed: {e})\n\n")

    return out_md
