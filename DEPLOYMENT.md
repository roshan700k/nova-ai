# NOVA AI Deployment Guide

## Overview
NOVA AI can be deployed to Render.com (free tier) for public access.

## Prerequisites
- GitHub account
- Render.com account (free)
- Gemini API key
- Google OAuth credentials (optional, for Gmail login)

## Step 1: Prepare Repository

1. Push your code to GitHub:
```bash
cd C:\Users\user\ASTRA-AI
git remote add origin https://github.com/yourusername/nova-ai.git
git push -u origin master
```

2. Ensure `render.yaml` is in the root directory (already created).

## Step 2: Deploy to Render

1. Go to https://render.com
2. Sign up/login with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Render will auto-detect `render.yaml`
6. Click "Create Web Service"

## Step 3: Configure Environment Variables

In Render dashboard → your service → "Environment":

```
PYTHON_VERSION=3.12.0
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLIENT_ID=your_google_client_id (optional)
GOOGLE_CLIENT_SECRET=your_google_client_secret (optional)
SESSION_SECRET=random_secret_key_here
DEV_AUTH=false
ASTRA_DB_PATH=/var/data/astra.db
MEMORY_FILE_PATH=/var/data/memory.json
LOG_FILE_PATH=/var/data/logs/astra.log
```

## Step 4: Database Setup

Render provides persistent disk. The `render.yaml` already configures:
- Disk mount: `/var/data`
- Database path: `/var/data/astra.db`
- Memory path: `/var/data/memory.json`

## Step 5: Frontend Deployment

Option A: Deploy frontend to Vercel/Netlify
Option B: Serve frontend from same backend (add static file serving)

For now, use the backend URL directly:
```
https://nova-backend.onrender.com
```

## Step 6: Google OAuth Setup (Optional)

1. Go to Google Cloud Console
2. Create OAuth 2.0 credentials
3. Add redirect URI: `https://your-domain.onrender.com/auth/google/callback`
4. Add credentials to Render environment variables

## Step 7: Test

1. Visit your Render URL
2. Test chat functionality
3. Test admin panel (first user becomes admin)
4. Test Google login (if configured)

## Free Tier Limits
- 750 hours/month (enough for 1 service)
- 512MB RAM
- Sleeps after 15 min inactivity (first request takes ~30s)

## Upgrading
- Render Starter: $7/month (no sleep, more RAM)
- Railway: $5/month credit
- Your own VPS: ~$5/month
