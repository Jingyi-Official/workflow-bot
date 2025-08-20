import os
import arxiv
from datetime import datetime, timezone
from textwrap import dedent


KEYWORDS = dict()
KEYWORDS["neural rendering"] = ["neural rendering", "radience field", "novel view synthesis", "NeRF", "light field"]
KEYWORDS["3D reconstruction"] = ["3D reconstruction", "surface reconstruction", "neural surface reconstruction"]

MAX_RESULTS = 5

# ========== arXiv Client ==========
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

def build_markdown():
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    header = dedent(f"""\
    # 每日论文速递 · {today}

    > 自动生成：按主题与关键词从 arXiv 抓取最近投稿（每类最多 {MAX_RESULTS} 篇）。
    """)
    lines = [header]

    for topic, keywords in KEYWORDS.items():
        lines.append(f"\n## {topic}\n")
        for kw in keywords:
            lines.append(f"### 🔍 {kw}\n")
            results = get_papers(query=kw, max_results=MAX_RESULTS)
            if not results:
                lines.append("- （无结果）\n")
                continue

            for r in results:
                published = r.published.strftime("%Y-%m-%d") if r.published else "N/A"
                title = r.title.replace("\n", " ").strip()
                pdf = r.pdf_url or r.entry_id
                # 如果需要摘要，打开下一行（摘要较长，默认先不展开）
                # summary = (r.summary or "").replace("\n", " ").strip()
                lines.append(f"- **{title}**  \n  发布：{published}  ·  [PDF]({pdf})\n")
                # 想展开摘要可加：\n  摘要：{summary}\n

    return "\n".join(lines)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def main():
    # 以“日期”命名的文件夹
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    out_dir = os.path.join(".", today)
    ensure_dir(out_dir)

    # Markdown 文件名
    out_md = os.path.join(out_dir, "summary.md")
    content = build_markdown()
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(content)

    # 额外：更新一个根目录 README 指向今日文件（可选）
    readme_path = "README.md"
    link_line = f"- [{today} 的汇总]({today}/summary.md)\n"
    if os.path.exists(readme_path):
        with open(readme_path, "r+", encoding="utf-8") as rf:
            txt = rf.read()
            if link_line not in txt:
                rf.seek(0, os.SEEK_END)
                rf.write("\n" + link_line)
    else:
        with open(readme_path, "w", encoding="utf-8") as rf:
            rf.write("# Daily ArXiv Digest\n\n" + link_line)

    print(f"[OK] 已生成 {out_md}")

if __name__ == "__main__":
    main()