# AstroPulse — Personalized Astrology Telegram Bot

[![CI](https://github.com/r3lax3/astrobot/actions/workflows/ci.yml/badge.svg)](https://github.com/r3lax3/astrobot/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![aiogram 3](https://img.shields.io/badge/aiogram-3.x-2CA5E0)

A production Telegram bot that computes personalized astrological forecasts from the
user's natal chart and delivers them daily at a chosen time, respecting the user's
timezone and location. All calculations run locally on Swiss Ephemeris — no
third-party astrology APIs.

## Features

- **Personal daily forecast** — transit aspects to the natal chart (Swiss Ephemeris),
  interpretation texts plus a generated image with astrological data.
- **Lunar calendar** — lunar days, moon phases, moon sign, void-of-course moon periods.
- **Favorable day picker** and dream interpretation by lunar day.
- **Paid subscriptions** — Prodamus payments (HMAC-signed links, incoming webhook
  signature verification), promo codes, renewal reminders.
- **Admin panel** — broadcasts, statistics, general forecasts, card of the day,
  automatic database backups delivered to the admin chat.

## Tech Stack

| Layer | Technologies |
|---|---|
| Bot | Python 3.11, aiogram 3 (webhook mode), aiohttp |
| State | Redis (FSM storage) |
| Database | SQLite + SQLAlchemy 2 |
| Scheduling | APScheduler — per-user cron jobs in the user's timezone |
| Astro engine | pyswisseph (Swiss Ephemeris), ephem |
| Images | Pillow — forecast card generation |
| Quality | pytest, ruff, GitHub Actions |

## Architecture

```
main.py                  # app wiring: aiohttp server, webhooks, middleware
src/
├── astro_engine/        # pure astrological math (aspects, lunar days, phases, signs)
├── routers/
│   ├── user/            # user flows (forecasts, subscription, profile)
│   └── admin/           # admin panel (broadcasts, statistics, content)
├── payments/            # Prodamus: signed payment links, payment webhooks
├── scheduler.py         # daily deliveries and renewal reminders
├── image_processing/    # astro-data image generation
├── database/            # models, CRUD, backups
├── middlewares/         # keyboard cleanup, media groups, update filtering
└── keyboards/           # declarative keyboard definitions
data/                    # content: interpretations, dreams, day picker (CSV/JSON)
docs/architecture.drawio # project diagram
```

Component interaction diagram: [docs/architecture.drawio](docs/architecture.drawio)
(opens with [diagrams.net](https://app.diagrams.net)).

## Getting Started

Prerequisites: Python 3.11+, Redis, and an HTTPS domain for the Telegram webhook.

```bash
git clone https://github.com/r3lax3/astrobot.git && cd astrobot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                    # bot token
cp config.example.toml config.toml      # webhook, payments, admins
python main.py
```

## Tests and Linting

```bash
pip install -r requirements-dev.txt
cp config.example.toml config.toml
pytest        # unit tests: astro math, payment signatures, image generation
ruff check .  # linting
```

Astrological calculations are tested against reference values from astrological
almanacs (accurate to minutes). Integration tests that hit external services are
enabled with `RUN_INTEGRATION_TESTS=1`.
