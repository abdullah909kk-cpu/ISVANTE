# ISVANTE — Luxury Horology Pakistan

> **CRAFTED TO STAND OUT**  
> Pakistan's Premier Luxury Watch Brand E-Commerce Platform

---

## 🏛️ Brand & Architecture Overview

**ISVANTE** is a high-end luxury watch brand launched specifically for the Pakistani market. The platform is architected to project opulence, prestige, and institutional trust—giving Pakistani customers total confidence to place orders via **Cash on Delivery (COD)** or digital payment.

### Key Highlights
- **Official Brand Identity**: Employs the official ISVANTE gold-embossed monogram and wordmark emblem (`isvante_logo_circle.png`), maintaining 100% original proportions and aesthetic dignity.
- **Pakistan-Centric Operations**:
  - Currency: Pakistani Rupees (**PKR / Rs.**).
  - Primary Payment: **Cash on Delivery (COD)** with door-to-door courier verification.
  - Delivery: 2–4 business days across Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Peshawar, Multan, Quetta, and nationwide via Trax Logistics & TCS.
  - Configurable nationwide shipping rate (Rs. 250) and free delivery threshold (Rs. 5,000+).
- **Centralized WhatsApp Business Deep-Linking**:
  - One central setting in `.env` and Database controls every touchpoint.
  - Floating WhatsApp concierge button with online pulse.
  - Product-level *"Chat on WhatsApp"* button with pre-filled watch title and price.
  - Post-checkout order verification button.
- **AI Horology Concierge**:
  - Floating chat assistant grounded in live catalog data, specs, prices, and store policies.
  - Zero-key intelligent local fallback engine included out of the box.
  - Plug-and-play AI provider integration via `AI_API_KEY` (Google Gemini or OpenAI). No keys are ever exposed to the client.
- **Full Atelier Admin Command Center**:
  - Protected administrative dashboard at `/admin`.
  - Product catalog CRUD with image upload.
  - Order pipeline management (Pending → Confirmed → Processing → Shipped → Delivered → Cancelled).
  - Courier assigner (Trax/TCS tracking number updates).
  - Promotional coupon creation (percentage or fixed PKR discounts).
  - Live store settings updater.

---

## 🚀 1. How to Run Locally

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Pip

### Quick Start (3 Steps)
1. **Clone or Navigate to the Directory**:
   ```bash
   cd "c:\Users\Hp\Desktop\My Web"
   ```

2. **Install Required Packages**:
   ```bash
   python -m pip install flask pillow
   ```

3. **Launch the ISVANTE Server**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to:
   - **Storefront**: `http://localhost:5000`
   - **Admin Command Center**: `http://localhost:5000/admin`

---

## 🔐 2. Admin Credentials

- **URL**: `http://localhost:5000/admin`
- **Username**: `admin`
- **Password**: `isvantepakistan`

*(You can update this password at any time in the `admins` table in `isvante.db`).*

---

## ⌚ 3. How to Add and Manage Products

You have two simple ways to add timepieces:

### Method A: Via Admin Dashboard (No Coding Required)
1. Go to `http://localhost:5000/admin` and log in.
2. Click the **Products** tab.
3. Click the golden **+ Add New Timepiece** button.
4. Fill in the watch specifications:
   - Model Name (e.g. *ISVANTE Imperial Rose*)
   - Price in PKR (e.g. `28000`) and Compare Price (e.g. `34000`)
   - Inventory Stock Count
   - Collection (Chronograph, Luxury, Classic, Minimal, Everyday, New Arrivals)
   - Caliber / Movement (e.g. *Japanese Seiko NH35A Automatic*)
   - Case Material (e.g. *316L Surgical Stainless Steel*)
   - Strap Material (e.g. *Genuine Italian Calfskin Leather*)
   - Water Resistance (e.g. *5 ATM / 50M*)
   - Upload a product photograph or enter an image URL.
   - Toggle *Featured*, *Best Seller*, or *New Arrival*.
5. Click **Publish Timepiece**. It immediately appears in the store, shop filters, and AI concierge memory!

### Method B: Via Python / Database
Add products directly into `database.py` in the `products` seed list or execute SQL queries against `isvante.db`.

---

## 📲 4. How to Configure the WhatsApp Number

The WhatsApp number is centralized and can be changed in **two easy ways**:

### Option 1: Through Admin Dashboard
1. Go to `/admin` -> **Settings** tab.
2. Under **Central WhatsApp Number**, type your business WhatsApp number in international Pakistani format:
   ```text
   +923001234567
   ```
3. Click **Save Store Settings**. All floating buttons, product page links, and checkout confirmation buttons update immediately!

### Option 2: Through `.env` File
Open the `.env` file in the root folder and edit:
```env
WHATSAPP_NUMBER=+923001234567
CONTACT_PHONE=+92 300 1234567
```

---

## 🤖 5. How to Connect the AI Chatbot

The AI Concierge has a dual-architecture:

1. **Default Mode (Zero Setup Needed)**:
   - The chatbot uses a built-in semantic matching engine that searches your real product catalog (`isvante.db`), prices, movements, materials, COD policy, warranty, and Pakistan delivery times.
   - It answers customers accurately without costing a single rupee in API credits.

2. **Live AI Mode (Gemini or OpenAI)**:
   - Obtain a Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/) or an OpenAI API key.
   - Open your `.env` file:
     ```env
     AI_PROVIDER=gemini
     AI_API_KEY=AIzaSyYourSecretKeyHere
     ```
   - Restart the server. The concierge will now leverage live conversational intelligence grounded in your dynamic watch catalog!
   - **Security**: The API key is stored server-side only in `.env` and never transmitted to the browser client.

---

## 🗄️ 6. How to Connect the Database

Currently, the application runs on **SQLite** (`isvante.db`), which requires zero setup, is fast, and stores all real products, orders, reviews, coupons, and settings locally.

### Upgrading to PostgreSQL or MySQL for Scale
The data access layer in `database.py` uses standard ANSI SQL queries. To connect PostgreSQL (e.g. on Supabase, AWS RDS, or Render):
1. Install psycopg2: `pip install psycopg2-binary`
2. Update the `get_db()` connection function in `database.py` with your `DATABASE_URL`:
   ```python
   import psycopg2
   from psycopg2.extras import RealDictCursor
   def get_db():
       return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
   ```

---

## 💳 7. How to Connect Pakistani Payment Gateways

The application is architected for seamless payment gateway integration:

### 1. Cash on Delivery (COD) — *Currently Active*
- COD is the #1 preferred payment method in Pakistan and is fully active.
- Orders place directly into the database with `payment_method = 'cod'` and `payment_status = 'pending'`.
- Deducts inventory, notifies the admin, and issues an order confirmation number (e.g. `ISV-94821`).

### 2. Safepay Pakistan (Debit/Credit Cards)
- Safepay is Pakistan's leading checkout gateway supporting Visa, Mastercard, and UnionPay.
- To activate:
  1. Register at [Safepay Merchant](https://www.getsafepay.com/).
  2. Add your keys to `.env`:
     ```env
     SAFEPAY_API_KEY=sec_live_...
     SAFEPAY_SECRET_KEY=...
     ```
  3. In `templates/checkout.html`, the online option can invoke the Safepay Checkout button script.

### 3. JazzCash & Easypaisa Merchant Integration
- Credentials placeholders are already declared in `config.py` and `.env`:
  ```env
  JAZZCASH_MERCHANT_ID=
  JAZZCASH_PASSWORD=
  EASYPAISA_STORE_ID=
  ```
- Direct bank transfer / Raast instructions are also pre-configured in the checkout drawer for instant manual receipt upload!

---

## 📦 8. Pakistani Courier & Tracking Integration

ISVANTE is structured for the top Pakistani couriers:
- **Trax Logistics**
- **TCS Express**
- **Leopard Courier**
- **PostEx**
- **CallCourier**

### Admin Workflow
1. When a customer orders, their order appears under `/admin` as **Pending**.
2. Pack the watch into the luxury ISVANTE presentation box with the stamped warranty card.
3. Book the parcel on your courier portal (e.g. Trax or TCS) to generate a Consignment Note (CN #).
4. In the ISVANTE Admin Panel, open the order, change status to **Shipped**, and paste the CN # (e.g. `TRX-948201`).
5. The customer can visit `http://localhost:5000/track` at any time, enter their Order Number and phone number, and see their real-time parcel journey!

---

## 🌐 9. How to Deploy Online

### Option A: Render (Free & Fast)
1. Create a `requirements.txt`:
   ```text
   flask==3.1.3
   pillow==12.3.0
   gunicorn==22.0.0
   ```
2. Create a `Procfile`:
   ```text
   web: gunicorn app:app
   ```
3. Push to GitHub and connect repository to [Render.com](https://render.com).
4. Set Environment Variables in Render dashboard matching `.env`.

### Option B: VPS (DigitalOcean / AWS / Linode / Hostinger)
1. Run Ubuntu 22.04 LTS.
2. Install Python 3, Nginx, and systemd.
3. Configure Gunicorn as a systemd service.
4. Point your domain (e.g. `isvante.pk`) to the server IP and install free SSL via Certbot:
   ```bash
   sudo certbot --nginx -d isvante.pk -d www.isvante.pk
   ```

---

## ⚙️ 10. Required Environment Variables Summary

| Variable | Description | Example / Default |
|---|---|---|
| `SECRET_KEY` | Flask session encryption key | `isvante-production-master-secret-pk-2026` |
| `DATABASE_PATH` | Local SQLite database file | `isvante.db` |
| `WHATSAPP_NUMBER` | Central Pakistan WhatsApp business phone | `+923001234567` |
| `CONTACT_PHONE` | Customer service voice line | `+92 300 1234567` |
| `CONTACT_EMAIL` | Concierge email address | `concierge@isvante.com` |
| `SHIPPING_FEE` | Standard courier fee in PKR | `250` |
| `FREE_SHIPPING_THRESHOLD` | Free delivery threshold in PKR | `5000` |
| `AI_PROVIDER` | AI Chatbot backend (`gemini` or `openai`) | `gemini` |
| `AI_API_KEY` | API Key for live AI responses (optional) | *(Leave empty for built-in catalog engine)* |

---

## 🛠️ 11. Checklist of What You Need to Configure Yourself

Before public advertising across Pakistan:
- [ ] **Change the WhatsApp Number**: Update to your real business WhatsApp in `/admin` Settings or `.env`.
- [ ] **Add Your Contact Phone & Email**: Update contact details in `/admin` Settings.
- [ ] **Adjust Watch Prices / Inventory**: Edit watch prices and stock in the Admin Products tab.
- [ ] **Update Social Media Links**: Add your real Instagram handle (`@isvante.pk`), Facebook page, and TikTok in `/admin` Settings.
- [ ] **(Optional) Add AI API Key**: If you wish to use Google Gemini live reasoning, paste your key into `.env`.
- [ ] **Change Admin Password**: In the database `admins` table.

---

*ISVANTE Horology — Crafted to Stand Out. Designed and engineered for Pakistan.*
