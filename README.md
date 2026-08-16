# Render Chat App

A simple FastAPI backend that provides a `POST /api/chat` endpoint backed by OpenAI's Chat Completion API, and a premium‑looking static web page that talks to it.

## Project structure
```
.
├─ main.py               # FastAPI app, serves static files and `/api/chat`
├─ requirements.txt      # Python dependencies
├─ .gitignore            # Excludes caches, compiled files and `.env`
├─ static/
│   ├─ index.html        # Chat UI (dark glassmorphism theme)
│   └─ style.css         # Styles for the UI
└─ README.md             # This file
```

## How to run locally (optional)
```bash
# (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate  # PowerShell

# Install dependencies
pip install -r requirements.txt

# Set environment variables (do NOT commit them!)
$env:OPENAI_API_KEY="<your‑api‑key>"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"

# Start the server (Render uses the same command)
uvicorn main:app --host 0.0.0.0 --port 8000
```
Open http://localhost:8000 in a browser – you should see the chat UI.

## Deploy to Render
1. **Create a GitHub repository**
   - Name: **render-chat-app** (public).  
   - Push the files in this folder to the repo.
2. **Log in to Render** and click **New → Web Service**.
3. **Connect the GitHub repository** you just created.
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. **Environment Variables** (add in Render UI, do NOT commit to the repo):
   - `OPENAI_API_KEY` – your OpenAI API key.
   - `OPENAI_BASE_URL` – usually `https://api.openai.com/v1`.
7. Click **Create Web Service** and wait for the deployment to finish.

When the service is live, the root URL (`https://render-chat-app-f56x.onrender.com`) will display the chat page, and the same origin will serve the `/api/chat` endpoint.

## Testing the deployed service
You can use Yaak (or any HTTP client like `curl`) to issue a request:
```bash
curl -X POST https://render-chat-app-f56x.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```
You should receive a JSON response containing the assistant's reply and model info (`{"reply": "...", "model": "gemma-4-E4B-it"}`).

---
Feel free to customise the UI (logo, colors, etc.) – just edit `static/index.html` and `static/style.css` and push the changes.
