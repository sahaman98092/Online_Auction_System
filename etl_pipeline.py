"""
ETL Pipeline for the Online Auction System
============================================
Implements Extract, Transform, Load operations using Pandas.

- Extract: Read auction and bid data from CSV/JSON files
- Transform: Clean invalid bids, format timestamps, validate data
- Load: Store processed data in structured database tables

Also includes data simulation for generating large datasets.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from models import db, User, Item, Auction, Bid


class ETLPipeline:
    """
    ETL Pipeline class that handles data extraction, transformation,
    and loading for the Online Auction System.
    """

    def __init__(self, app=None):
        """Initialize the ETL pipeline with Flask app context."""
        self.app = app
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.results = {
            'extracted': 0,
            'transformed': 0,
            'loaded': 0,
            'invalid_records': 0,
            'errors': []
        }

    # ============================================================
    # EXTRACT Phase
    # ============================================================

    def extract_users_csv(self):
        """Extract user data from CSV file."""
        filepath = os.path.join(self.data_dir, 'users.csv')
        if not os.path.exists(filepath):
            self.results['errors'].append('users.csv not found')
            return pd.DataFrame()

        try:
            df = pd.read_csv(filepath)
            self.results['extracted'] += len(df)
            print(f"[EXTRACT] Loaded {len(df)} users from CSV")
            return df
        except Exception as e:
            self.results['errors'].append(f'Error reading users.csv: {str(e)}')
            return pd.DataFrame()

    def extract_items_csv(self):
        """Extract item data from CSV file."""
        filepath = os.path.join(self.data_dir, 'items.csv')
        if not os.path.exists(filepath):
            self.results['errors'].append('items.csv not found')
            return pd.DataFrame()

        try:
            df = pd.read_csv(filepath)
            self.results['extracted'] += len(df)
            print(f"[EXTRACT] Loaded {len(df)} items from CSV")
            return df
        except Exception as e:
            self.results['errors'].append(f'Error reading items.csv: {str(e)}')
            return pd.DataFrame()

    def extract_bids_json(self):
        """Extract bid data from JSON file."""
        filepath = os.path.join(self.data_dir, 'bids.json')
        if not os.path.exists(filepath):
            self.results['errors'].append('bids.json not found')
            return pd.DataFrame()

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            self.results['extracted'] += len(df)
            print(f"[EXTRACT] Loaded {len(df)} bids from JSON")
            return df
        except Exception as e:
            self.results['errors'].append(f'Error reading bids.json: {str(e)}')
            return pd.DataFrame()

    # ============================================================
    # TRANSFORM Phase
    # ============================================================

    def transform_users(self, df):
        """
        Transform user data:
        - Remove duplicates
        - Validate email format
        - Clean whitespace
        - Standardize usernames
        """
        if df.empty:
            return df

        original_count = len(df)

        # Remove duplicates based on email
        df = df.drop_duplicates(subset=['email'], keep='first')

        # Clean whitespace
        for col in ['username', 'email', 'full_name']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Validate email format (basic check)
        if 'email' in df.columns:
            valid_mask = df['email'].str.contains('@', na=False)
            invalid_count = (~valid_mask).sum()
            self.results['invalid_records'] += invalid_count
            df = df[valid_mask]

        # Standardize usernames to lowercase
        if 'username' in df.columns:
            df['username'] = df['username'].str.lower()

        self.results['transformed'] += len(df)
        print(f"[TRANSFORM] Users: {original_count} -> {len(df)} "
              f"({original_count - len(df)} removed)")
        return df

    def transform_items(self, df):
        """
        Transform item data:
        - Clean descriptions
        - Validate starting prices
        - Handle missing values
        """
        if df.empty:
            return df

        original_count = len(df)

        # Remove items with no title
        if 'title' in df.columns:
            df = df.dropna(subset=['title'])
            df['title'] = df['title'].astype(str).str.strip()

        # Validate starting price
        if 'starting_price' in df.columns:
            df['starting_price'] = pd.to_numeric(df['starting_price'], errors='coerce')
            invalid_prices = df['starting_price'].isna() | (df['starting_price'] <= 0)
            self.results['invalid_records'] += invalid_prices.sum()
            df = df[~invalid_prices]

        # Fill missing descriptions
        if 'description' in df.columns:
            df['description'] = df['description'].fillna('No description provided.')

        # Fill missing categories
        if 'category' in df.columns:
            df['category'] = df['category'].fillna('General')

        self.results['transformed'] += len(df)
        print(f"[TRANSFORM] Items: {original_count} -> {len(df)} "
              f"({original_count - len(df)} removed)")
        return df

    def transform_bids(self, df):
        """
        Transform bid data:
        - Clean invalid bids (negative amounts, zero amounts)
        - Format timestamps
        - Validate bid amounts against auction prices
        - Mark invalid bids
        """
        if df.empty:
            return df

        original_count = len(df)

        # Convert amounts to numeric
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

        # Remove bids with invalid amounts
        if 'amount' in df.columns:
            invalid_amounts = df['amount'].isna() | (df['amount'] <= 0)
            self.results['invalid_records'] += invalid_amounts.sum()
            df = df[~invalid_amounts]

        # Format timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            invalid_times = df['timestamp'].isna()
            self.results['invalid_records'] += invalid_times.sum()
            df = df[~invalid_times]

        # Mark validity
        df['is_valid'] = True

        self.results['transformed'] += len(df)
        print(f"[TRANSFORM] Bids: {original_count} -> {len(df)} "
              f"({original_count - len(df)} removed)")
        return df

    # ============================================================
    # LOAD Phase
    # ============================================================

    def load_users(self, df):
        """Load transformed user data into the database."""
        if df.empty:
            return 0

        loaded = 0
        with self.app.app_context():
            for _, row in df.iterrows():
                # Skip if user already exists
                existing = User.query.filter_by(email=row.get('email', '')).first()
                if existing:
                    continue

                user = User(
                    username=row.get('username', ''),
                    email=row.get('email', ''),
                    full_name=row.get('full_name', ''),
                    phone=str(row.get('phone', ''))
                )
                user.set_password(row.get('password', 'default123'))
                db.session.add(user)
                loaded += 1

            db.session.commit()
        self.results['loaded'] += loaded
        print(f"[LOAD] Loaded {loaded} users into database")
        return loaded

    def load_items(self, df):
        """Load transformed item data into the database."""
        if df.empty:
            return 0

        loaded = 0
        with self.app.app_context():
            for _, row in df.iterrows():
                # Get seller (use first user if seller_id not specified)
                seller_id = row.get('seller_id', 1)
                seller = User.query.get(seller_id)
                if not seller:
                    seller = User.query.first()
                    if not seller:
                        continue

                item = Item(
                    title=row.get('title', ''),
                    description=row.get('description', ''),
                    category=row.get('category', 'General'),
                    seller_id=seller.id,
                    image_url=row.get('image_url', '/static/images/default-item.jpg')
                )
                db.session.add(item)
                db.session.flush()

                # Create auction for the item
                now = datetime.now(timezone.utc)
                duration = int(row.get('duration_hours', 48))
                auction = Auction(
                    item_id=item.id,
                    starting_price=float(row.get('starting_price', 10.0)),
                    current_price=float(row.get('starting_price', 10.0)),
                    start_time=now,
                    end_time=now + timedelta(hours=duration),
                    status='active'
                )
                db.session.add(auction)
                loaded += 1

            db.session.commit()
        self.results['loaded'] += loaded
        print(f"[LOAD] Loaded {loaded} items and auctions into database")
        return loaded

    def load_bids(self, df):
        """Load transformed bid data into the database."""
        if df.empty:
            return 0

        loaded = 0
        with self.app.app_context():
            for _, row in df.iterrows():
                auction_id = row.get('auction_id')
                bidder_id = row.get('bidder_id')

                auction = Auction.query.get(auction_id)
                bidder = User.query.get(bidder_id)

                if not auction or not bidder:
                    continue

                bid = Bid(
                    auction_id=auction_id,
                    bidder_id=bidder_id,
                    amount=float(row['amount']),
                    timestamp=row.get('timestamp', datetime.now(timezone.utc)),
                    is_valid=row.get('is_valid', True)
                )
                db.session.add(bid)

                # Update auction current price if this bid is highest
                if float(row['amount']) > auction.current_price:
                    auction.current_price = float(row['amount'])
                    auction.bid_count += 1

                loaded += 1

            db.session.commit()
        self.results['loaded'] += loaded
        print(f"[LOAD] Loaded {loaded} bids into database")
        return loaded

    # ============================================================
    # Run Full Pipeline
    # ============================================================

    def run_full_pipeline(self):
        """Execute the complete ETL pipeline."""
        print("=" * 60)
        print("  ONLINE AUCTION SYSTEM - ETL PIPELINE")
        print("=" * 60)

        # Phase 1: Extract
        print("\n--- PHASE 1: EXTRACT ---")
        users_df = self.extract_users_csv()
        items_df = self.extract_items_csv()
        bids_df = self.extract_bids_json()

        # Phase 2: Transform
        print("\n--- PHASE 2: TRANSFORM ---")
        users_df = self.transform_users(users_df)
        items_df = self.transform_items(items_df)
        bids_df = self.transform_bids(bids_df)

        # Phase 3: Load
        print("\n--- PHASE 3: LOAD ---")
        self.load_users(users_df)
        self.load_items(items_df)
        self.load_bids(bids_df)

        print("\n" + "=" * 60)
        print(f"  ETL PIPELINE COMPLETE")
        print(f"  Extracted: {self.results['extracted']} records")
        print(f"  Transformed: {self.results['transformed']} records")
        print(f"  Loaded: {self.results['loaded']} records")
        print(f"  Invalid: {self.results['invalid_records']} records")
        print("=" * 60)

        return self.results

    def load_from_csv(self):
        """Quick load from CSV files (extract + transform + load)."""
        return self.run_full_pipeline()


# ============================================================
# Data Simulator - Generate Large Datasets
# ============================================================

class DataSimulator:
    """
    Generates simulated auction data for testing purposes.
    Can create datasets with up to 1M rows.
    """

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)

    def generate_users(self, count=50):
        """Generate sample user data and save to CSV."""
        np.random.seed(42)

        first_names = ['James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer',
                       'Michael', 'Linda', 'David', 'Elizabeth', 'William', 'Barbara',
                       'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah',
                       'Christopher', 'Karen', 'Arjun', 'Priya', 'Rahul', 'Ananya',
                       'Vikram', 'Sneha', 'Arun', 'Divya', 'Karthik', 'Meera']

        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
                      'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Sharma', 'Patel',
                      'Kumar', 'Singh', 'Gupta', 'Verma', 'Joshi', 'Rao', 'Mishra',
                      'Reddy']

        users = []
        for i in range(count):
            first = np.random.choice(first_names)
            last = np.random.choice(last_names)
            username = f"{first.lower()}{last.lower()}{np.random.randint(1, 999)}"
            users.append({
                'username': username,
                'email': f"{username}@email.com",
                'password': 'password123',
                'full_name': f"{first} {last}",
                'phone': f"+1{np.random.randint(200000000, 999999999)}0"
            })

        df = pd.DataFrame(users)
        df.to_csv(os.path.join(self.data_dir, 'users.csv'), index=False)
        print(f"Generated {count} users -> users.csv")
        return df

    def generate_items(self, count=30, num_sellers=10):
        """Generate sample item data and save to CSV."""
        np.random.seed(42)

        categories = ['Electronics', 'Art', 'Jewelry', 'Vehicles', 'Collectibles',
                      'Fashion', 'Home & Garden', 'Sports', 'Books', 'Antiques']

        item_prefixes = {
            'Electronics': ['Vintage', 'Rare', 'Limited Edition', 'Professional'],
            'Art': ['Original', 'Signed', 'Abstract', 'Contemporary'],
            'Jewelry': ['14K Gold', 'Diamond', 'Vintage', 'Handcrafted'],
            'Vehicles': ['Classic', 'Restored', 'Vintage', 'Custom'],
            'Collectibles': ['Rare', 'First Edition', 'Limited', 'Mint Condition'],
            'Fashion': ['Designer', 'Vintage', 'Limited Edition', 'Luxury'],
            'Home & Garden': ['Antique', 'Handmade', 'Vintage', 'Artisan'],
            'Sports': ['Signed', 'Game-Used', 'Vintage', 'Championship'],
            'Books': ['First Edition', 'Signed', 'Rare', 'Antique'],
            'Antiques': ['19th Century', 'Victorian', 'Art Deco', 'Colonial']
        }

        item_names = {
            'Electronics': ['Camera', 'Watch', 'Radio', 'Synthesizer', 'Turntable'],
            'Art': ['Painting', 'Sculpture', 'Print', 'Photograph', 'Drawing'],
            'Jewelry': ['Ring', 'Necklace', 'Bracelet', 'Earrings', 'Brooch'],
            'Vehicles': ['Mustang', 'Corvette', 'Motorcycle', 'Beetle', 'Porsche'],
            'Collectibles': ['Coin Set', 'Stamp Collection', 'Action Figure', 'Card', 'Medal'],
            'Fashion': ['Handbag', 'Coat', 'Shoes', 'Watch', 'Sunglasses'],
            'Home & Garden': ['Vase', 'Clock', 'Lamp', 'Chair', 'Rug'],
            'Sports': ['Jersey', 'Baseball', 'Trophy', 'Helmet', 'Gloves'],
            'Books': ['Novel', 'Atlas', 'Encyclopedia', 'Manuscript', 'Comic'],
            'Antiques': ['Clock', 'Furniture', 'Porcelain', 'Silver', 'Map']
        }

        items = []
        for i in range(count):
            category = np.random.choice(categories)
            prefix = np.random.choice(item_prefixes[category])
            name = np.random.choice(item_names[category])
            title = f"{prefix} {name}"

            items.append({
                'title': title,
                'description': f"A beautiful {prefix.lower()} {name.lower()} in excellent condition. "
                              f"Category: {category}. Perfect for collectors and enthusiasts.",
                'category': category,
                'starting_price': round(np.random.uniform(10, 5000), 2),
                'seller_id': np.random.randint(1, num_sellers + 1),
                'duration_hours': np.random.choice([6, 12, 24, 48, 72, 168]),
                'image_url': '/static/images/default-item.jpg'
            })

        df = pd.DataFrame(items)
        df.to_csv(os.path.join(self.data_dir, 'items.csv'), index=False)
        print(f"Generated {count} items -> items.csv")
        return df

    def generate_bids(self, count=100, num_auctions=30, num_bidders=50):
        """Generate sample bid data and save to JSON."""
        np.random.seed(42)

        bids = []
        for i in range(count):
            auction_id = np.random.randint(1, num_auctions + 1)
            bidder_id = np.random.randint(1, num_bidders + 1)

            # Generate realistic bid amounts
            base_price = np.random.uniform(10, 5000)
            bid_increment = np.random.uniform(1, base_price * 0.2)
            amount = round(base_price + bid_increment, 2)

            # Generate timestamp within the last 30 days
            days_ago = np.random.randint(0, 30)
            hours_ago = np.random.randint(0, 24)
            timestamp = (datetime.now(timezone.utc) -
                        timedelta(days=days_ago, hours=hours_ago))

            bids.append({
                'auction_id': int(auction_id),
                'bidder_id': int(bidder_id),
                'amount': amount,
                'timestamp': timestamp.isoformat(),
                'is_valid': True
            })

        # Add some intentionally invalid bids for ETL testing
        invalid_bids = [
            {'auction_id': 1, 'bidder_id': 1, 'amount': -50, 'timestamp': 'invalid', 'is_valid': False},
            {'auction_id': 2, 'bidder_id': 2, 'amount': 0, 'timestamp': '2024-01-01T00:00:00', 'is_valid': False},
            {'auction_id': 999, 'bidder_id': 999, 'amount': None, 'timestamp': None, 'is_valid': False},
        ]
        bids.extend(invalid_bids)

        with open(os.path.join(self.data_dir, 'bids.json'), 'w') as f:
            json.dump(bids, f, indent=2, default=str)

        print(f"Generated {len(bids)} bids -> bids.json")
        return pd.DataFrame(bids)

    def generate_all(self, user_count=50, item_count=30, bid_count=100):
        """Generate all sample data files."""
        print("=" * 50)
        print("  GENERATING SAMPLE DATA")
        print("=" * 50)
        self.generate_users(user_count)
        self.generate_items(item_count, num_sellers=min(10, user_count))
        self.generate_bids(bid_count, num_auctions=item_count, num_bidders=user_count)
        print("=" * 50)
        print("  DATA GENERATION COMPLETE")
        print("=" * 50)


# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'generate':
        # Generate sample data
        simulator = DataSimulator()
        simulator.generate_all()
    elif len(sys.argv) > 1 and sys.argv[1] == 'run':
        # Run ETL pipeline
        from app import create_app
        app = create_app()
        with app.app_context():
            pipeline = ETLPipeline(app)
            pipeline.run_full_pipeline()
    else:
        print("Usage:")
        print("  python etl_pipeline.py generate  - Generate sample data files")
        print("  python etl_pipeline.py run        - Run ETL pipeline")
