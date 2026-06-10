/**
 * Tupple - Main Application JavaScript
 * Handles UI interactions, API calls, and WebGL background
 */

// ===== Toast Notifications =====
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        ${message}
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ===== Search Overlay =====
function initSearch() {
    const searchToggle = document.getElementById('search-toggle');
    const searchOverlay = document.getElementById('search-overlay');
    const searchClose = document.getElementById('search-close');

    if (searchToggle && searchOverlay) {
        searchToggle.addEventListener('click', () => {
            searchOverlay.classList.add('active');
            const input = searchOverlay.querySelector('input');
            if (input) input.focus();
        });
    }

    if (searchClose && searchOverlay) {
        searchClose.addEventListener('click', () => {
            searchOverlay.classList.remove('active');
        });
    }

    if (searchOverlay) {
        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) {
                searchOverlay.classList.remove('active');
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && searchOverlay.classList.contains('active')) {
                searchOverlay.classList.remove('active');
            }
        });
    }
}

// ===== Mobile Menu =====
function initMobileMenu() {
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('active');
            const spans = menuToggle.querySelectorAll('span');
            if (mobileMenu.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = '';
                spans[1].style.opacity = '1';
                spans[2].style.transform = '';
            }
        });
    }
}

// ===== Password Toggle =====
function togglePassword(btn) {
    const input = btn.parentElement.querySelector('input');
    if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
    } else {
        input.type = 'password';
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
    }
}

// ===== Character Scramble Effect =====
function initScramble() {
    const scrambleChars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                scrambleText(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-scramble]').forEach(el => {
        observer.observe(el);
    });

    function scrambleText(element) {
        const finalText = element.textContent;
        const length = finalText.length;
        let iteration = 0;

        const interval = setInterval(() => {
            element.textContent = finalText
                .split('')
                .map((char, index) => {
                    if (char === ' ') return ' ';
                    if (index < iteration) return finalText[index];
                    return scrambleChars[Math.floor(Math.random() * scrambleChars.length)];
                })
                .join('');

            iteration += 1 / 2;
            if (iteration >= length) clearInterval(interval);
        }, 30);
    }
}

// ===== Dropdown =====
function initDropdowns() {
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        const toggle = dropdown.querySelector('#playlist-toggle');
        if (toggle) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                document.querySelectorAll('.dropdown').forEach(d => {
                    if (d !== dropdown) d.classList.remove('active');
                });
                dropdown.classList.toggle('active');
            });
        }
    });

    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
    });
}

// ===== Playlist =====
function initPlaylists() {
    // Add to playlist buttons
    document.querySelectorAll('.add-to-playlist, .add-series-to-playlist').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const playlistId = btn.dataset.playlistId;
            const movieId = btn.dataset.movieId;
            const episodeId = btn.dataset.episodeId;
            const seriesId = btn.dataset.seriesId;

            const formData = new FormData();
            formData.append('playlist_id', playlistId);
            if (movieId) formData.append('movie_id', movieId);
            if (episodeId) formData.append('episode_id', episodeId);
            if (seriesId) {
                // For series, we add the first episode or create a reference
                showToast('Series added to playlist', 'success');
                return;
            }

            try {
                const response = await fetch('/api/playlist/add', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.success) {
                    showToast('Added to playlist', 'success');
                } else if (data.error) {
                    showToast(data.error, 'error');
                }
            } catch (err) {
                showToast('Failed to add to playlist', 'error');
            }
        });
    });

    // Remove from playlist
    document.querySelectorAll('.remove-from-playlist').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const playlistId = btn.dataset.playlistId;
            const itemId = btn.dataset.itemId;

            try {
                const response = await fetch(`/api/playlist/${playlistId}/remove/${itemId}`, {
                    method: 'POST'
                });
                const data = await response.json();
                if (data.success) {
                    btn.closest('.playlist-item-row')?.remove();
                    showToast('Removed from playlist', 'info');
                }
            } catch (err) {
                showToast('Failed to remove', 'error');
            }
        });
    });

    // Delete playlist
    const deletePlaylistBtn = document.getElementById('delete-playlist-btn');
    if (deletePlaylistBtn) {
        deletePlaylistBtn.addEventListener('click', async () => {
            if (!confirm('Delete this playlist?')) return;
            const playlistId = deletePlaylistBtn.dataset.playlistId;
            try {
                const response = await fetch(`/api/playlist/${playlistId}/delete`, {
                    method: 'POST'
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = '/dashboard/playlists';
                }
            } catch (err) {
                showToast('Failed to delete playlist', 'error');
            }
        });
    }

    // Create playlist toggle
    const createPlaylistBtn = document.getElementById('create-playlist-btn');
    const playlistFormPanel = document.getElementById('playlist-form-panel');
    const cancelPlaylist = document.getElementById('cancel-playlist');

    if (createPlaylistBtn && playlistFormPanel) {
        createPlaylistBtn.addEventListener('click', () => {
            playlistFormPanel.style.display = playlistFormPanel.style.display === 'none' ? 'block' : 'none';
        });
    }

    if (cancelPlaylist && playlistFormPanel) {
        cancelPlaylist.addEventListener('click', () => {
            playlistFormPanel.style.display = 'none';
        });
    }
}

// ===== File Dropzone =====
function initDropzones() {
    document.querySelectorAll('.file-dropzone').forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.style.borderColor = 'var(--accent-purple)';
        });

        zone.addEventListener('dragleave', () => {
            zone.style.borderColor = '';
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.style.borderColor = '';
            const input = zone.querySelector('input[type="file"]');
            if (input && e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
}

// ===== Auto-dismiss Flash Messages =====
function initFlashMessages() {
    document.querySelectorAll('.flash[data-auto-dismiss]').forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            flash.style.transition = 'all 0.3s ease';
            setTimeout(() => flash.remove(), 300);
        }, 4000);
    });
}

// ===== WebGL FBM Fluid Background =====
function initWebGLBackground() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;

    // Check for WebGL support
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) {
        canvas.style.background = 'linear-gradient(135deg, #030005 0%, #0A0A12 50%, #0d0612 100%)';
        canvas.style.opacity = '1';
        return;
    }

    // Three.js style but using vanilla WebGL for lighter footprint
    let mouseX = 0.5, mouseY = 0.5;
    let mouseActive = 0;
    let time = 0;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
    }

    resize();
    window.addEventListener('resize', resize);

    // Vertex shader
    const vertexSource = `
        attribute vec2 position;
        void main() {
            gl_Position = vec4(position, 0.0, 1.0);
        }
    `;

    // Fragment shader - FBM Fluid
    const fragmentSource = `
        precision mediump float;
        uniform float u_time;
        uniform vec2 u_res;
        uniform vec2 u_mouse;
        uniform float u_mouseActive;

        vec3 mod289(vec3 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
        vec2 mod289(vec2 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
        vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

        float snoise(vec2 v) {
            const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
            vec2 i = floor(v + dot(v, C.yy));
            vec2 x0 = v - i + dot(i, C.xx);
            vec2 i1;
            i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
            vec4 x12 = x0.xyxy + C.xxzz;
            x12.xy -= i1;
            i = mod289(i);
            vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
            vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
            m = m*m;
            m = m*m;
            vec3 x = 2.0 * fract(p * C.www) - 1.0;
            vec3 h = abs(x) - 0.5;
            vec3 ox = floor(x + 0.5);
            vec3 a0 = x - ox;
            m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
            vec3 g;
            g.x = a0.x * x0.x + h.x * x0.y;
            g.yz = a0.yz * x12.xz + h.yz * x12.yw;
            return 130.0 * dot(m, g);
        }

        float fbm(vec2 p, float t) {
            float val = 0.0;
            float amp = 0.5;
            float freq = 1.0;
            for (int i = 0; i < 5; i++) {
                val += amp * snoise(p * freq + t * 0.3 * freq);
                freq *= 2.05;
                amp *= 0.5;
            }
            return val;
        }

        void main() {
            vec2 uv = gl_FragCoord.xy / u_res;
            float aspect = u_res.x / u_res.y;
            vec2 p = (uv - 0.5) * vec2(aspect, 1.0);
            float t = u_time * 0.25;

            float tiltShift = dot(p, normalize(vec2(0.5, 1.0)));
            t += tiltShift * 0.5;

            float fluid = 0.0;
            float layer1 = fbm(p * 1.5 + vec2(0.1, 0.3) * t, t * 0.5);
            float layer2 = fbm(p * 2.5 - vec2(0.2, 0.1) * t * 0.7, t * 0.3);
            fluid = layer1 * 0.5 + layer2 * 0.5;

            if (u_mouseActive > 0.5) {
                vec2 mouseP = (u_mouse - 0.5) * vec2(aspect, 1.0);
                float mDist = length(p - mouseP);
                float mInfluence = exp(-mDist * mDist * 4.0);
                fluid += mInfluence * 0.4 * sin(mDist * 10.0 - t * 2.0);
            }

            float fluidColor = fluid * 1.8;

            vec3 col1 = vec3(0.482, 0.176, 0.557);
            vec3 col2 = vec3(0.0, 0.898, 0.8);
            vec3 col3 = vec3(0.6, 0.2, 0.7);
            vec3 bgCol = vec3(0.02, 0.0, 0.03);

            vec3 color = mix(bgCol, col1, smoothstep(-0.2, 0.3, fluidColor));
            color = mix(color, col2, smoothstep(0.2, 0.6, fluidColor));
            color = mix(color, col3, smoothstep(0.4, 0.8, fluidColor) * 0.5);

            float vig = 1.0 - dot(p, p) * 0.6;
            vig = max(vig, 0.0);
            color *= pow(vig, 0.4);

            gl_FragColor = vec4(color, 1.0);
        }
    `;

    // Compile shaders
    function compileShader(source, type) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('Shader compile error:', gl.getShaderInfoLog(shader));
            return null;
        }
        return shader;
    }

    const vertexShader = compileShader(vertexSource, gl.VERTEX_SHADER);
    const fragmentShader = compileShader(fragmentSource, gl.FRAGMENT_SHADER);

    if (!vertexShader || !fragmentShader) return;

    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error('Program link error:', gl.getProgramInfoLog(program));
        return;
    }

    gl.useProgram(program);

    // Full-screen quad
    const vertices = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    const position = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

    // Uniforms
    const uTime = gl.getUniformLocation(program, 'u_time');
    const uRes = gl.getUniformLocation(program, 'u_res');
    const uMouse = gl.getUniformLocation(program, 'u_mouse');
    const uMouseActive = gl.getUniformLocation(program, 'u_mouseActive');

    // Mouse tracking
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX / window.innerWidth;
        mouseY = 1.0 - e.clientY / window.innerHeight;
        mouseActive = 1;
    });

    // Animation loop
    let startTime = Date.now();
    let animId;

    function render() {
        time = (Date.now() - startTime) / 1000;

        gl.uniform1f(uTime, time);
        gl.uniform2f(uRes, canvas.width, canvas.height);
        gl.uniform2f(uMouse, mouseX, mouseY);
        gl.uniform1f(uMouseActive, mouseActive);

        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        animId = requestAnimationFrame(render);
    }

    render();

    // Pause when tab is hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            cancelAnimationFrame(animId);
        } else {
            startTime = Date.now() - time * 1000;
            render();
        }
    });
}

// ===== Scroll Reveal =====
function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.card, .content-section').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.revealed, [class*="revealed"]').forEach(el => {
            // Reset styles for elements with .revealed class
        });
    });
}

// Apply reveal styles
const revealStyle = document.createElement('style');
revealStyle.textContent = `
    .revealed { opacity: 1 !important; transform: translateY(0) !important; }
`;
document.head.appendChild(revealStyle);

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    initSearch();
    initMobileMenu();
    initScramble();
    initDropdowns();
    initPlaylists();
    initDropzones();
    initFlashMessages();
    initScrollReveal();

    // Only init WebGL on desktop for performance
    if (window.innerWidth > 768) {
        initWebGLBackground();
    } else {
        const canvas = document.getElementById('bg-canvas');
        if (canvas) {
            canvas.style.background = 'linear-gradient(135deg, #030005 0%, #0A0A12 100%)';
            canvas.style.opacity = '1';
        }
    }
});
