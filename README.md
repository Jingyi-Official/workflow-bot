# 📨 Daily Workflow Bot

This bot automatically collects and digests your daily information into an HTML/Markdown report and sends it to your Gmail inbox.  

#### Currently it supports:

- 📄 **Daily Paper Digest**  
  Fetches the latest papers from **arXiv** based on configurable keywords, downloads PDFs, and generates structured AI-based summaries.
- 📅 **Calendar Digest**  
  Connects to **Google Calendar** and displays today's schedule in a styled HTML table inside the email.

🚀 Future Extensions: The design is modular, therefore new data sources can be added easily. Potential future integrations:

- 🌤️ **Weather Forecasts** (daily weather in your location)    
- 💹 **Finance & Market Data** (stocks, crypto, exchange rates)



## ⚙️ Setup & Usage

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/workflow-bot.git
cd workflow-bot
```

### 2. Python environment
```bash
conda create -n workflow-bot python=3.12
conda activate workflow-bot
pip install -r requirements.txt
```

### 3. Prepare Google APIs
This bot needs access to **Google Calendar** and **Gmail API**.
1. Go to [Google Cloud Console](https://console.cloud.google.com/).  
2. Enable **Calendar API** and **Gmail API**.  
3. Create **OAuth Client ID** of type *Desktop application*.  
4. Download the JSON and save it as:  
   - `credentials_calendar.json`  
   - `credentials_gmail.json`  
5. On first run, you’ll be asked to log in → tokens (`token_calendar.json`, `token_gmail.json`) will be generated automatically.  

### 4. Environment variables
Create a .env or export them in your shell:
```bash
export OPENAI_API_KEY="sk-xxxxxx" # OpenAI key for summarization
export EMAIL_FROM="yourname@gmail.com" # the Gmail address you authorized with credentials_gmail.json.
export EMAIL_TO="yourname@gmail.com" # the recipient email (can be the same as EMAIL_FROM)
export EMAIL_SUBJECT_PREFIX="[Daily Digest]"
```

### PDF summarization / PDF 摘要

The default model is `gpt-6-astra` (override with `OPENAI_MODEL`). The Responses API reads the complete PDF, including text and high-detail page images, and returns a strict JSON summary. Each PDF must be smaller than 50 MB and fit the model context. This mode uses more tokens than text-only extraction; errors are recorded in the digest rather than silently dropping content.

默认使用 `gpt-6-astra`（可通过 `OPENAI_MODEL` 覆盖）。Responses API 读取完整 PDF 的文字与高清页面图像，输出严格 JSON 摘要。单份 PDF 必须小于 50 MB，且不超过模型上下文限制。此方式比纯文本读取消耗更多 token；失败会记录到日报，不会静默截断论文。

摘要写作规则位于 [`configs/paper_summary.md`](configs/paper_summary.md)，每次生成时连同模板注释发送给模型。规则参考 [asd-ste100](https://github.com/danyuchn/asd-ste100-skill) 的 STE-flavored 模式和 [karpathy-guidelines](https://github.com/multica-ai/andrej-karpathy-skills)：使用清晰短句和一致术语，保留论文的条件与不确定性，并核对事实依据。默认仍输出中文；英文词数规则仅用于英文内容。这些规则随项目运行，无需在运行设备上安装 Codex skills，也不代表官方 STE 认证。

### 5. Run the bot
```bash
# Set Topics & Keywords in main.py
KEYWORDS = dict()
KEYWORDS["3D reconstruction"] = ["neural rendering"]

MAX_RESULTS = 1

python main.py
```
Highly suggest to schedule the bot to run daily using GitHub Actions.
