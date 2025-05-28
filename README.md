# Habits Adventure Backend

A Python FastAPI service that manages characters, habits, and habit‑driven RPG mechanics backed by a Gremlin graph database (Amazon Neptune, local Gremlin Server, etc).

## Features

- Create, read, update & delete Characters  
- Track Attributes with base scores and habit points  
- Create Habits per Attribute, record daily completions  
- Calculate DnD‑style bonuses from Attributes + Habits  
- Gremlin queries under the hood (via `gremlin_python`)

---

## 📁 Project Structure

```
habits-adventure-backend/
├── app/
│   ├── main.py             # FastAPI app
│   ├── routers/            # HTTP route definitions
│   ├── models/             # Pydantic + business logic
│   └── neptune_client.py   # Gremlin client wrapper
├── requirements.txt        # Python dependencies
└── Local_Gremlin_Testing.md
```

---

## 🛠 Prerequisites

- **Python 3.10+**  
- **Gremlin‑compatible server**
  - Amazon Neptune, or  
  - TinkerPop Gremlin Server (Docker image `tinkerpop/gremlin-server`)  
- (Optional) Docker & Docker Compose

---

## 🚀 Running Locally

1. **Clone & enter repo**  
   ```bash
   git clone https://github.com/your-username/habits-adventure-backend.git
   cd habits-adventure-backend
   ```

2. **Spin up a Gremlin server**  
   ```bash
   # If you have Docker:
   docker run -d --name gremlin-server -p 8182:8182 tinkerpop/gremlin-server
   ```
   Or configure your Amazon Neptune endpoint.

3. **Create a virtual environment & install dependencies**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment**  
   Create a `.env` (or export) with:
   ```bash
   # If using local Gremlin:
   NEPTUNE_ENDPOINT=localhost
   NEPTUNE_PORT=8182
   NEPTUNE_USE_SSL=false

   # If using Amazon Neptune:
   # NEPTUNE_ENDPOINT=your-neptune-endpoint.region.amazonaws.com
   # NEPTUNE_PORT=8182
   # NEPTUNE_USE_SSL=true
   ```

5. **Start the FastAPI server**  
   ```bash
   uvicorn app.main:app      --host 0.0.0.0 --port 8000      --reload
   ```

6. **Browse the interactive docs**  
   Open your browser at  
   ```
   http://localhost:8000/docs
   ```

---

## ⚙️ Environment Variables

| Name               | Description                         | Default  |
|--------------------|-------------------------------------|----------|
| `NEPTUNE_ENDPOINT` | Hostname of your Gremlin/Neptune DB | —        |
| `NEPTUNE_PORT`     | Port (usually 8182)                 | —        |
| `NEPTUNE_USE_SSL`  | `true` for TLS, `false` otherwise   | `false`  |

---

## 🧪 Testing

You can use the OpenAPI UI at `/docs` or send raw HTTP to the endpoints:
```http
POST /api/character
Content-Type: application/json

{
  "name": "Vigil Pathfinder",
  "strength": 12,
  "dexterity": 14,
  "constitution": 10,
  "intelligence": 19,
  "wisdom": 11,
  "charisma": 9
}
```

---

## 📖 Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)  
- [TinkerPop Gremlin Docs](https://tinkerpop.apache.org/docs/current/)  
