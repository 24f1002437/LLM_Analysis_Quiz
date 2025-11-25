# LLM Quiz Project — Flask + Gemini + Playwright (Render-ready)

This project implements the `/api/quiz` endpoint for the LLM Analysis Quiz assignment.

## Features
- Verifies incoming POST secrets
- Uses Playwright to render JS-heavy quiz pages
- Downloads and parses CSV/XLSX/PDF files
- Uses Gemini (Google Generative AI) for reasoning
- Submits answers to the submit URL found on quiz pages
- Deploy-ready for Render (render.yaml included)

## Quickstart (local)
1. Clone repo and `cd backend`
2. Create virtualenv and activate
3. Install packages:
