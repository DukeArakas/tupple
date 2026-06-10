/**
 * Tupple - Detail Page JavaScript
 * Handles likes, comments, video player, and playlist interactions
 */

// ===== Like Button =====
function initLikeButton() {
    const likeBtn = document.getElementById('like-btn');
    if (!likeBtn) return;

    likeBtn.addEventListener('click', async () => {
        const movieId = likeBtn.dataset.movieId;
        const episodeId = likeBtn.dataset.episodeId;
        let url;

        if (movieId) {
            url = `/api/movie/${movieId}/like`;
        } else if (episodeId) {
            url = `/api/episode/${episodeId}/like`;
        } else {
            return;
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.status === 401) {
                window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
                return;
            }

            const data = await response.json();
            if (data.liked !== undefined) {
                const countEl = document.getElementById('like-count');
                const svg = likeBtn.querySelector('svg');

                if (countEl) countEl.textContent = data.count;

                if (data.liked) {
                    likeBtn.dataset.liked = 'true';
                    svg.setAttribute('fill', 'currentColor');
                } else {
                    likeBtn.dataset.liked = 'false';
                    svg.setAttribute('fill', 'none');
                }
            }
        } catch (err) {
            console.error('Like error:', err);
        }
    });
}

// ===== Comment Form =====
function initCommentForm() {
    const commentForm = document.getElementById('comment-form');
    if (!commentForm) return;

    commentForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const movieId = commentForm.dataset.movieId;
        const episodeId = commentForm.dataset.episodeId;
        const contentInput = document.getElementById('comment-content');
        const content = contentInput.value.trim();

        if (!content) return;

        let url;
        if (movieId) {
            url = `/api/movie/${movieId}/comment`;
        } else if (episodeId) {
            url = `/api/episode/${episodeId}/comment`;
        } else {
            return;
        }

        const formData = new FormData();
        formData.append('content', content);
        // Add CSRF token if present
        const csrfToken = document.querySelector('input[name="csrf_token"]');
        if (csrfToken) formData.append('csrf_token', csrfToken.value);

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.status === 401) {
                window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
                return;
            }

            const data = await response.json();
            if (data.id) {
                // Add comment to list
                const commentsList = document.getElementById('comments-list');
                const emptyMsg = document.getElementById('comments-empty');
                if (emptyMsg) emptyMsg.remove();

                const commentEl = document.createElement('div');
                commentEl.className = 'comment';
                commentEl.dataset.commentId = data.id;
                commentEl.innerHTML = `
                    <img src="${data.avatar}" alt="${data.author}" class="comment-avatar">
                    <div class="comment-body">
                        <div class="comment-header">
                            <span class="comment-author">${data.author}</span>
                            <span class="comment-time">${data.time_ago}</span>
                        </div>
                        <p class="comment-text">${escapeHtml(data.content)}</p>
                    </div>
                `;

                commentsList.insertBefore(commentEl, commentsList.firstChild);
                contentInput.value = '';

                // Update count
                const countEl = document.getElementById('comment-count');
                if (countEl) countEl.textContent = data.count;
            }
        } catch (err) {
            console.error('Comment error:', err);
        }
    });
}

// ===== Video Player Enhancements =====
function initVideoPlayer() {
    const video = document.querySelector('.video-player');
    if (!video) return;

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Only trigger if not in an input/textarea
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        switch (e.key) {
            case ' ':
                e.preventDefault();
                if (video.paused) video.play();
                else video.pause();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                video.currentTime = Math.max(0, video.currentTime - 10);
                break;
            case 'ArrowRight':
                e.preventDefault();
                video.currentTime = Math.min(video.duration, video.currentTime + 10);
                break;
            case 'ArrowUp':
                e.preventDefault();
                video.volume = Math.min(1, video.volume + 0.1);
                break;
            case 'ArrowDown':
                e.preventDefault();
                video.volume = Math.max(0, video.volume - 0.1);
                break;
            case 'f':
                e.preventDefault();
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                } else {
                    video.requestFullscreen();
                }
                break;
        }
    });

    // Save watch progress
    let progressInterval;
    video.addEventListener('play', () => {
        progressInterval = setInterval(saveProgress, 10000); // Save every 10 seconds
    });

    video.addEventListener('pause', () => {
        clearInterval(progressInterval);
        saveProgress();
    });

    video.addEventListener('ended', () => {
        clearInterval(progressInterval);
        saveProgress(true);
    });

    function saveProgress(completed = false) {
        if (!video.duration) return;

        const progress = completed ? 100 : Math.round((video.currentTime / video.duration) * 100);
        const movieId = document.querySelector('[data-movie-id]')?.dataset.movieId;
        const episodeId = document.querySelector('[data-episode-id]')?.dataset.episodeId;

        const payload = { progress };
        if (movieId) payload.movie_id = parseInt(movieId);
        if (episodeId) payload.episode_id = parseInt(episodeId);

        fetch('/api/watch/progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        }).catch(() => {}); // Silently fail
    }
}

// ===== Playlist Dropdown =====
function initPlaylistDropdown() {
    const toggle = document.getElementById('playlist-toggle');
    const dropdown = document.getElementById('playlist-dropdown');
    if (!toggle || !dropdown) return;

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.parentElement.classList.toggle('active');
    });

    document.addEventListener('click', () => {
        dropdown.parentElement.classList.remove('active');
    });
}

// ===== Utility =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    initLikeButton();
    initCommentForm();
    initVideoPlayer();
    initPlaylistDropdown();
});
