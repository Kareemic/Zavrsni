---
title: AI Code Detector
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# AI Code Detector

Web aplikacija za detekciju AI generiranog koda. Koristi Random Forest klasifikator s ekstrakcijom značajki putem tree-sitter parsera.

## API

- `GET /api/health` — status servera
- `POST /api/analyze` — analiza jednog isječka koda
- `POST /api/analyze-batch` — batch analiza (streaming)
- `POST /api/similarity` — međusobna sličnost kodova
