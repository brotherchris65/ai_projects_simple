## AI Resume Critique (Streamlit)

### Run locally

```bash
uv run streamlit run main.py
```

### Deploy to Streamlit Community Cloud

1. Push this folder to GitHub.
2. Go to https://share.streamlit.io and click **New app**.
3. Select repository: `brotherchris65/ai_projects_simple`
4. Branch: `main`
5. Main file path: `project2/main.py`
6. In app settings, add secret:

```toml
OPENAI_API_KEY = "your_openai_key"
```

7. Click **Deploy**.

If you update code, push to `main` and Streamlit will auto-redeploy.
