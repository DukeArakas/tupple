import os
import secrets
# import imghdr  # <-- REMOVED (unused, and removed in Python 3.13)
import filetype   # <-- Added (option 1 – available for future image type detection if needed)
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Category, Movie, Series, Season, Episode, Playlist, PlaylistItem, Comment, Like, WatchHistory
from forms import (LoginForm, RegistrationForm, ProfileForm, ChangePasswordForm,
                   MovieForm, SeriesForm, SeasonForm, EpisodeForm, PlaylistForm,
                   CommentForm, SearchForm)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'

# Create upload directories
os.makedirs(Config.COVERS_FOLDER, exist_ok=True)
os.makedirs(Config.VIDEOS_FOLDER, exist_ok=True)
os.makedirs(Config.THUMBNAILS_FOLDER, exist_ok=True)
os.makedirs(Config.AVATARS_FOLDER, exist_ok=True)

# Create default avatar and placeholder
AVATAR_PATH = os.path.join(app.root_path, 'static', 'images', 'default-avatar.png')
PLACEHOLDER_PATH = os.path.join(app.root_path, 'static', 'images', 'poster-placeholder.png')


def create_default_images():
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create default avatar
        if not os.path.exists(AVATAR_PATH):
            img = Image.new('RGBA', (200, 200), (15, 15, 25, 255))
            draw = ImageDraw.Draw(img)
            # Draw a simple user icon
            draw.ellipse([60, 40, 140, 120], fill=(123, 45, 142, 255))
            draw.ellipse([40, 100, 160, 200], fill=(123, 45, 142, 255))
            img.save(AVATAR_PATH)
        
        # Create poster placeholder
        if not os.path.exists(PLACEHOLDER_PATH):
            img = Image.new('RGBA', (400, 600), (10, 10, 18, 255))
            draw = ImageDraw.Draw(img)
            # Gradient-like background
            for y in range(600):
                r = int(10 + (123 - 10) * y / 600 * 0.3)
                g = int(10 * y / 600)
                b = int(18 + (142 - 18) * y / 600 * 0.3)
                draw.line([(0, y), (400, y)], fill=(r, g, b, 255))
            # Draw film icon shape
            draw.rectangle([140, 220, 260, 340], outline=(123, 45, 142, 200), width=3)
            draw.polygon([(200, 240), (200, 320), (240, 280)], fill=(0, 229, 204, 200))
            # Text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            except:
                font = ImageFont.load_default()
            draw.text((140, 360), "Tupple", fill=(255, 255, 255, 200), font=font)
            draw.text((110, 400), "No Poster", fill=(255, 255, 255, 150), font=font)
            img.save(PLACEHOLDER_PATH)
    except Exception as e:
        print(f"Warning: Could not create default images: {e}")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, folder, prefix=''):
    if file and allowed_file(file.filename, Config.ALLOWED_IMAGE_EXTENSIONS | Config.ALLOWED_VIDEO_EXTENSIONS):
        ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        filename = f"{prefix}{secrets.token_hex(8)}.{ext}"
        filepath = os.path.join(folder, filename)
        file.save(filepath)
        return filename
    return None


def get_youtube_embed_url(url):
    """Convert YouTube URL to embed URL with no-cookie domain"""
    import re
    # Extract video ID from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/watch\?.*v=)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube-nocookie.com/embed/{video_id}?modestbranding=1&rel=0&controls=1"
    return url


def init_categories():
    """Initialize default categories if none exist"""
    categories = [
        ('Action', 'action'),
        ('Sci-Fi', 'sci-fi'),
        ('Horror', 'horror'),
        ('Animation', 'animation'),
        ('Anime', 'anime'),
        ('Drama', 'drama'),
        ('Thriller', 'thriller'),
        ('Comedy', 'comedy'),
        ('Romance', 'romance'),
        ('Nollywood', 'nollywood'),
        ('Netflix', 'netflix'),
        ('Documentary', 'documentary'),
        ('Fantasy', 'fantasy'),
        ('Crime', 'crime'),
        ('Adventure', 'adventure'),
    ]
    for name, slug in categories:
        if not Category.query.filter_by(slug=slug).first():
            db.session.add(Category(name=name, slug=slug))
    db.session.commit()


@app.context_processor
def inject_globals():
    categories = Category.query.all()
    search_form = SearchForm()
    return dict(categories=categories, search_form=search_form, now=datetime.utcnow)


# ========== HOME PAGE ==========
@app.route('/')
def index():
    trending_movies = Movie.query.filter_by(is_active=True).order_by(Movie.views.desc()).limit(8).all()
    latest_movies = Movie.query.filter_by(is_active=True).order_by(Movie.created_at.desc()).limit(8).all()
    latest_series = Series.query.filter_by(is_active=True).order_by(Series.created_at.desc()).limit(8).all()
    anime_series = Series.query.join(Category).filter(Category.slug == 'anime', Series.is_active == True).order_by(Series.created_at.desc()).limit(8).all()
    anime_movies = Movie.query.join(Category).filter(Category.slug == 'anime', Movie.is_active == True).order_by(Movie.created_at.desc()).limit(8).all()
    return render_template('index.html',
                         trending_movies=trending_movies,
                         latest_movies=latest_movies,
                         latest_series=latest_series,
                         anime_series=anime_series,
                         anime_movies=anime_movies)


# ========== AUTHENTICATION ==========
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first():
            flash('Username or email already taken.', 'error')
            return redirect(url_for('register'))
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please sign in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username.data) | (User.email == form.username.data)).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been disabled.', 'error')
                return redirect(url_for('login'))
            login_user(user, remember=True)
            user.last_seen = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('index'))


# ========== MOVIE DETAIL ==========
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    movie.views += 1
    db.session.commit()
    
    comments = Comment.query.filter_by(movie_id=movie_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    related_movies = Movie.query.filter(Movie.category_id == movie.category_id, Movie.id != movie.id).limit(6).all()
    
    user_liked = False
    user_playlists = []
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(user_id=current_user.id, movie_id=movie_id).first() is not None
        user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    
    video_embed_url = None
    if movie.video_source_type == 'youtube' and movie.video_url:
        video_embed_url = get_youtube_embed_url(movie.video_url)
    
    return render_template('movie_detail.html', movie=movie, comments=comments,
                         related_movies=related_movies, user_liked=user_liked,
                         user_playlists=user_playlists, video_embed_url=video_embed_url,
                         comment_form=CommentForm())


# ========== SERIES FOLDER VIEW ==========
@app.route('/series/<int:series_id>')
def series_detail(series_id):
    series = Series.query.get_or_404(series_id)
    series.views += 1
    db.session.commit()
    
    seasons = Season.query.filter_by(series_id=series_id).order_by(Season.season_number).all()
    season_id = request.args.get('season', type=int)
    
    if season_id:
        current_season = Season.query.get_or_404(season_id)
    elif seasons:
        current_season = seasons[0]
    else:
        current_season = None
    
    episodes = []
    if current_season:
        episodes = Episode.query.filter_by(season_id=current_season.id).order_by(Episode.episode_number).all()
    
    user_playlists = []
    if current_user.is_authenticated:
        user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    
    return render_template('series_detail.html', series=series, seasons=seasons,
                         current_season=current_season, episodes=episodes,
                         user_playlists=user_playlists)


# ========== EPISODE WATCH PAGE ==========
@app.route('/series/<int:series_id>/episode/<int:episode_id>')
def watch_episode(series_id, episode_id):
    episode = Episode.query.get_or_404(episode_id)
    series = Series.query.get_or_404(series_id)
    
    episode.views += 1
    db.session.commit()
    
    comments = Comment.query.filter_by(episode_id=episode_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    # Get prev/next episodes
    prev_episode = Episode.query.filter(
        Episode.series_id == series_id,
        Episode.season_id == episode.season_id,
        Episode.episode_number < episode.episode_number
    ).order_by(Episode.episode_number.desc()).first()
    
    next_episode = Episode.query.filter(
        Episode.series_id == series_id,
        Episode.season_id == episode.season_id,
        Episode.episode_number > episode.episode_number
    ).order_by(Episode.episode_number).first()
    
    user_liked = False
    user_playlists = []
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(user_id=current_user.id, episode_id=episode_id).first() is not None
        user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    
    video_embed_url = None
    if episode.video_source_type == 'youtube' and episode.video_url:
        video_embed_url = get_youtube_embed_url(episode.video_url)
    
    return render_template('watch_episode.html', episode=episode, series=series,
                         comments=comments, prev_episode=prev_episode,
                         next_episode=next_episode, user_liked=user_liked,
                         user_playlists=user_playlists, video_embed_url=video_embed_url,
                         comment_form=CommentForm())


# ========== SEARCH ==========
@app.route('/search')
def search():
    query = request.args.get('q', '')
    category_slug = request.args.get('category', '')
    content_type = request.args.get('type', '')
    sort = request.args.get('sort', 'relevance')
    
    movies = []
    series_list = []
    
    if query or category_slug or content_type:
        # Search movies
        if content_type in ('', 'movie'):
            movies_query = Movie.query.filter_by(is_active=True)
            if query:
                movies_query = movies_query.filter(
                    db.or_(Movie.title.ilike(f'%{query}%'), Movie.description.ilike(f'%{query}%'))
                )
            if category_slug:
                cat = Category.query.filter_by(slug=category_slug).first()
                if cat:
                    movies_query = movies_query.filter_by(category_id=cat.id)
            
            if sort == 'newest':
                movies_query = movies_query.order_by(Movie.created_at.desc())
            elif sort == 'most_viewed':
                movies_query = movies_query.order_by(Movie.views.desc())
            elif sort == 'rating':
                movies_query = movies_query.order_by(Movie.rating.desc())
            
            movies = movies_query.all()
        
        # Search series
        if content_type in ('', 'series'):
            series_query = Series.query.filter_by(is_active=True)
            if query:
                series_query = series_query.filter(
                    db.or_(Series.title.ilike(f'%{query}%'), Series.description.ilike(f'%{query}%'))
                )
            if category_slug:
                cat = Category.query.filter_by(slug=category_slug).first()
                if cat:
                    series_query = series_query.filter_by(category_id=cat.id)
            
            if sort == 'newest':
                series_query = series_query.order_by(Series.created_at.desc())
            elif sort == 'most_viewed':
                series_query = series_query.order_by(Series.views.desc())
            
            series_list = series_query.all()
    
    return render_template('search.html', query=query, movies=movies, series_list=series_list,
                         category_slug=category_slug, content_type=content_type, sort=sort)


# ========== CATEGORY PAGE ==========
@app.route('/category/<slug>')
def category_page(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    movies = Movie.query.filter_by(category_id=category.id, is_active=True).order_by(Movie.created_at.desc()).all()
    series_list = Series.query.filter_by(category_id=category.id, is_active=True).order_by(Series.created_at.desc()).all()
    return render_template('category.html', category=category, movies=movies, series_list=series_list)


# ========== USER DASHBOARD ==========
@app.route('/dashboard')
@login_required
def dashboard():
    playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.created_at.desc()).all()
    watch_history = WatchHistory.query.filter_by(user_id=current_user.id).order_by(WatchHistory.watched_at.desc()).limit(20).all()
    liked_movies = Movie.query.join(Like).filter(Like.user_id == current_user.id).all()
    liked_episodes = Episode.query.join(Like).filter(Like.user_id == current_user.id).all()
    return render_template('user/dashboard.html', playlists=playlists,
                         watch_history=watch_history, liked_movies=liked_movies,
                         liked_episodes=liked_episodes)


@app.route('/dashboard/playlists', methods=['GET', 'POST'])
@login_required
def playlists():
    form = PlaylistForm()
    if form.validate_on_submit():
        playlist = Playlist(
            user_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            is_public=form.is_public.data
        )
        db.session.add(playlist)
        db.session.commit()
        flash('Playlist created!', 'success')
        return redirect(url_for('playlists'))
    
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.created_at.desc()).all()
    return render_template('user/playlists.html', playlists=user_playlists, form=form)


@app.route('/dashboard/playlist/<int:playlist_id>')
@login_required
def playlist_detail(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        abort(403)
    return render_template('user/playlist_detail.html', playlist=playlist)


@app.route('/dashboard/history')
@login_required
def watch_history():
    history = WatchHistory.query.filter_by(user_id=current_user.id).order_by(WatchHistory.watched_at.desc()).all()
    return render_template('user/history.html', history=history)


@app.route('/dashboard/liked')
@login_required
def liked_videos():
    liked_movies = Movie.query.join(Like).filter(Like.user_id == current_user.id).all()
    liked_episodes = Episode.query.join(Like).filter(Like.user_id == current_user.id).all()
    return render_template('user/liked.html', liked_movies=liked_movies, liked_episodes=liked_episodes)


@app.route('/dashboard/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    profile_form = ProfileForm(obj=current_user)
    password_form = ChangePasswordForm()
    
    if profile_form.validate_on_submit():
        current_user.username = profile_form.username.data
        current_user.email = profile_form.email.data
        if profile_form.avatar.data:
            avatar_file = save_uploaded_file(profile_form.avatar.data, Config.AVATARS_FOLDER, 'avatar_')
            if avatar_file:
                current_user.avatar = avatar_file
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('user_settings'))
    
    if password_form.validate_on_submit():
        if current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Password changed!', 'success')
            return redirect(url_for('user_settings'))
        else:
            flash('Current password is incorrect.', 'error')
    
    return render_template('user/settings.html', profile_form=profile_form, password_form=password_form)


# ========== API ENDPOINTS ==========
@app.route('/api/movie/<int:movie_id>/like', methods=['POST'])
@login_required
def toggle_movie_like(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    existing = Like.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'liked': False, 'count': movie.like_count()})
    else:
        like = Like(user_id=current_user.id, movie_id=movie_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'liked': True, 'count': movie.like_count()})


@app.route('/api/episode/<int:episode_id>/like', methods=['POST'])
@login_required
def toggle_episode_like(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    existing = Like.query.filter_by(user_id=current_user.id, episode_id=episode_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'liked': False, 'count': episode.like_count()})
    else:
        like = Like(user_id=current_user.id, episode_id=episode_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'liked': True, 'count': episode.like_count()})


@app.route('/api/movie/<int:movie_id>/comment', methods=['POST'])
@login_required
def add_movie_comment(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(user_id=current_user.id, movie_id=movie_id, content=form.content.data)
        db.session.add(comment)
        db.session.commit()
        return jsonify({
            'id': comment.id,
            'content': comment.content,
            'author': current_user.username,
            'avatar': current_user.avatar_url(),
            'time_ago': comment.time_ago(),
            'count': movie.comment_count()
        })
    return jsonify({'error': 'Invalid form'}), 400


@app.route('/api/episode/<int:episode_id>/comment', methods=['POST'])
@login_required
def add_episode_comment(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(user_id=current_user.id, episode_id=episode_id, content=form.content.data)
        db.session.add(comment)
        db.session.commit()
        return jsonify({
            'id': comment.id,
            'content': comment.content,
            'author': current_user.username,
            'avatar': current_user.avatar_url(),
            'time_ago': comment.time_ago(),
            'count': episode.comment_count()
        })
    return jsonify({'error': 'Invalid form'}), 400


@app.route('/api/playlist/add', methods=['POST'])
@login_required
def add_to_playlist():
    playlist_id = request.form.get('playlist_id', type=int)
    movie_id = request.form.get('movie_id', type=int)
    episode_id = request.form.get('episode_id', type=int)
    
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if already in playlist
    existing = PlaylistItem.query.filter_by(playlist_id=playlist_id)
    if movie_id:
        existing = existing.filter_by(movie_id=movie_id)
    elif episode_id:
        existing = existing.filter_by(episode_id=episode_id)
    
    if existing.first():
        return jsonify({'error': 'Already in playlist'}), 400
    
    item = PlaylistItem(playlist_id=playlist_id, movie_id=movie_id, episode_id=episode_id)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'count': playlist.item_count()})


@app.route('/api/playlist/<int:playlist_id>/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_playlist(playlist_id, item_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    item = PlaylistItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/playlist/<int:playlist_id>/delete', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(playlist)
    db.session.commit()
    flash('Playlist deleted.', 'info')
    return jsonify({'success': True})


@app.route('/api/watch/progress', methods=['POST'])
@login_required
def save_watch_progress():
    data = request.get_json()
    movie_id = data.get('movie_id')
    episode_id = data.get('episode_id')
    progress = data.get('progress', 0)
    
    if movie_id:
        wh = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        if wh:
            wh.progress = progress
            wh.watched_at = datetime.utcnow()
        else:
            wh = WatchHistory(user_id=current_user.id, movie_id=movie_id, progress=progress)
            db.session.add(wh)
    elif episode_id:
        wh = WatchHistory.query.filter_by(user_id=current_user.id, episode_id=episode_id).first()
        if wh:
            wh.progress = progress
            wh.watched_at = datetime.utcnow()
        else:
            wh = WatchHistory(user_id=current_user.id, episode_id=episode_id, progress=progress)
            db.session.add(wh)
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/download/<content_type>/<int:content_id>')
@login_required
def download(content_type, content_id):
    if content_type == 'movie':
        movie = Movie.query.get_or_404(content_id)
        movie.download_count += 1
        db.session.commit()
        if movie.video_source_type == 'upload' and movie.video_file:
            return send_from_directory(Config.VIDEOS_FOLDER, movie.video_file, as_attachment=True)
        elif movie.video_url:
            return redirect(movie.video_url)
    elif content_type == 'episode':
        episode = Episode.query.get_or_404(content_id)
        episode.download_count += 1
        db.session.commit()
        if episode.video_source_type == 'upload' and episode.video_file:
            return send_from_directory(Config.VIDEOS_FOLDER, episode.video_file, as_attachment=True)
        elif episode.video_url:
            return redirect(episode.video_url)
    
    flash('Download not available for this content.', 'error')
    return redirect(request.referrer or url_for('index'))


# ========== ADMIN ROUTES ==========
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_movies = Movie.query.count()
    total_series = Series.query.count()
    total_views = db.session.query(db.func.sum(Movie.views)).scalar() or 0
    total_views += db.session.query(db.func.sum(Series.views)).scalar() or 0
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_movies = Movie.query.order_by(Movie.created_at.desc()).limit(5).all()
    recent_series = Series.query.order_by(Series.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', total_users=total_users,
                         total_movies=total_movies, total_series=total_series,
                         total_views=total_views, recent_users=recent_users,
                         recent_movies=recent_movies, recent_series=recent_series)


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(db.or_(User.username.ilike(f'%{search}%'), User.email.ilike(f'%{search}%')))
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=Config.USERS_PER_PAGE, error_out=False
    )
    return render_template('admin/users.html', users=users, search=search)


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot ban yourself.', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'banned'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/movies')
@login_required
@admin_required
def admin_movies():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    query = Movie.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    movies = query.order_by(Movie.created_at.desc()).paginate(
        page=page, per_page=Config.MOVIES_PER_PAGE, error_out=False
    )
    return render_template('admin/movies.html', movies=movies, category_id=category_id)


@app.route('/admin/movies/post', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_post_movie():
    form = MovieForm()
    form.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        category_id = form.category_id.data if form.category_id.data != 0 else None
        
        cover_file = save_uploaded_file(form.cover_image.data, Config.COVERS_FOLDER, 'cover_')
        video_file = None
        video_url = None
        
        if form.video_source_type.data == 'upload':
            video_file = save_uploaded_file(form.video_file.data, Config.VIDEOS_FOLDER, 'video_')
        else:
            video_url = form.video_url.data
        
        movie = Movie(
            title=form.title.data,
            description=form.description.data,
            category_id=category_id,
            cover_image=cover_file,
            video_source_type=form.video_source_type.data,
            video_url=video_url,
            video_file=video_file,
            duration=form.duration.data,
            rating=form.rating.data,
            year=form.year.data,
            admin_id=current_user.id
        )
        db.session.add(movie)
        db.session.commit()
        flash('Movie posted successfully!', 'success')
        return redirect(url_for('admin_movies'))
    
    return render_template('admin/post_movie.html', form=form)


@app.route('/admin/movies/<int:movie_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Movie deleted.', 'info')
    return redirect(url_for('admin_movies'))


@app.route('/admin/series')
@login_required
@admin_required
def admin_series():
    page = request.args.get('page', 1, type=int)
    series_list = Series.query.order_by(Series.created_at.desc()).paginate(
        page=page, per_page=Config.SERIES_PER_PAGE, error_out=False
    )
    return render_template('admin/series_list.html', series_list=series_list)


@app.route('/admin/series/post', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_post_series():
    form = SeriesForm()
    form.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        category_id = form.category_id.data if form.category_id.data != 0 else None
        cover_file = save_uploaded_file(form.cover_image.data, Config.COVERS_FOLDER, 'cover_')
        
        series = Series(
            title=form.title.data,
            description=form.description.data,
            category_id=category_id,
            cover_image=cover_file,
            status=form.status.data,
            admin_id=current_user.id
        )
        db.session.add(series)
        db.session.commit()
        flash('Series created! Now add seasons and episodes.', 'success')
        return redirect(url_for('admin_manage_series', series_id=series.id))
    
    return render_template('admin/post_series.html', form=form)


@app.route('/admin/series/<int:series_id>/manage')
@login_required
@admin_required
def admin_manage_series(series_id):
    series = Series.query.get_or_404(series_id)
    seasons = Season.query.filter_by(series_id=series_id).order_by(Season.season_number).all()
    season_form = SeasonForm()
    return render_template('admin/manage_series.html', series=series, seasons=seasons, season_form=season_form)


@app.route('/admin/series/<int:series_id>/season/add', methods=['POST'])
@login_required
@admin_required
def admin_add_season(series_id):
    series = Series.query.get_or_404(series_id)
    form = SeasonForm()
    if form.validate_on_submit():
        season = Season(
            series_id=series_id,
            season_number=form.season_number.data,
            title=form.title.data
        )
        db.session.add(season)
        series.total_seasons = Season.query.filter_by(series_id=series_id).count()
        db.session.commit()
        flash(f'Season {form.season_number.data} added!', 'success')
    return redirect(url_for('admin_manage_series', series_id=series_id))


@app.route('/admin/series/season/<int:season_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_season(season_id):
    season = Season.query.get_or_404(season_id)
    series_id = season.series_id
    
    # Delete all episodes in this season
    Episode.query.filter_by(season_id=season_id).delete()
    db.session.delete(season)
    
    # Update series counts
    series = Series.query.get(series_id)
    series.total_seasons = Season.query.filter_by(series_id=series_id).count()
    series.total_episodes = Episode.query.filter_by(series_id=series_id).count()
    db.session.commit()
    
    flash('Season deleted.', 'info')
    return redirect(url_for('admin_manage_series', series_id=series_id))


@app.route('/admin/series/<int:series_id>/episode/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_episode(series_id):
    series = Series.query.get_or_404(series_id)
    seasons = Season.query.filter_by(series_id=series_id).all()
    
    if not seasons:
        flash('Please add a season first.', 'warning')
        return redirect(url_for('admin_manage_series', series_id=series_id))
    
    form = EpisodeForm()
    
    if form.validate_on_submit():
        season_id = request.form.get('season_id', type=int)
        season = Season.query.get_or_404(season_id)
        
        thumbnail_file = save_uploaded_file(form.thumbnail.data, Config.THUMBNAILS_FOLDER, 'thumb_') if form.thumbnail.data else None
        video_file = None
        video_url = None
        
        if form.video_source_type.data == 'upload':
            video_file = save_uploaded_file(form.video_file.data, Config.VIDEOS_FOLDER, 'video_')
        else:
            video_url = form.video_url.data
        
        episode = Episode(
            season_id=season_id,
            series_id=series_id,
            episode_number=form.episode_number.data,
            title=form.title.data,
            description=form.description.data,
            thumbnail=thumbnail_file,
            video_source_type=form.video_source_type.data,
            video_url=video_url,
            video_file=video_file,
            duration=form.duration.data
        )
        db.session.add(episode)
        
        # Update counts
        season.episode_count = Episode.query.filter_by(season_id=season_id).count()
        series.total_episodes = Episode.query.filter_by(series_id=series_id).count()
        db.session.commit()
        
        flash(f'Episode {form.episode_number.data} added!', 'success')
        return redirect(url_for('admin_manage_series', series_id=series_id))
    
    return render_template('admin/add_episode.html', form=form, series=series, seasons=seasons)


@app.route('/admin/series/episode/<int:episode_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_episode(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    series_id = episode.series_id
    season_id = episode.season_id
    
    db.session.delete(episode)
    
    # Update counts
    season = Season.query.get(season_id)
    season.episode_count = Episode.query.filter_by(season_id=season_id).count()
    series = Series.query.get(series_id)
    series.total_episodes = Episode.query.filter_by(series_id=series_id).count()
    db.session.commit()
    
    flash('Episode deleted.', 'info')
    return redirect(url_for('admin_manage_series', series_id=series_id))


@app.route('/admin/series/<int:series_id>/status', methods=['POST'])
@login_required
@admin_required
def admin_toggle_series_status(series_id):
    series = Series.query.get_or_404(series_id)
    series.status = 'completed' if series.status == 'ongoing' else 'ongoing'
    db.session.commit()
    status = 'completed' if series.status == 'completed' else 'ongoing'
    flash(f'Series marked as {status}.', 'success')
    return redirect(url_for('admin_series'))


@app.route('/admin/series/<int:series_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_series(series_id):
    series = Series.query.get_or_404(series_id)
    db.session.delete(series)
    db.session.commit()
    flash('Series deleted.', 'info')
    return redirect(url_for('admin_series'))


# ========== SERVE UPLOADS ==========
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found(error):
    return render_template('partials/404.html'), 404


@app.errorhandler(403)
def forbidden(error):
    flash('You do not have permission to access this page.', 'error')
    return redirect(url_for('index'))


# ========== INIT ==========
def create_admin():
    """Create default admin user if none exists"""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@tupple.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Default admin created: admin/admin123')


@app.cli.command('init-db')
def init_db_command():
    with app.app_context():
        db.create_all()
        init_categories()
        create_admin()
        create_default_images()
        print('Database initialized.')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_categories()
        create_admin()
        create_default_images()
    app.run(debug=True, host='0.0.0.0', port=5000)