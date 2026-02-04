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

### 5. Run the bot
```bash
# Set Topics & Keywords in main.py
KEYWORDS = dict()
KEYWORDS["3D reconstruction"] = ["neural rendering"]

MAX_RESULTS = 1

python main.py
```
Highly suggest to schedule the bot to run daily using GitHub Actions.
- [2025-08-26 Digest](2025/08/26.md)

- [2025-08-27 Digest](2025/08/27.md)

- [2025-08-28 Digest](2025/08/28.md)

- [2025-08-29 Digest](2025/08/29.md)

- [2025-08-30 Digest](2025/08/30.md)

- [2025-08-31 Digest](2025/08/31.md)

- [2025-09-01 Digest](2025/09/01.md)

- [2025-09-02 Digest](2025/09/02.md)

- [2025-09-03 Digest](2025/09/03.md)

- [2025-09-04 Digest](2025/09/04.md)

- [2025-09-05 Digest](2025/09/05.md)

- [2025-09-06 Digest](2025/09/06.md)

- [2025-09-07 Digest](2025/09/07.md)

- [2025-09-08 Digest](2025/09/08.md)

- [2025-09-09 Digest](2025/09/09.md)

- [2025-09-10 Digest](2025/09/10.md)

- [2025-09-11 Digest](2025/09/11.md)

- [2025-09-12 Digest](2025/09/12.md)

- [2025-09-13 Digest](2025/09/13.md)

- [2025-09-14 Digest](2025/09/14.md)

- [2025-09-15 Digest](2025/09/15.md)

- [2025-09-16 Digest](2025/09/16.md)

- [2025-09-17 Digest](2025/09/17.md)

- [2025-09-18 Digest](2025/09/18.md)

- [2025-09-19 Digest](2025/09/19.md)

- [2025-09-20 Digest](2025/09/20.md)

- [2025-09-21 Digest](2025/09/21.md)

- [2025-09-22 Digest](2025/09/22.md)

- [2025-09-23 Digest](2025/09/23.md)

- [2025-09-24 Digest](2025/09/24.md)

- [2025-09-25 Digest](2025/09/25.md)

- [2025-09-26 Digest](2025/09/26.md)

- [2025-09-27 Digest](2025/09/27.md)

- [2025-09-28 Digest](2025/09/28.md)

- [2025-09-29 Digest](2025/09/29.md)

- [2025-09-30 Digest](2025/09/30.md)

- [2025-10-01 Digest](2025/10/01.md)

- [2025-10-02 Digest](2025/10/02.md)

- [2025-10-03 Digest](2025/10/03.md)

- [2025-10-04 Digest](2025/10/04.md)

- [2025-10-05 Digest](2025/10/05.md)

- [2025-10-06 Digest](2025/10/06.md)

- [2025-10-07 Digest](2025/10/07.md)

- [2025-10-08 Digest](2025/10/08.md)

- [2025-10-09 Digest](2025/10/09.md)

- [2025-10-10 Digest](2025/10/10.md)

- [2025-10-11 Digest](2025/10/11.md)

- [2025-10-12 Digest](2025/10/12.md)

- [2025-10-13 Digest](2025/10/13.md)

- [2025-10-14 Digest](2025/10/14.md)

- [2025-10-15 Digest](2025/10/15.md)

- [2025-10-16 Digest](2025/10/16.md)

- [2025-10-17 Digest](2025/10/17.md)

- [2025-10-18 Digest](2025/10/18.md)

- [2025-10-19 Digest](2025/10/19.md)

- [2025-10-20 Digest](2025/10/20.md)

- [2025-10-21 Digest](2025/10/21.md)

- [2025-10-22 Digest](2025/10/22.md)

- [2025-10-23 Digest](2025/10/23.md)

- [2025-10-24 Digest](2025/10/24.md)

- [2025-10-25 Digest](2025/10/25.md)

- [2025-10-26 Digest](2025/10/26.md)

- [2025-10-27 Digest](2025/10/27.md)

- [2025-10-29 Digest](2025/10/29.md)

- [2025-10-30 Digest](2025/10/30.md)

- [2025-10-31 Digest](2025/10/31.md)

- [2025-11-01 Digest](2025/11/01.md)

- [2025-11-02 Digest](2025/11/02.md)

- [2025-11-03 Digest](2025/11/03.md)

- [2025-11-04 Digest](2025/11/04.md)

- [2025-11-05 Digest](2025/11/05.md)

- [2025-11-06 Digest](2025/11/06.md)

- [2025-11-07 Digest](2025/11/07.md)

- [2025-11-08 Digest](2025/11/08.md)

- [2025-11-09 Digest](2025/11/09.md)

- [2025-11-10 Digest](2025/11/10.md)

- [2025-11-11 Digest](2025/11/11.md)

- [2025-11-12 Digest](2025/11/12.md)

- [2025-11-13 Digest](2025/11/13.md)

- [2025-11-14 Digest](2025/11/14.md)

- [2025-11-15 Digest](2025/11/15.md)

- [2025-11-16 Digest](2025/11/16.md)

- [2025-11-17 Digest](2025/11/17.md)

- [2025-11-18 Digest](2025/11/18.md)

- [2025-11-20 Digest](2025/11/20.md)

- [2025-11-21 Digest](2025/11/21.md)

- [2025-11-22 Digest](2025/11/22.md)

- [2025-11-23 Digest](2025/11/23.md)

- [2025-11-24 Digest](2025/11/24.md)

- [2025-11-28 Digest](2025/11/28.md)

- [2025-11-29 Digest](2025/11/29.md)

- [2025-11-30 Digest](2025/11/30.md)

- [2025-12-02 Digest](2025/12/02.md)

- [2025-12-03 Digest](2025/12/03.md)

- [2025-12-04 Digest](2025/12/04.md)

- [2025-12-05 Digest](2025/12/05.md)

- [2025-12-06 Digest](2025/12/06.md)

- [2025-12-07 Digest](2025/12/07.md)

- [2025-12-09 Digest](2025/12/09.md)

- [2025-12-10 Digest](2025/12/10.md)

- [2025-12-11 Digest](2025/12/11.md)

- [2025-12-12 Digest](2025/12/12.md)

- [2025-12-13 Digest](2025/12/13.md)

- [2025-12-14 Digest](2025/12/14.md)

- [2025-12-15 Digest](2025/12/15.md)

- [2025-12-16 Digest](2025/12/16.md)

- [2025-12-17 Digest](2025/12/17.md)

- [2025-12-18 Digest](2025/12/18.md)

- [2025-12-19 Digest](2025/12/19.md)

- [2025-12-20 Digest](2025/12/20.md)

- [2025-12-21 Digest](2025/12/21.md)

- [2025-12-22 Digest](2025/12/22.md)

- [2025-12-23 Digest](2025/12/23.md)

- [2025-12-24 Digest](2025/12/24.md)

- [2025-12-25 Digest](2025/12/25.md)

- [2025-12-26 Digest](2025/12/26.md)

- [2025-12-27 Digest](2025/12/27.md)

- [2025-12-28 Digest](2025/12/28.md)

- [2025-12-29 Digest](2025/12/29.md)

- [2025-12-30 Digest](2025/12/30.md)

- [2025-12-31 Digest](2025/12/31.md)

- [2026-01-01 Digest](2026/01/01.md)

- [2026-01-02 Digest](2026/01/02.md)

- [2026-01-03 Digest](2026/01/03.md)

- [2026-01-04 Digest](2026/01/04.md)

- [2026-01-05 Digest](2026/01/05.md)

- [2026-01-06 Digest](2026/01/06.md)

- [2026-01-07 Digest](2026/01/07.md)

- [2026-01-09 Digest](2026/01/09.md)

- [2026-01-10 Digest](2026/01/10.md)

- [2026-01-11 Digest](2026/01/11.md)

- [2026-01-12 Digest](2026/01/12.md)

- [2026-01-13 Digest](2026/01/13.md)

- [2026-01-15 Digest](2026/01/15.md)

- [2026-01-16 Digest](2026/01/16.md)

- [2026-01-17 Digest](2026/01/17.md)

- [2026-01-18 Digest](2026/01/18.md)

- [2026-01-19 Digest](2026/01/19.md)

- [2026-01-20 Digest](2026/01/20.md)

- [2026-01-21 Digest](2026/01/21.md)

- [2026-01-22 Digest](2026/01/22.md)

- [2026-01-23 Digest](2026/01/23.md)

- [2026-01-24 Digest](2026/01/24.md)

- [2026-01-25 Digest](2026/01/25.md)

- [2026-01-26 Digest](2026/01/26.md)

- [2026-01-27 Digest](2026/01/27.md)

- [2026-01-28 Digest](2026/01/28.md)

- [2026-01-29 Digest](2026/01/29.md)

- [2026-01-30 Digest](2026/01/30.md)

- [2026-01-31 Digest](2026/01/31.md)

- [2026-02-01 Digest](2026/02/01.md)

- [2026-02-02 Digest](2026/02/02.md)

- [2026-02-03 Digest](2026/02/03.md)

- [2026-02-04 Digest](2026/02/04.md)
