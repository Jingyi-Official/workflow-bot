# main.py
import os
import re
from datetime import datetime
from html import escape

from bots import CONFIGS_DIR
from bots.arxiv_bot import run_daily_digest
from bots.openai_bot import summarize_pdf, summary_to_markdown
from bots.calendar_bot import fetch_todays_events, events_to_markdown, events_to_html
from bots.email_bot import send_email
from markdown import markdown
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# ----------- Topics & Keywords -----------
KEYWORDS = dict()
KEYWORDS["deep learning"] = ["model collapse"]
KEYWORDS["digital humans and drivable avatars"] = ["head avatars", "full-body avatars", "audio-driven facial animation", "talking-head animation", "Lip Synchronization"]
KEYWORDS["video generation"] = ["video generation", "diffusion models", "video Continuation", "temporal autoregression"]
KEYWORDS["world models"] = ["world models"]

# Final papers per topic across all keywords; preferences live in configs/paper_preferences.json.
MAX_RESULTS_PER_TOPIC = 5


def paper_topic_sections(source: str, keywords_by_topic: dict) -> list[dict]:
    """Group new topic headings and legacy keyword headings into email cards."""
    keyword_topics = {
        keyword: topic for topic, keywords in keywords_by_topic.items() for keyword in keywords
    }
    grouped = {}
    current = None
    def keyword_heading(label):
        return (
            '<h3 style="font-size:26px; line-height:1.3; font-weight:700; '
            'margin:24px 0 16px;">' + escape(label) + '</h3>'
        )

    for line in source.splitlines():
        if re.match(r"^# Daily Paper Digest\b", line):
            continue
        if line.startswith("## "):
            heading = line[3:].strip()
            current = heading if heading in keywords_by_topic else keyword_topics.get(heading, heading)
            grouped.setdefault(current, [])
            if heading != current:
                grouped[current].append(keyword_heading(heading))
            continue
        if current is not None:
            if line.startswith("### ") and line[4:].strip() in keywords_by_topic.get(current, []):
                line = keyword_heading(line[4:].strip())
            grouped[current].append(line)
    return [
        {"title": topic, "html": markdown(
            "\n".join(lines), output_format="html5",
            extensions=["extra", "sane_lists", "nl2br", "tables", "fenced_code", "md_in_html"],
        )}
        for topic, lines in grouped.items()
    ]


def main():
    # 1) ----------- generate daily arXiv digest -----------
    arXiv_md = run_daily_digest(
        keywords_by_topic=KEYWORDS,
        max_results_per_topic=MAX_RESULTS_PER_TOPIC,
        summarize_pdf_fn=summarize_pdf,
        summary_to_markdown_fn=summary_to_markdown,
    )
    paper_topics = paper_topic_sections(Path(arXiv_md).read_text(encoding="utf-8"), KEYWORDS)

    # 2) ----------- generate daily Calendar digest -----------
    events = fetch_todays_events()
    cal_html = events_to_html(events)

    # 3) ----------- write email -----------
    today = datetime.now().strftime("%Y-%m-%d")
    subject_prefix = os.getenv("EMAIL_SUBJECT_PREFIX", "[Weekly Digest]")
    subject = f"{subject_prefix} {today}"

    env = Environment(loader=FileSystemLoader(str(CONFIGS_DIR)))
    template = env.get_template("email_template.html")

    combined_html = template.render(
        title=f"Weekly Digest {today}",
        paper_topics=paper_topics,
        cal_html=cal_html
    )

    # 4) ----------- send email -----------
    send_email(
        subject=subject,
        body_markdown="This message is best viewed in HTML.",  
        html_body=combined_html,                                
    )
    
    print("[OK] Email sent.")


if __name__ == "__main__":
    main()
