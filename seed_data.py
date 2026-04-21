"""
Database Seeder for the Online Auction System.
Creates sample users, items, auctions, and bids for testing.
"""
import os, sys
from datetime import datetime, timezone, timedelta
from app import create_app
from models import db, User, Item, Auction, Bid
from etl_pipeline import DataSimulator

def seed_database():
    """Seed the database with sample data."""
    app = create_app()
    with app.app_context():
        # Clear existing data
        Bid.query.delete()
        Auction.query.delete()
        Item.query.delete()
        User.query.delete()
        db.session.commit()

        print("Creating sample users...")
        users = []
        user_data = [
            ('admin', 'admin@auction.com', 'Admin User', 'admin123'),
            ('john_doe', 'john@email.com', 'John Doe', 'password123'),
            ('jane_smith', 'jane@email.com', 'Jane Smith', 'password123'),
            ('alice_wonder', 'alice@email.com', 'Alice Wonder', 'password123'),
            ('bob_builder', 'bob@email.com', 'Bob Builder', 'password123'),
            ('charlie_brown', 'charlie@email.com', 'Charlie Brown', 'password123'),
            ('diana_prince', 'diana@email.com', 'Diana Prince', 'password123'),
            ('edward_snow', 'edward@email.com', 'Edward Snow', 'password123'),
            ('fiona_green', 'fiona@email.com', 'Fiona Green', 'password123'),
            ('george_king', 'george@email.com', 'George King', 'password123'),
        ]
        for uname, email, fullname, pwd in user_data:
            u = User(username=uname, email=email, full_name=fullname)
            u.set_password(pwd)
            db.session.add(u)
            users.append(u)
        db.session.commit()

        print("Creating sample items and auctions...")
        now = datetime.now(timezone.utc)
        items_data = [
            ('Vintage Rolex Submariner', 'A classic 1960s Rolex Submariner watch in pristine condition.', 'Jewelry', 2500, 72, users[1]),
            ('Original Oil Painting - Sunset', 'Beautiful hand-painted oil on canvas depicting a Mediterranean sunset.', 'Art', 500, 48, users[2]),
            ('Rare Pokemon Card Collection', 'Complete first edition Base Set in near-mint condition.', 'Collectibles', 1000, 168, users[3]),
            ('Apple MacBook Pro M3 (Sealed)', 'Brand new, sealed MacBook Pro with M3 chip, 16GB RAM.', 'Electronics', 1800, 24, users[1]),
            ('Antique Victorian Writing Desk', 'Beautiful mahogany writing desk from the Victorian era, circa 1870.', 'Antiques', 800, 120, users[4]),
            ('Signed Michael Jordan Jersey', 'Authenticated signed Bulls #23 jersey from the 1996 season.', 'Sports', 3000, 96, users[5]),
            ('1967 Ford Mustang Fastback', 'Fully restored classic muscle car in Highland Green.', 'Vehicles', 45000, 168, users[6]),
            ('Diamond Engagement Ring', '1.5 carat princess cut diamond in platinum setting.', 'Jewelry', 4000, 48, users[2]),
            ('First Edition Harry Potter', 'First edition of "Harry Potter and the Philosopher\'s Stone" by J.K. Rowling.', 'Books', 1500, 72, users[7]),
            ('Sony PS5 Pro Bundle', 'PS5 Pro console with 2 controllers and 5 games.', 'Electronics', 600, 24, users[3]),
            ('Handmade Persian Rug', 'Authentic hand-knotted silk Persian rug, 8x10 feet.', 'Home & Garden', 2000, 96, users[8]),
            ('Gucci Bamboo Handbag', 'Vintage Gucci bamboo handle handbag in excellent condition.', 'Fashion', 1200, 48, users[9]),
        ]

        auctions = []
        for title, desc, cat, price, hours, seller in items_data:
            item = Item(title=title, description=desc, category=cat, seller_id=seller.id,
                       image_url='/static/images/default-item.jpg')
            db.session.add(item)
            db.session.flush()
            auction = Auction(item_id=item.id, starting_price=price, current_price=price,
                            start_time=now - timedelta(hours=2),
                            end_time=now + timedelta(hours=hours), status='active')
            db.session.add(auction)
            auctions.append(auction)
        db.session.commit()

        print("Creating sample bids...")
        import random
        random.seed(42)
        for auction in auctions[:8]:
            num_bids = random.randint(2, 6)
            current = auction.starting_price
            bidders = random.sample([u for u in users if u.id != auction.item.seller_id], min(num_bids, 8))
            for i, bidder in enumerate(bidders):
                increment = random.uniform(current * 0.02, current * 0.15)
                current = round(current + increment, 2)
                bid = Bid(auction_id=auction.id, bidder_id=bidder.id, amount=current,
                         timestamp=now - timedelta(hours=random.randint(0, 2),
                                                   minutes=random.randint(0, 59)))
                db.session.add(bid)
                auction.current_price = current
                auction.bid_count += 1
        db.session.commit()

        # Generate CSV/JSON data files for ETL
        print("Generating ETL data files...")
        simulator = DataSimulator()
        simulator.generate_all()

        total_users = User.query.count()
        total_items = Item.query.count()
        total_auctions = Auction.query.count()
        total_bids = Bid.query.count()
        print(f"\nDatabase seeded successfully!")
        print(f"  Users: {total_users}")
        print(f"  Items: {total_items}")
        print(f"  Auctions: {total_auctions}")
        print(f"  Bids: {total_bids}")

if __name__ == '__main__':
    seed_database()
