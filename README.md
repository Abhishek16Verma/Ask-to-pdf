# Ask to PDF

Ask questions over your PDF documents using a Retrieval-Augmented Generation (RAG) pipeline built with FastAPI, LangChain, Qdrant, and Groq/Ollama.

## What this project does

- Uploads PDF files through an API.
- Splits text into chunks and stores embeddings in Qdrant.
- Retrieves relevant chunks for a question.
- Sends retrieved context to an LLM and returns an answer.
- Supports normal and streaming answer endpoints.

## Tech stack

- FastAPI for API server
- LangChain for RAG orchestration
- Qdrant as vector database
- HuggingFace sentence-transformers for embeddings
- Groq (default) or Ollama for chat completion
- Docker Compose for local Qdrant/Redis services

## Project structure

```text
ask_to_pdf/
	app/
		main.py                # FastAPI app and endpoints
		embeddings.py
		rag.py
	pdf_loader/
		ingest.py              # PDF ingestion and vector indexing
		query.py               # Retrieval + prompt + LLM chain
	utils/
		config.py              # Environment-based settings
		redis_setup.py
	compose/
		docker-compose-qdrant.yaml
	uploads/                 # Uploaded PDFs
	requirements.txt
	.env.example
```

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- A Groq API key (if using Groq)
- Optional: Ollama installed locally (if using Ollama)

## Quick start

### 1. Clone and enter project

```bash
git clone https://github.com/Abhishek16Verma/Ask-to-pdf.git
cd Ask-to-pdf/ask_to_pdf
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create environment file

Create a file named `.env` in the project root and add values like:

```env
# Vector DB
QDRANT_HOST=http://localhost:6333
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=ask_to_pdf_collection

# LLM
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Embeddings
MODEL_NAME=all-MiniLM-L6-v2
MODEL_DEVICE=cpu
```

Notes:

- `QDRANT_HOST` is used in query flow.
- `QDRANT_URL` is used in ingestion flow.
- Keeping both set to the same URL avoids mismatches.

### 5. Start Qdrant (and Redis)

```bash
docker compose -f compose/docker-compose-qdrant.yaml up -d
```

### 6. Run API server

```bash
python -m app.main
```

This starts the API on `0.0.0.0:8585` by default. You can override via `.env`:

```env
APP_HOST=0.0.0.0
APP_PORT=8585
APP_RELOAD=true
```

Open docs at http://127.0.0.1:8585/docs

## API usage

### Health

```bash
curl http://127.0.0.1:8585/health
```

### Upload a PDF

```bash
curl -X POST "http://127.0.0.1:8585/upload" \
	-H "accept: application/json" \
	-H "Content-Type: multipart/form-data" \
	-F "file=@/absolute/path/to/your.pdf"
```

### Ask a question

```bash
curl -X POST "http://127.0.0.1:8585/ask" \
	-H "Content-Type: application/json" \
	-d '{
		"question": "Summarize the key points",
		"session_id": "demo-session-1"
	}'
```

### Stream an answer

```bash
curl -N -X POST "http://127.0.0.1:8585/ask-stream" \
	-H "Content-Type: application/json" \
	-d '{
		"question": "What are the action items?",
		"session_id": "demo-session-1"
	}'
```

## Configuration reference

Environment variables used by the current code:

- `QDRANT_HOST` (default: `http://localhost:6333`)
- `QDRANT_URL` (default: `http://localhost:6333`)
- `COLLECTION_NAME` (default: `ask_to_pdf_collection`)
- `GROQ_API_KEY` (required for Groq mode)
- `GROQ_MODEL` (model name for Groq)
- `MODEL_NAME` (default: `all-MiniLM-L6-v2`)
- `MODEL_DEVICE` (default: `cpu`)

## Troubleshooting

### "Unexpected message type: history"

This happens if a prompt role named `history` is used directly.
Current code uses a proper `MessagesPlaceholder` and should no longer fail with this error.

### Pull asks for branch reconciliation

Set a default pull strategy once:

```bash
git config --global pull.rebase false
```

or use fast-forward only:

```bash
git config --global pull.ff only
```

### Ignored files still showing in git

If files were tracked before `.gitignore`, untrack once:

```bash
git rm -r --cached --ignore-unmatch .env '**/__pycache__/**' '*.pyc'
git commit -m "Stop tracking local env/cache files"
```

## Development notes

- Uploaded files are stored in `uploads/`.
- Ingestion creates embeddings and writes vectors into Qdrant collection.
- Query path retrieves top-k chunks (currently k=3) and sends them to the LLM.

## License

No license file is currently included in this repository.
