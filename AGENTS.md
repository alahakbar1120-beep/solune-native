# Solune 2.3 — Android build handoff

## Objective
Build a real installable ARM64 debug APK for Moto G55 5G / Android 16 from this repository. Preserve the existing UI and local engine; cloud is the default. Do not redesign from scratch.

## Build
- JDK 17, Android SDK 35, build-tools 35.0.0, NDK 27.2.12479018, CMake 3.22.1, Gradle 8.9.
- Use the SDK manager already installed on the GitHub runner, not the old setup-android action that requests the removed 'tools' package.
- Generate the Gradle wrapper if needed; run gradle :app:assembleDebug --stacktrace. Fix actual compiler errors. Keep llama.cpp pinned to b5046 unless compatibility requires a documented adjustment.
- Verify APK signature with apksigner verify and ARM64 native library. Deliver app/build/outputs/apk/debug/app-debug.apk.
- Android CI: .github/workflows/android.yml. Cloud: Railway root Dockerfile.

## Product requirements
English interface, including native notifications, settings, errors, plans, skills and usage. Response language independent of UI, with Auto/English/Russian/Ukrainian.
Profiles: Solune Paper 2.6 — Fast answers for everyday questions. Solune Marble 2.1 — Balanced intelligence for everyday tasks and creativity. Solune Opal 1.5 — Advanced reasoning, coding and complex tasks.
Use product names on regular screens. About must explain third-party models; never claim original model training. Keep actual upstream identifiers and licenses in engineering documentation and server configuration.
Cloud default via https://solune-cloud-production.up.railway.app/v1. No model downloads required for cloud. Local and demo modes remain explicit alternatives; demo must not masquerade as live generation.
Free/Pro/Dev: 20/50/100 percent of configured per-model quota; Pro/Dev require server-verified passwords for cloud. No credentials in APK, source or logs. Preserve server-side shared quota; one NVIDIA key; honor upstream rate limits. Separate personal limit from server busy message.
Code tab: dedicated coding conversations, named fenced files, downloadable code, HTML preview and SVG/PNG export. Never grant generated previews access to native bridge or remote network. Preserve chats and dark/light themes.

## Acceptance tests
1. Verify app launches with English UI and correct profile names.
2. Test cloud health and authenticated plan activation without printing secrets; test each permitted model with a short real prompt, stream and cancel. If unavailable, report deployment failure, never replace it with demo silently.
3. Test code chat creation, reopening, revision history, HTML preview with interactive inline JS, SVG display, PNG conversion and Android file picker.
4. Test Free restrictions, Pro/Dev passwords, session expiry, personal quota, upstream busy behavior and upstream errors. Session counters are in-memory and not production authentication.
5. Verify main-frame-only origin-scoped native bridge, strict navigation and sandbox. Check native local load/cancel and device lifecycle if available. Do not claim device tests without device.
6. Measure cloud response timing and verify model access if credentials are available. Report exact build/test results and limitations. No Firebase yet.
7. Build until actual success or document a concrete blocker. Do not call a source commit a finished APK.

## Railway deployment
Railway hosts the API. Configure NVIDIA_API_KEY and plan passwords in Railway Variables. No HF_TOKEN required.
