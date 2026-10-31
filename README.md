# ShopThread 🧵

> **Turn Instagram DMs into orders — automatically.**

ShopThread is an AI-powered commerce layer for Instagram. Vendors connect their Instagram Business account and ShopThread's AI agent handles customer DMs end-to-end: understands what they want, collects size/variant and address, creates the order, and sends a UPI payment link — all without the vendor lifting a finger.

🔗 **Live Demo:** https://shopthread-omega.vercel.app  
🤖 **Simulator:** https://shopthread-omega.vercel.app/simulator  
�� **Dashboard:** https://shopthread-omega.vercel.app/dashboard

---

## The Problem

Small Indian businesses sell on Instagram but manage orders manually — screenshot DMs, ask for address, send UPI link, track in a notebook. It's chaotic, slow, and doesn't scale.

## The Solution

ShopThread sits between Instagram and the vendor. When a customer DMs "do you have this in size M?", the AI:
1. Identifies the product they want
2. Confirms variant availability
3. Collects delivery address
4. Creates the order
5. Sends a UPI payment link in the same DM thread

The vendor sees all orders on a live dashboard. No manual work.

---

## Architecture

Instagram DM
│
▼
Meta Webhook ──► FastAPI (Cloud Run)
│
┌───────┴────────┐
│ order_weave │ ← AI agent (Meta Llama)
│ (intent → │ classifies intent,
│ reply gen) │ stages conversation
└───────┬────────┘
│
┌───────┴────────┐
│ Supabase │ ← vendors, products,
│ (Postgres) │ orders, conversations
└────────────────┘
│
▼
Next.js Dashboard (Vercel)

**Stack:**
- **Frontend:** Next.js 14, TailwindCSS → Vercel
- **Backend:** FastAPI (Python) → Google Cloud Run
- **Database:** Supabase (Postgres)
- **AI:** Meta Llama via muse-spark-1.3 — intent classification + reply generation
- **Payments:** UPI deep links (no payment gateway needed)
- **Instagram:** Meta Webhooks + Instagram Graph API

---

## How to Test (Judges)

> ⚠️ **Note:** This is a hackathon demo build. Instagram Business API requires Meta app review for production. The simulator below bypasses that — no Instagram account needed.

### Option 1 — Quick Test (Recommended)

1. Go to **https://shopthread-omega.vercel.app/simulator**
2. Pick any vendor from the dropdown (e.g. "Demo Vendor")
3. Type a message like: *"Do you have a test product?"*
4. The AI will ask for size, then address, then confirm and send a UPI payment link
5. Open **https://shopthread-omega.vercel.app/dashboard** in another tab — watch the order appear in real time

### Option 2 — Full Vendor Flow

1. Sign up at **https://shopthread-omega.vercel.app/signup**
2. Add a product on the dashboard
3. Open the simulator, pick your vendor
4. Run a conversation — your products will show up in the AI's responses

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account
- Google Cloud account (for Cloud Run)

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in Supabase URL, keys, Meta tokens
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local   # fill in NEXT_PUBLIC_API_URL
npm run dev
```

---

## Key Files
backend/
├── app/
│ ├── routers/webhook.py # Meta webhook + simulate-dm endpoint
│ ├── agents/order_weave.py # AI agent — intent → order → UPI
│ └── main.py
frontend/
├── app/
│ ├── simulator/page.tsx # DM simulator for judges
│ ├── dashboard/page.tsx # Vendor order dashboard
│ └── onboarding/page.tsx # Post-signup onboarding


---

## What's Next

- **Meta App Review** — get production Instagram DM access approved
- **Payment confirmation** — webhook from UPI apps to mark orders paid
- **Multi-product catalog** — vendor product management UI
- **Analytics** — conversion rates, response times, revenue per vendor
- **WhatsApp support** — same agent, different channel

---

## Built for

**Hackathon 2026**  
By **Remya C** — [@remyacode](https://github.com/remyacode)
