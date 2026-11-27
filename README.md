# SoluneAI 2.8

Android and browser AI chat with a shared English interface, local chat history, coding workspaces, and sandboxed HTML/SVG artifacts. Cloud is the default. Solune is an assistant product using third-party models, not independently trained weights.

| Profile | Purpose |
| --- | --- |
| Solune Paper 2.8 | Fast answers for everyday questions |
| Solune Marble 2.5 | Balanced intelligence for everyday tasks and creativity |
| Solune Opal 2.1 | Advanced reasoning, coding and complex tasks |
| Solune Onyx 3.5 | MiniMax M3.1 Flash, Code Studio exclusive, Pro and Dev |

## APK
Use JDK 17, Gradle 8.9, Android SDK 35, build-tools 35.0.0, NDK 27.2.12479018 and CMake 3.22.1. Run gradle :app:assembleDebug. APK output: app/build/outputs/apk/debug/app-debug.apk. GitHub Actions uploads SoluneAI-2.8-debug after signature and ARM64 checks. See AGENTS.md for the build and acceptance checklist.

## Cloud
Railway serves the API and shared UI at https://solune-cloud-production.up.railway.app. Set NVIDIA_API_KEY and plan passwords in Railway Variables. No HF_TOKEN required. Verify live generation before release.

## Engineering attribution
Cloud mappings are in cloud/app.py. Local models: SmolLM2-360M-Instruct, Qwen2.5-0.5B-Instruct, Qwen2.5-Coder-1.5B-Instruct GGUF Q4_K_M. Verify licenses before redistribution. Local models are not bundled in APK; downloads are optional. Cloud and local profiles differ in capability.

## Limitations
Cloud quotas are shared across profiles per signed session identity: Free 100,000 tokens, Pro 300,000, Dev no app token cap per 24-hour window from first request. SQLite stores lifetime usage and the signing key when a persistent data volume is mounted. Upstream limits still apply. Cloud accounts have a server-generated recovery code. Save it outside the app and restore the same account after reinstalling. Usage and plan are tied to that account. Creating a separate account creates a separate identity; lifetime statistics start with the current database, not historical usage. No email-based recovery. Observed provider quota headers are not aggregate account balances. No failover on quota exhaustion. SVG is vector generation, not raster image generation. External resources are disabled in HTML previews. Local engine and Android background behavior require device testing; cloud generation may stop if Android kills the app. Do not claim successful APK build or deployment without CI evidence.
