# HVAC Pro SaaS Platform

A complete HVAC company management SaaS with AI chatbot, lead capture, SMS automation, and ROI tracking.

## Tech Stack

- **Next.js 16** (App Router) + TypeScript
- **Tailwind CSS v4**
- **Prisma** + PostgreSQL
- **NextAuth v5** (Credentials provider)
- **Anthropic Claude** (AI chatbot and SMS assistant)
- **Twilio** (SMS webhooks for missed call recovery)

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `NEXTAUTH_SECRET` - Generate with `openssl rand -base64 32`
- `NEXTAUTH_URL` - Your app URL (e.g., `http://localhost:3000`)
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com
- `TWILIO_ACCOUNT_SID` - From Twilio console
- `TWILIO_AUTH_TOKEN` - From Twilio console
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number
- `SUPER_ADMIN_EMAIL` - Initial admin email
- `SUPER_ADMIN_PASSWORD` - Initial admin password

### 3. Set up the database

```bash
npx prisma db push
```

### 4. Seed with demo data

```bash
npm run seed
```

### 5. Run the development server

```bash
npm run dev
```

## URLs

- **Landing page**: `http://localhost:3000/cool-air-pros` (demo company)
- **Admin login**: `http://localhost:3000/login`
- **Dashboard**: `http://localhost:3000/dashboard`

## Demo Credentials

After running the seed:
- **Super Admin**: `admin@hvacpro.com` / `admin123`
- **Company Admin**: `owner@coolairpros.com` / `company123`

## Features

- **Public landing pages** per HVAC company (`/[slug]`)
- **AI chatbot** powered by Claude for lead qualification
- **Lead capture form** with urgency classification
- **CRM dashboard** with lead management
- **Appointments calendar** view
- **ROI reporting** dashboard
- **SMS automation** via Twilio webhooks (missed call recovery)
- **Multi-company** support (SUPER_ADMIN manages all companies)

## Twilio SMS Setup

Configure your Twilio phone number webhook to point to:

```
https://your-domain.com/api/sms/webhook
```

This enables automatic SMS responses when customers call after hours.
