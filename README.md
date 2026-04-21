# 🔨 Online Auction System

A full-stack web-based auction platform with Data Engineering capabilities. Users can register, log in, list items for auction, and place bids in real-time. The system manages auction timing, bidding logic, data storage, and includes a complete ETL pipeline with analytics.

---

## 📸 Features

### 👤 User Module
- User Registration and Login (session-based authentication)
- User Dashboard: Active auctions, bid history, won/lost items

### 🛒 Seller Module
- Create auction listings with title, description, category, starting price, duration
- Upload item images
- View bids on listed items

### 💰 Bidding System
- Place bids on active auctions (validated: must be higher than current bid)
- Real-time price updates via AJAX polling
- Complete bid history tracking

### ⏱ Auction Logic
- Automatic auction closing at deadline
- Highest bidder wins automatically
- Bids prevented after auction ends

### 📊 Data Engineering
- **ETL Pipeline**: Extract from CSV/JSON → Transform (clean/validate) → Load to database
- **Analytics Dashboard**: Top bidders, most active auctions, revenue reports, category analysis
- **Data Simulation**: Generate large test datasets with realistic data

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Backend | Python Flask |
| Database | SQLite (dev) / PostgreSQL (prod-ready) |
| ORM | SQLAlchemy |
| Auth | Flask-Login + Werkzeug |
| Data Tools | Pandas, NumPy |

---

## 📦 Database Schema

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Users   │───→│  Items   │───→│ Auctions │←───│   Bids   │
├──────────┤    ├──────────┤    ├──────────┤    ├──────────┤
│ id       │    │ id       │    │ id       │    │ id       │
│ username │    │ title    │    │ item_id  │    │ auction_id│
│ email    │    │ desc     │    │ start_$  │    │ bidder_id│
│ password │    │ image    │    │ current_$│    │ amount   │
│ fullname │    │ category │    │ end_time │    │ timestamp│
│ phone    │    │ seller_id│    │ status   │    │ is_valid │
│ created  │    │ created  │    │ winner_id│    └──────────┘
└──────────┘    └──────────┘    └──────────┘
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- pip

### Steps

```bash
# 1. Navigate to project directory
cd "Online Auction System1"

# 2. Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database with sample data
python seed_data.py

# 5. Run the application
python app.py

# 6. Open in browser
# http://localhost:5000
```

### Demo Credentials
| Username | Password |
|----------|----------|
| admin | admin123 |
| john_doe | password123 |
| jane_smith | password123 |

---

## 📂 Project Structure

```
Online Auction System1/
├── app.py                  # Main Flask application (routes, API)
├── config.py               # Configuration settings
├── models.py               # SQLAlchemy database models
├── etl_pipeline.py         # ETL pipeline + Data simulator
├── analytics.py            # Pandas analytics module
├── seed_data.py            # Database seeder
├── requirements.txt        # Python dependencies
├── data/                   # CSV/JSON data files for ETL
│   ├── users.csv
│   ├── items.csv
│   └── bids.json
├── static/
│   ├── css/style.css       # Complete stylesheet
│   ├── js/app.js           # Frontend JavaScript
│   └── images/             # Uploaded images
├── templates/
│   ├── base.html           # Base layout template
│   ├── index.html          # Homepage
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # User dashboard
│   ├── auctions.html       # Browse auctions
│   ├── auction_detail.html # Auction detail + bidding
│   ├── create_auction.html # Create new auction
│   ├── analytics.html      # Analytics dashboard
│   └── etl.html            # ETL pipeline interface
└── README.md
```

---

## 🔄 ETL Pipeline

The system includes a complete ETL pipeline using Pandas:

1. **Extract**: Read data from `users.csv`, `items.csv`, and `bids.json`
2. **Transform**:
   - Remove duplicates
   - Validate email formats
   - Clean invalid bids (negative amounts, zero values)
   - Format timestamps
   - Standardize data
3. **Load**: Insert cleaned data into SQLite database tables

Run manually: `python etl_pipeline.py generate` then `python etl_pipeline.py run`

---

## 📊 Analytics

The analytics module generates reports on:
- **Top Bidders**: Most active bidders by bid count and total amount
- **Most Active Auctions**: Auctions with highest engagement
- **Revenue Report**: Total revenue from completed auctions
- **Category Analysis**: Performance breakdown by item category

---

## ⚙️ Unique Points

1. **Real-time bidding** with auto-refresh status updates
2. **Complete ETL pipeline** demonstrating Data Engineering concepts
3. **Glassmorphism UI** with dark theme and premium aesthetics
4. **Automatic auction closing** with winner determination
5. **Analytics dashboard** with visual bar charts
6. **Data simulation** for generating realistic test datasets
7. **Pandas-powered** data analysis and reporting

---

## 🔮 Future Improvements

- WebSocket integration for true real-time bidding
- Payment gateway integration (Stripe/PayPal)
- Email notifications for bid updates
- Image CDN for better performance
- Apache Spark integration for processing 1M+ rows
- Mobile-responsive PWA version
- Admin panel for platform management
- Recommendation engine based on bidding patterns

---

## 📄 License

This project is for educational purposes - Data Engineering Capstone Project.
