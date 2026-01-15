# Azure Cost Optimization Agent (MVP)

**Run locally**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY if you want summaries
streamlit run app/main.py
