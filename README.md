<div align="center">
  <h1>🥗 FoodBridge</h1>
  <p><em>Bridging the gap between surplus food and communities in need.</em></p>
  
  [![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
  [![Flask](https://img.shields.io/badge/Flask-3.0.3-lightgrey.svg)](https://flask.palletsprojects.com/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
  [![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
</div>

<br />

## 📖 Overview

**FoodBridge** is a comprehensive, production-grade web application built to combat food waste. It serves as a dynamic marketplace connecting **Food Donors** (restaurants, catering services, households) with **Claimants** (NGOs, food banks, community volunteers). 

By providing real-time listings, urgency tracking, and atomic claiming mechanisms, FoodBridge ensures that surplus food reaches those who need it before it expires, while actively tracking the environmental and social impact of every rescue.

This project was developed as the final project for Harvard's **CS50x**.

[**🎥 Watch the Demo Video Here**](#) *(CS50 Video Link Placeholder)*

---

## ✨ Key Features

- **Role-Based Access Control (RBAC):** Dedicated, secure dashboards for Donors, Claimants, and System Administrators.
- **Real-Time Food Marketplace:** Browse active surplus listings with live countdown timers, urgency color-coding (Critical, Urgent, Normal), and keyword/category filtering.
- **Atomic Transactions:** Database-level locking prevents race conditions, ensuring a listing cannot be double-claimed.
- **Impact Tracking System:** Automatically calculates and visualizes KG of food rescued, CO₂ emissions prevented, and equivalent meals enabled.
- **Modern UI/UX:** Built from scratch with a custom Vanilla CSS design system featuring glassmorphism, fluid typography, and responsive grid layouts.

---

## 🛠️ Technology Stack

| Category | Technologies Used |
|----------|-------------------|
| **Backend** | Python 3.11, Flask, Flask-Login, Flask-Bcrypt, Flask-WTF |
| **Database** | SQLite3, SQLAlchemy ORM |
| **Frontend** | Jinja2, Vanilla HTML5/CSS3, Vanilla JavaScript (ES6) |
| **Security** | CSRF Protection, Bcrypt Password Hashing, Env Vars |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Git

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kartikeyagrawal2007/FoodBridge.git
   cd FoodBridge
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Copy the example environment file and update it if necessary:
   ```bash
   cp .env.example .env
   ```

5. **Initialize and Seed the Database:**
   FoodBridge comes with a custom CLI command to instantly populate the database with test users and sample food listings:
   ```bash
   flask seed-db
   ```

6. **Run the Application:**
   ```bash
   flask run -p 5002
   ```
   Navigate to `http://127.0.0.1:5002` in your browser.

---

## 🔐 Demo Credentials

Use these pre-configured accounts to explore the different role perspectives:

| Role | Email | Password | Capabilities |
|---|---|---|---|
| **Admin** | `admin@foodbridge.com` | `admin123` | View all users, listings, platform stats |
| **Donor** | `donor1@test.com` | `password123` | Create listings, confirm pickups, track impact |
| **Claimant** | `claimant1@test.com` | `password123` | Browse, filter, claim food, view claim history |

---

## 🗺️ Future Roadmap

While fully functional, FoodBridge is designed to scale. Planned future enhancements include:
- [ ] **Database Migration:** Transition from SQLite to PostgreSQL for production scaling.
- [ ] **Background Jobs:** Integrate Celery + Redis for automated email notifications and expiry pruning.
- [ ] **Geocoding API:** Add Google Maps integration for distance-based sorting and routing.
- [ ] **Containerization:** Full Docker support (`Dockerfile` & `docker-compose.yml`).

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## ✍️ Author

**Kartikey Agrawal** 
- GitHub: [@kartikeyagrawal2007](https://github.com/kartikeyagrawal2007)
- Developed for Harvard University's CS50x.
