import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tupple-secret-key-2026-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "instance", "tupple.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    COVERS_FOLDER = os.path.join(UPLOAD_FOLDER, 'covers')
    VIDEOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
    THUMBNAILS_FOLDER = os.path.join(UPLOAD_FOLDER, 'thumbnails')
    AVATARS_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
    
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file upload
    
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    MOVIES_PER_PAGE = 12
    SERIES_PER_PAGE = 12
    USERS_PER_PAGE = 20
    COMMENTS_PER_PAGE = 20