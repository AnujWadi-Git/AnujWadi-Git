# Anuj Wadi

Software engineer who builds AI-backed products end to end: APIs, integrations, deployment, and the user workflow around them. M.S. in Robotics & Autonomous Systems (AI), Arizona State University.

Previously built the APIs and staff interface for a blood-bank management system live in 3 hospitals, and trained the staff who used it.

[Portfolio](https://www.anujwadi.com) · [LinkedIn](https://linkedin.com/in/anujwadi) · [awadi@asu.edu](mailto:awadi@asu.edu)

## Featured projects

### [Clippy](https://github.com/AnujWadi-Git/Clippy): macOS clipboard manager
A native menu-bar app for finding things you copied earlier without keeping secrets around. I built the clipboard monitor, a retention worker (24 hours by default), SHA-256 deduplication and natural-language search.
- **Engineering detail:** passwords, tokens, keys and OTPs are filtered *before* anything is saved. Search combines intent parsing, keywords and on-device embeddings. On a 40-query set, top-1 accuracy rose from 70% to roughly 75–82%; [the evaluation](https://github.com/AnujWadi-Git/Clippy/blob/main/docs/SEARCH-EVAL.md) notes the run-to-run noise.
- **Verification:** 302 core checks and 35 headless end-to-end tests. Cloud AI is off by default.
- Swift, SwiftUI, on-device LLM and embeddings, OCR · [Demo and download](https://www.anujwadi.com/clippy/)

### [Yapper AI](https://github.com/AnujWadi-Git/yapper-ai-public): multi-user AI chat with RAG
A deployed FastAPI service combining tool calling with retrieval over user-uploaded documents. I built auth, conversation persistence, per-user rate limits and the browser client.
- **Engineering detail:** local ONNX embeddings (`fastembed`) replaced PyTorch to fit a 512 MB host. Daily limits are DB-backed, with a separate message when the shared model quota runs out; I reproduced that case on purpose to verify it.
- **Status:** the retrieval store is in-memory today. A pgvector swap is planned, not done. This public build uses browser speech only.
- Python, FastAPI, Postgres (Supabase), Alembic, JWT cookie auth, Render · [Live](https://yapper-ai-public.onrender.com) (free tier, may cold-start)

### [Job Search Agent](https://github.com/AnujWadi-Git/AnujWadi-Git/tree/main/job-search-agent): MCP-driven job pipeline
Claude fetches postings through the Indeed MCP connector. Deterministic, unit-tested Python then handles deduplication, filtering, classification and SQLite storage.
- **Engineering detail:** judgment calls such as "is this a duplicate?" live in testable code, not in prompts.
- Python, SQLite, MCP, Claude Code skills

### [FlipFlick](https://github.com/AnujWadi-Git/FlipFlick): movie picker
Answer three questions and get one movie. A TF-IDF recommender over about 5,200 TMDB titles builds a ranked pool, then a softmax-weighted draw picks one and explains why.
- **Engineering detail:** filters relax instead of returning zero results, and the API has per-IP rate limiting.
- Next.js, FastAPI, scikit-learn

## Skills

**Languages:** Python, TypeScript, JavaScript, Swift, Java, C++, SQL  
**Backend and cloud:** FastAPI, REST APIs, React, AWS, GCP, Docker, Kubernetes, Terraform  
**AI and ML:** LLM APIs, MCP, RAG, tool use, scikit-learn, PyTorch, TensorFlow  
**Robotics:** ROS, OpenCV, motion planning
