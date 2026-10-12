# main.py
import os
from datetime import datetime

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

# Final papers per keyword; preferences live in configs/paper_preferences.json.
MAX_RESULTS = 3

def main():
    # 1) ----------- generate daily arXiv digest -----------
    arXiv_md = run_daily_digest(
        keywords_by_topic=KEYWORDS,
        max_results_per_query=MAX_RESULTS,
        summarize_pdf_fn=summarize_pdf,
        summary_to_markdown_fn=summary_to_markdown,
    )
    arXiv_html = markdown(Path(arXiv_md).read_text(encoding="utf-8"),
                      output_format="html5",
                      extensions=["extra","sane_lists","nl2br","tables","fenced_code","toc","md_in_html"])

    # 2) ----------- generate daily Calendar digest -----------
    events = fetch_todays_events()
    cal_html = events_to_html(events)

    # 3) ----------- write email -----------
    today = datetime.now().strftime("%Y-%m-%d")
    subject_prefix = os.getenv("EMAIL_SUBJECT_PREFIX", "[Daily Digest]")
    subject = f"{subject_prefix} {today}"

    env = Environment(loader=FileSystemLoader(str(CONFIGS_DIR)))
    template = env.get_template("email_template.html")

    combined_html = template.render(
        title=f"Daily Digest {today}",
        arXiv_html=arXiv_html,
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
