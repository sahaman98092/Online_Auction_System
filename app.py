"""
Online Auction System - Main Flask Application
================================================
A full-stack auction platform with user authentication, real-time bidding,
auction management, ETL pipeline, and analytics dashboard.

Author: Online Auction System Team
"""

import os
from datetime import datetime, timezone, timedelta
from functools import wraps

def utcnow():
    """Get current UTC time as naive datetime (for SQLite compatibility)."""
    return datetime.utcnow()

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, session)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename

from config import config
from models import db, User, Item, Auction, Bid

# ============================================================
# Application Factory
# ============================================================

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        return User.query.get(int(user_id))

    # Create database tables
    with app.app_context():
        db.create_all()
        # Create upload directory if it doesn't exist
        os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/images/uploads'), exist_ok=True)

    # ============================================================
    # Helper Functions
    # ============================================================

    def allowed_file(filename):
        """Check if the uploaded file has an allowed extension."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS', set())

    def check_and_close_auctions():
        """Auto-close expired auctions and determine winners."""
        now = utcnow()
        expired_auctions = Auction.query.filter(
            Auction.status == 'active',
            Auction.end_time <= now
        ).all()

        for auction in expired_auctions:
            auction.status = 'ended'
            # Find the highest valid bid
            highest_bid = Bid.query.filter_by(
                auction_id=auction.id, is_valid=True
            ).order_by(Bid.amount.desc()).first()

            if highest_bid:
                auction.winner_id = highest_bid.bidder_id
                auction.current_price = highest_bid.amount

        if expired_auctions:
            db.session.commit()

    # ============================================================
    # Routes - Authentication
    # ============================================================

    @app.route('/')
    def index():
        """Homepage - displays featured auctions and platform overview."""
        check_and_close_auctions()
        # Get active auctions for the homepage
        active_auctions = Auction.query.filter_by(status='active').order_by(
            Auction.end_time.asc()
        ).limit(6).all()
        # Get recently ended auctions
        ended_auctions = Auction.query.filter_by(status='ended').order_by(
            Auction.end_time.desc()
        ).limit(3).all()
        return render_template('index.html',
                               active_auctions=active_auctions,
                               ended_auctions=ended_auctions)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            full_name = request.form.get('full_name', '').strip()
            phone = request.form.get('phone', '').strip()

            # Validation
            errors = []
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters.')
            if not email or '@' not in email:
                errors.append('Please provide a valid email address.')
            if not password or len(password) < 6:
                errors.append('Password must be at least 6 characters.')
            if password != confirm_password:
                errors.append('Passwords do not match.')
            if User.query.filter_by(username=username).first():
                errors.append('Username already exists.')
            if User.query.filter_by(email=email).first():
                errors.append('Email already registered.')

            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('register.html')

            # Create new user
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                phone=phone
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user, remember=True)
                flash(f'Welcome back, {user.username}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """Log out the current user."""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    # ============================================================
    # Routes - Dashboard
    # ============================================================

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard - shows active auctions, bid history, won/lost items."""
        check_and_close_auctions()

        # Active auctions created by the user (seller view)
        my_auctions = Auction.query.join(Item).filter(
            Item.seller_id == current_user.id
        ).order_by(Auction.created_at.desc()).all()

        # Bids placed by the user
        my_bids = Bid.query.filter_by(bidder_id=current_user.id).order_by(
            Bid.timestamp.desc()
        ).all()

        # Auctions won by the user
        won_auctions = Auction.query.filter_by(
            winner_id=current_user.id, status='ended'
        ).all()

        # Auctions where user placed bids but lost
        bid_auction_ids = db.session.query(Bid.auction_id).filter_by(
            bidder_id=current_user.id
        ).distinct().subquery()

        lost_auctions = Auction.query.filter(
            Auction.id.in_(bid_auction_ids),
            Auction.status == 'ended',
            Auction.winner_id != current_user.id
        ).all()

        # Stats
        total_bids = len(my_bids)
        total_won = len(won_auctions)
        total_lost = len(lost_auctions)
        active_listings = sum(1 for a in my_auctions if a.status == 'active')

        return render_template('dashboard.html',
                               my_auctions=my_auctions,
                               my_bids=my_bids,
                               won_auctions=won_auctions,
                               lost_auctions=lost_auctions,
                               total_bids=total_bids,
                               total_won=total_won,
                               total_lost=total_lost,
                               active_listings=active_listings)

    # ============================================================
    # Routes - Auction Management
    # ============================================================

    @app.route('/auctions')
    def auctions():
        """List all active auctions."""
        check_and_close_auctions()
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category', '')
        search = request.args.get('search', '')

        query = Auction.query.filter_by(status='active')

        if category:
            query = query.join(Item).filter(Item.category == category)
        if search:
            query = query.join(Item).filter(
                Item.title.ilike(f'%{search}%') |
                Item.description.ilike(f'%{search}%')
            )

        auctions_list = query.order_by(Auction.end_time.asc()).paginate(
            page=page, per_page=9, error_out=False
        )

        # Get unique categories for filter
        categories = db.session.query(Item.category).distinct().filter(
            Item.category.isnot(None)
        ).all()
        categories = [c[0] for c in categories if c[0]]

        return render_template('auctions.html',
                               auctions=auctions_list,
                               categories=categories,
                               current_category=category,
                               search=search)

    @app.route('/auction/<int:auction_id>')
    def auction_detail(auction_id):
        """View detailed auction page with bidding interface."""
        check_and_close_auctions()
        auction = Auction.query.get_or_404(auction_id)
        bids = Bid.query.filter_by(auction_id=auction_id, is_valid=True).order_by(
            Bid.amount.desc()
        ).limit(20).all()

        # Calculate time remaining
        now = utcnow()
        time_left = None
        if auction.status == 'active' and auction.end_time > now:
            delta = auction.end_time - now
            time_left = {
                'days': delta.days,
                'hours': delta.seconds // 3600,
                'minutes': (delta.seconds % 3600) // 60,
                'seconds': delta.seconds % 60,
                'total_seconds': int(delta.total_seconds())
            }

        return render_template('auction_detail.html',
                               auction=auction,
                               bids=bids,
                               time_left=time_left)

    @app.route('/create-auction', methods=['GET', 'POST'])
    @login_required
    def create_auction():
        """Create a new auction listing."""
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            starting_price = request.form.get('starting_price', 0, type=float)
            duration_hours = request.form.get('duration_hours', 24, type=int)

            # Validation
            errors = []
            if not title:
                errors.append('Title is required.')
            if starting_price <= 0:
                errors.append('Starting price must be greater than 0.')
            if duration_hours < 1 or duration_hours > 720:
                errors.append('Duration must be between 1 and 720 hours (30 days).')

            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('create_auction.html')

            # Handle image upload
            image_url = '/static/images/default-item.jpg'
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to avoid filename conflicts
                    filename = f"{int(datetime.now().timestamp())}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_url = f'/static/images/uploads/{filename}'

            # Create item
            item = Item(
                title=title,
                description=description,
                image_url=image_url,
                category=category or 'General',
                seller_id=current_user.id
            )
            db.session.add(item)
            db.session.flush()  # Get the item ID

            # Create auction
            now = utcnow()
            auction = Auction(
                item_id=item.id,
                starting_price=starting_price,
                current_price=starting_price,
                start_time=now,
                end_time=now + timedelta(hours=duration_hours),
                status='active'
            )
            db.session.add(auction)
            db.session.commit()

            flash('Auction created successfully!', 'success')
            return redirect(url_for('auction_detail', auction_id=auction.id))

        return render_template('create_auction.html')

    # ============================================================
    # Routes - Bidding System
    # ============================================================

    @app.route('/api/place-bid', methods=['POST'])
    @login_required
    def place_bid():
        """API endpoint to place a bid on an auction."""
        check_and_close_auctions()

        data = request.get_json()
        auction_id = data.get('auction_id')
        bid_amount = data.get('amount', 0)

        try:
            bid_amount = float(bid_amount)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid bid amount.'}), 400

        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'success': False, 'message': 'Auction not found.'}), 404

        # Validation checks
        if not auction.is_active:
            return jsonify({'success': False, 'message': 'This auction has ended.'}), 400

        if auction.item.seller_id == current_user.id:
            return jsonify({'success': False,
                            'message': 'You cannot bid on your own auction.'}), 400

        if bid_amount <= auction.current_price:
            return jsonify({
                'success': False,
                'message': f'Bid must be higher than current price (${auction.current_price:.2f}).'
            }), 400

        # Minimum bid increment: $1 or 1% of current price, whichever is greater
        min_increment = max(1.0, auction.current_price * 0.01)
        if bid_amount < auction.current_price + min_increment:
            return jsonify({
                'success': False,
                'message': f'Minimum bid increment is ${min_increment:.2f}.'
            }), 400

        # Place the bid
        bid = Bid(
            auction_id=auction_id,
            bidder_id=current_user.id,
            amount=bid_amount,
            is_valid=True
        )
        db.session.add(bid)

        # Update auction current price and bid count
        auction.current_price = bid_amount
        auction.bid_count += 1
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Bid placed successfully!',
            'new_price': bid_amount,
            'bid_count': auction.bid_count,
            'bidder': current_user.username
        })

    @app.route('/api/auction-status/<int:auction_id>')
    def auction_status(auction_id):
        """API endpoint to get real-time auction status."""
        check_and_close_auctions()
        auction = Auction.query.get_or_404(auction_id)

        now = utcnow()
        time_left = 0
        if auction.status == 'active' and auction.end_time > now:
            time_left = int((auction.end_time - now).total_seconds())

        # Get latest bids
        latest_bids = Bid.query.filter_by(
            auction_id=auction_id, is_valid=True
        ).order_by(Bid.amount.desc()).limit(5).all()

        bids_data = [{
            'bidder': bid.bidder.username,
            'amount': bid.amount,
            'time': bid.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for bid in latest_bids]

        return jsonify({
            'current_price': auction.current_price,
            'bid_count': auction.bid_count,
            'status': auction.status,
            'time_remaining': time_left,
            'winner': auction.winner.username if auction.winner else None,
            'latest_bids': bids_data
        })

    # ============================================================
    # Routes - Analytics
    # ============================================================

    @app.route('/analytics')
    @login_required
    def analytics():
        """Analytics dashboard with auction reports."""
        check_and_close_auctions()

        # Top Bidders (by number of bids)
        from sqlalchemy import func
        top_bidders = db.session.query(
            User.username,
            func.count(Bid.id).label('bid_count'),
            func.sum(Bid.amount).label('total_amount')
        ).join(Bid, User.id == Bid.bidder_id).group_by(User.username).order_by(
            func.count(Bid.id).desc()
        ).limit(10).all()

        # Most Active Auctions (by bid count)
        active_auctions = db.session.query(
            Auction.id,
            Item.title,
            Auction.current_price,
            Auction.bid_count,
            Auction.status
        ).join(Item, Auction.item_id == Item.id).order_by(
            Auction.bid_count.desc()
        ).limit(10).all()

        # Total Revenue (sum of winning bids from ended auctions)
        total_revenue = db.session.query(
            func.sum(Auction.current_price)
        ).filter(Auction.status == 'ended', Auction.winner_id.isnot(None)).scalar() or 0

        # Category Distribution
        category_stats = db.session.query(
            Item.category,
            func.count(Auction.id).label('auction_count'),
            func.avg(Auction.current_price).label('avg_price')
        ).join(Auction, Item.id == Auction.item_id).group_by(
            Item.category
        ).all()

        # Overall Stats
        total_users = User.query.count()
        total_auctions = Auction.query.count()
        total_bids = Bid.query.count()
        active_count = Auction.query.filter_by(status='active').count()
        ended_count = Auction.query.filter_by(status='ended').count()

        return render_template('analytics.html',
                               top_bidders=top_bidders,
                               active_auctions=active_auctions,
                               total_revenue=total_revenue,
                               category_stats=category_stats,
                               total_users=total_users,
                               total_auctions=total_auctions,
                               total_bids=total_bids,
                               active_count=active_count,
                               ended_count=ended_count)

    @app.route('/api/analytics/chart-data')
    @login_required
    def chart_data():
        """API endpoint for analytics chart data."""
        from sqlalchemy import func

        # Bids per day (last 30 days)
        thirty_days_ago = utcnow() - timedelta(days=30)
        daily_bids = db.session.query(
            func.date(Bid.timestamp).label('date'),
            func.count(Bid.id).label('count')
        ).filter(Bid.timestamp >= thirty_days_ago).group_by(
            func.date(Bid.timestamp)
        ).all()

        # Price distribution
        price_ranges = db.session.query(
            func.count(Auction.id)
        ).filter(Auction.status == 'ended').all()

        return jsonify({
            'daily_bids': [{'date': str(d.date), 'count': d.count} for d in daily_bids],
            'total_ended': price_ranges[0][0] if price_ranges else 0
        })

    # ============================================================
    # Routes - ETL Pipeline
    # ============================================================

    @app.route('/etl')
    @login_required
    def etl_dashboard():
        """ETL Pipeline dashboard."""
        return render_template('etl.html')

    @app.route('/api/etl/run', methods=['POST'])
    @login_required
    def run_etl():
        """Run the ETL pipeline."""
        try:
            from etl_pipeline import ETLPipeline
            pipeline = ETLPipeline(app)
            results = pipeline.run_full_pipeline()
            return jsonify({'success': True, 'results': results})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/etl/load-csv', methods=['POST'])
    @login_required
    def load_csv():
        """Load data from CSV files into database."""
        try:
            from etl_pipeline import ETLPipeline
            pipeline = ETLPipeline(app)
            results = pipeline.load_from_csv()
            return jsonify({'success': True, 'results': results})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ============================================================
    # Template Filters
    # ============================================================

    @app.template_filter('timeago')
    def timeago_filter(dt):
        """Convert datetime to a human-readable 'time ago' format."""
        if not dt:
            return 'N/A'
        now = utcnow()
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        diff = now - dt
        seconds = diff.total_seconds()

        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes}m ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours}h ago'
        else:
            days = int(seconds / 86400)
            return f'{days}d ago'

    @app.template_filter('currency')
    def currency_filter(value):
        """Format a number as currency."""
        try:
            return f'${float(value):,.2f}'
        except (ValueError, TypeError):
            return '$0.00'

    # ============================================================
    # Error Handlers
    # ============================================================

    @app.errorhandler(404)
    def not_found(e):
        return render_template('base.html', error='Page not found'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', error='Internal server error'), 500

    return app


# ============================================================
# Run the Application
# ============================================================

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
