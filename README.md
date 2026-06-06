# FoodBridge

FoodBridge is a comprehensive food waste reduction web app that connects food donors (restaurants, households, catering) with claimants (NGOs, volunteers, food banks). The platform facilitates the listing of surplus food and allows claimants to easily browse and claim these resources before they expire.

## Features
- **Role-based Dashboards:** Dedicated views for Donors, Claimants, and Administrators.
- **Real-time Listings:** Browse active listings with filters and urgency color coding.
- **Impact Tracking:** Automatically calculates KG of food rescued, CO2 emissions prevented, and equivalent meals enabled.
- **Secure Authentication:** Using Flask-Login and Bcrypt.
- **Atomic Operations:** Ensuring no double-claiming using database-level locks.

## Tech Stack
- Python 3.11, Flask, SQLite (SQLAlchemy)
- Flask-WTF, Flask-Login, Flask-Bcrypt
- Vanilla CSS with custom properties & responsive grid
- Vanilla JavaScript for client-side interactivity

## Setup Instructions

1. **Clone & Virtual Environment:**
   ```bash
   cd FoodBridge
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

4. **Initialize Database with Seed Data:**
   ```bash
   flask seed-db
   ```

5. **Run the Application:**
   ```bash
   flask run
   ```
   Access at `http://127.0.0.1:5000`

## Demo Credentials
| Role | Email | Password |
|---|---|---|
| Admin | admin@foodbridge.com | admin123 |
| Donor | donor1@test.com | password123 |
| Claimant | claimant1@test.com | password123 |

## CS50 Video link
[Insert video link here]

## Future Roadmap
- Migration to PostgreSQL
- Redis for caching & background jobs
- Dockerization
- Native Mobile App (React Native)
