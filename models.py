from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(256), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, nullable=True)
    
    playlists = db.relationship('Playlist', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    watch_history = db.relationship('WatchHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def avatar_url(self):
        if self.avatar:
            return f'/static/uploads/avatars/{self.avatar}'
        return '/static/images/default-avatar.png'


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    
    movies = db.relationship('Movie', backref='category', lazy='dynamic')
    series = db.relationship('Series', backref='category', lazy='dynamic')


class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    cover_image = db.Column(db.String(500), nullable=True)
    video_source_type = db.Column(db.String(20), default='upload')  # upload, youtube, external
    video_url = db.Column(db.String(500), nullable=True)
    video_file = db.Column(db.String(500), nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    year = db.Column(db.Integer, nullable=True)
    views = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    admin = db.relationship('User', foreign_keys=[admin_id])
    comments = db.relationship('Comment', backref='movie', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='movie', lazy='dynamic', cascade='all, delete-orphan')
    watch_history = db.relationship('WatchHistory', backref='movie', lazy='dynamic', cascade='all, delete-orphan')
    playlist_items = db.relationship('PlaylistItem', backref='movie', lazy='dynamic', cascade='all, delete-orphan')
    
    def cover_url(self):
        if self.cover_image:
            return f'/static/uploads/covers/{self.cover_image}'
        return '/static/images/poster-placeholder.png'
    
    def video_source(self):
        if self.video_source_type == 'upload' and self.video_file:
            return f'/static/uploads/videos/{self.video_file}'
        elif self.video_source_type in ('youtube', 'external') and self.video_url:
            return self.video_url
        return None
    
    def like_count(self):
        return Like.query.filter_by(movie_id=self.id).count()
    
    def comment_count(self):
        return Comment.query.filter_by(movie_id=self.id).count()


class Series(db.Model):
    __tablename__ = 'series'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    cover_image = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='ongoing')  # ongoing, completed
    total_seasons = db.Column(db.Integer, default=0)
    total_episodes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    admin = db.relationship('User', foreign_keys=[admin_id])
    seasons = db.relationship('Season', backref='series', lazy='dynamic', cascade='all, delete-orphan', order_by='Season.season_number')
    
    def cover_url(self):
        if self.cover_image:
            return f'/static/uploads/covers/{self.cover_image}'
        return '/static/images/poster-placeholder.png'
    
    def episode_count(self):
        return Episode.query.filter_by(series_id=self.id).count()
    
    def season_count(self):
        return Season.query.filter_by(series_id=self.id).count()


class Season(db.Model):
    __tablename__ = 'seasons'
    
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)
    season_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    episode_count = db.Column(db.Integer, default=0)
    
    episodes = db.relationship('Episode', backref='season', lazy='dynamic', cascade='all, delete-orphan', order_by='Episode.episode_number')


class Episode(db.Model):
    __tablename__ = 'episodes'
    
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)
    episode_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail = db.Column(db.String(500), nullable=True)
    video_source_type = db.Column(db.String(20), default='upload')
    video_url = db.Column(db.String(500), nullable=True)
    video_file = db.Column(db.String(500), nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    views = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    series = db.relationship('Series', foreign_keys=[series_id])
    comments = db.relationship('Comment', backref='episode', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='episode', lazy='dynamic', cascade='all, delete-orphan')
    watch_history = db.relationship('WatchHistory', backref='episode', lazy='dynamic', cascade='all, delete-orphan')
    playlist_items = db.relationship('PlaylistItem', backref='episode', lazy='dynamic', cascade='all, delete-orphan')
    
    def thumbnail_url(self):
        if self.thumbnail:
            return f'/static/uploads/thumbnails/{self.thumbnail}'
        return '/static/images/poster-placeholder.png'
    
    def video_source(self):
        if self.video_source_type == 'upload' and self.video_file:
            return f'/static/uploads/videos/{self.video_file}'
        elif self.video_source_type in ('youtube', 'external') and self.video_url:
            return self.video_url
        return None
    
    def like_count(self):
        return Like.query.filter_by(episode_id=self.id).count()
    
    def comment_count(self):
        return Comment.query.filter_by(episode_id=self.id).count()


class Playlist(db.Model):
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('PlaylistItem', backref='playlist', lazy='dynamic', cascade='all, delete-orphan', order_by='PlaylistItem.position')
    
    def item_count(self):
        return PlaylistItem.query.filter_by(playlist_id=self.id).count()
    
    def cover_image(self):
        first_item = PlaylistItem.query.filter_by(playlist_id=self.id).order_by(PlaylistItem.position).first()
        if first_item:
            if first_item.movie:
                return first_item.movie.cover_url()
            elif first_item.episode:
                return first_item.episode.thumbnail_url()
        return '/static/images/poster-placeholder.png'


class PlaylistItem(db.Model):
    __tablename__ = 'playlist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=True)
    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    position = db.Column(db.Integer, default=0)


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=True)
    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_edited = db.Column(db.Boolean, default=False)
    
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic', cascade='all, delete-orphan')
    
    def time_ago(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        if diff.days > 365:
            return f'{diff.days // 365}y ago'
        if diff.days > 30:
            return f'{diff.days // 30}mo ago'
        if diff.days > 0:
            return f'{diff.days}d ago'
        if diff.seconds > 3600:
            return f'{diff.seconds // 3600}h ago'
        if diff.seconds > 60:
            return f'{diff.seconds // 60}m ago'
        return 'just now'


class Like(db.Model):
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=True)
    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id', 'episode_id', name='unique_like'),)


class WatchHistory(db.Model):
    __tablename__ = 'watch_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=True)
    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'), nullable=True)
    progress = db.Column(db.Integer, default=0)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)