@echo off
cd /d C:\tools\Google-Map-Business-Scrapper
call .venv\Scripts\activate
uvicorn app.api:app --host 0.0.0.0 --port 3000 --reload
