@echo off
title RAG CONVERSATIONAL API
color 0B
D:
cd palm_mind_task
call venv\Scripts\activate.bat
python banner.py
python -m uvicorn app.main:app --reload --port 8000