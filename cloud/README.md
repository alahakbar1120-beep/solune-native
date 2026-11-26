---
title: Solune Cloud
emoji: 🌙
colorFrom: yellow
colorTo: gray
sdk: gradio
app_file: app.py
pinned: false
---

Experimental Solune inference backend. Select ZeroGPU hardware in Space settings. Copy only this directory's three files into the Space root. The Gradio API endpoint is /generate with inputs [model display name, prompt, history JSON, maximum output tokens]. This is a public demo; do not send sensitive information. The models use original open weights with Solune system instructions. GPU availability, Russian output quality and actual latency require testing. Android client is not yet connected.
