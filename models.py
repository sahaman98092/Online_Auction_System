"""
Database Models for the Online Auction System.
Defines the schema for Users, Items, Auctions, and Bids tables.
Uses SQLAlchemy ORM for database abstraction.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User model - stores registered user information.
    Supports both buyers and sellers.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    items = db.relationship('Item', backref='seller', lazy='dynamic')
    bids = db.relationship('Bid', backref='bidder', lazy='dynamic')
    won_auctions = db.relationship('Auction', backref='winner',
                                   foreign_keys='Auction.winner_id', lazy='dynamic')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Item(db.Model):
    """
    Item model - stores details of items listed for auction.
    Each item belongs to a seller (User).
    """
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    auctions = db.relationship('Auction', backref='item', lazy='dynamic')

    def __repr__(self):
        return f'<Item {self.title}>'


class Auction(db.Model):
    """
    Auction model - manages auction sessions for items.
    Tracks pricing, timing, and auction status.
    """
    __tablename__ = 'auctions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    starting_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, ended, cancelled
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    bid_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    bids = db.relationship('Bid', backref='auction', lazy='dynamic',
                           order_by='Bid.amount.desc()')

    @property
    def is_active(self):
        """Check if the auction is currently active."""
        from datetime import datetime
        now = datetime.utcnow()
        return self.status == 'active' and self.end_time > now

    @property
    def time_remaining(self):
        """Calculate remaining time for the auction."""
        from datetime import datetime
        now = datetime.utcnow()
        if self.end_time > now:
            return self.end_time - now
        return None

    def __repr__(self):
        return f'<Auction {self.id} for Item {self.item_id}>'


class Bid(db.Model):
    """
    Bid model - stores individual bids placed on auctions.
    Each bid is linked to an auction and a bidder (User).
    """
    __tablename__ = 'bids'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_valid = db.Column(db.Boolean, default=True)  # Used in ETL pipeline for validation

    def __repr__(self):
        return f'<Bid ${self.amount} on Auction {self.auction_id}>'
