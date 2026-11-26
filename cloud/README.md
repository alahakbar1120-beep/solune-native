---
title: Solune Cloud
emoji: 🌙
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

Solune Cloud experimental Groq gateway, intended for CPU Basic. The Space root is assembled by GitHub Actions. Model profiles: Solune Paper 2.6 (GPT-OSS 20B), Solune Marble 2.1 (Qwen 3.8 27B), Solune Opal 1.5 (GPT-OSS 120B). These are existing hosted models with Solune instructions, not newly trained models.

Credentials are stored as Space secrets. Do not put them in HTML, source control or client requests. Each signed session has a rolling 24h token/request allowance; a shared server ceiling additionally protects the upstream quota. Usage is held in memory and resets on server restart; anonymous sessions and public demo are not production-grade authentication. Backup keys are used on invalid credentials, never to bypass rate limits. The usage screen shows only previously observed response headers, not independently queried account balances. No Firebase integration yet.

The APK and browser use the same UI; HTML previews are sandboxed and block external resources. SVG only, not raster image generation. Verify deployment, API permissions, actual response quality and latency before production use.
