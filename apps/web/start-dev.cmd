@echo off
cd /d D:\Everest\apps\web
set NEXT_PUBLIC_EVEREST_API_BASE_URL=http://localhost:50149
echo Starting Everest frontend on http://localhost:50151
echo Keep this window open.
npm run dev
