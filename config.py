"""
Configuration settings for the Online Auction System.
Supports SQLite for development and PostgreSQL for production.
"""

import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class."""
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY', 'auction-system-secret-key-2024')

    # SQLite database for development (easy setup, no external dependencies)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "auction.db")}'
    )

    # Disable modification tracking to save memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folder for item images
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    # Allowed image extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
