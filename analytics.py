"""
Analytics Module for the Online Auction System.
Uses Pandas for data analysis and report generation.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from models import db, User, Item, Auction, Bid

class AuctionAnalytics:
    def __init__(self, app=None):
        self.app = app

    def get_bids_dataframe(self):
        with self.app.app_context():
            bids = Bid.query.all()
            data = [{'bid_id': b.id, 'auction_id': b.auction_id, 'bidder_id': b.bidder_id,
                      'bidder_name': b.bidder.username, 'amount': b.amount,
                      'timestamp': b.timestamp, 'is_valid': b.is_valid} for b in bids]
            return pd.DataFrame(data)

    def get_auctions_dataframe(self):
        with self.app.app_context():
            auctions = Auction.query.all()
            data = [{'auction_id': a.id, 'item_title': a.item.title, 'category': a.item.category,
                      'starting_price': a.starting_price, 'current_price': a.current_price,
                      'bid_count': a.bid_count, 'status': a.status, 'start_time': a.start_time,
                      'end_time': a.end_time, 'seller': a.item.seller.username,
                      'winner': a.winner.username if a.winner else None} for a in auctions]
            return pd.DataFrame(data)

    def top_bidders_report(self, top_n=10):
        bids_df = self.get_bids_dataframe()
        if bids_df.empty:
            return pd.DataFrame()
        return bids_df.groupby('bidder_name').agg(
            total_bids=('bid_id', 'count'), total_amount=('amount', 'sum'),
            avg_bid=('amount', 'mean'), max_bid=('amount', 'max')
        ).sort_values('total_bids', ascending=False).head(top_n).round(2)

    def revenue_report(self):
        auctions_df = self.get_auctions_dataframe()
        if auctions_df.empty:
            return {'total_revenue': 0, 'avg_sale_price': 0, 'total_sold': 0}
        ended = auctions_df[auctions_df['status'] == 'ended']
        sold = ended[ended['winner'].notna()]
        return {
            'total_revenue': round(sold['current_price'].sum(), 2),
            'avg_sale_price': round(sold['current_price'].mean(), 2) if len(sold) > 0 else 0,
            'total_sold': len(sold)
        }

    def category_analysis(self):
        auctions_df = self.get_auctions_dataframe()
        if auctions_df.empty:
            return pd.DataFrame()
        return auctions_df.groupby('category').agg(
            total_auctions=('auction_id', 'count'), avg_price=('current_price', 'mean'),
            total_bids=('bid_count', 'sum')
        ).sort_values('total_auctions', ascending=False).round(2)
