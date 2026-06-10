# Tupple - Movies & Anime Streaming Platform

A full-featured streaming and download platform for movies, series, and anime built with Flask.

## Features

### For Users
- Browse movies and series by category (Action, Sci-Fi, Horror, Anime, Drama, Comedy, etc.)
- Watch videos via YouTube embed, external links, or direct file upload
- Download movies and episodes
- Create and manage personal playlists
- Like and comment on content
- Track watch history
- Search with category and type filters

### For Admins
- Dashboard with statistics (users, movies, series, views)
- User management (view, ban/unban, delete users)
- Post movies with cover image, description, and video source (upload/YouTube/external)
- Create and manage series with seasons and episodes
- Mark series as completed or ongoing
- Delete content (movies, series, seasons, episodes)


## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
cd /mnt/agents/output/app
python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
```

3. Run the application:
```bash
python app.py
```

4. Open in browser: http://localhost:5000

## Project Structure

```
app/
├── app.py                  # Main Flask application
├── models.py               # Database models
├── forms.py                # WTForms
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── static/
│   ├── css/style.css       # Main stylesheet
│   ├── js/app.js           # Main JavaScript
│   ├── js/detail.js        # Detail page JavaScript
│   └── uploads/            # Uploaded files
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Homepage
│   ├── *.html              # Other pages
│   ├── admin/              # Admin templates
│   ├── user/               # User dashboard templates
│   └── partials/           # Reusable components
```

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **WebGL**: FBM Fluid Simulation background
- **Auth**: Flask-Login with session-based authentication
- **Forms**: Flask-WTF with CSRF protection
