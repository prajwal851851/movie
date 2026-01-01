// ===================================
// StreamFlix - JavaScript Application
// ===================================

// Configuration
const API_BASE = '/api';
const ITEMS_PER_PAGE = 12;

// State Management
const state = {
    currentPage: 'home',
    currentProfile: { name: 'John', avatar: 'J' },
    allMovies: [],
    allSeries: [],
    currentMovieOffset: 0,
    currentSeriesOffset: 0,
    hasMoreMovies: true,
    hasMoreSeries: true,
    currentSearch: '',
    currentYear: '',
    currentSource: '',
    currentMovie: null,
    darkMode: true
};

// ===================================
// Initialization
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    loadProfileFromStorage();
    applyDarkMode();
    navigateTo('home');
    setupEventListeners();
}

function setupEventListeners() {
    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.profile-dropdown')) {
            closeProfileDropdown();
        }
    });
}

// ===================================
// Profile Management
// ===================================

function loadProfileFromStorage() {
    const savedProfile = localStorage.getItem('streamflix_profile');
    if (savedProfile) {
        state.currentProfile = JSON.parse(savedProfile);
        updateProfileDisplay();
    }
}

function saveProfileToStorage() {
    localStorage.setItem('streamflix_profile', JSON.stringify(state.currentProfile));
}

function updateProfileDisplay() {
    const profileBtn = document.querySelector('.profile-btn');
    if (profileBtn) {
        const avatar = profileBtn.querySelector('.profile-avatar');
        const name = profileBtn.querySelector('.profile-name');
        if (avatar) avatar.textContent = state.currentProfile.avatar;
        if (name) name.textContent = state.currentProfile.name;
    }
}

function toggleProfileDropdown() {
    const menu = document.getElementById('profile-dropdown-menu');
    if (menu) {
        menu.classList.toggle('show');
    }
}

function closeProfileDropdown() {
    const menu = document.getElementById('profile-dropdown-menu');
    if (menu) {
        menu.classList.remove('show');
    }
}

function switchProfile(name, avatar) {
    state.currentProfile = { name, avatar };
    saveProfileToStorage();
    updateProfileDisplay();
    closeProfileDropdown();

    // Update active state in dropdown
    document.querySelectorAll('.profile-option').forEach(option => {
        option.classList.remove('active');
    });
    event.target.closest('.profile-option').classList.add('active');
}

function addProfile() {
    alert('Add Profile functionality - Coming soon!');
    closeProfileDropdown();
}

// ===================================
// Dark Mode
// ===================================

function toggleDarkMode() {
    state.darkMode = !state.darkMode;
    applyDarkMode();
    localStorage.setItem('streamflix_darkmode', state.darkMode);
}

function applyDarkMode() {
    const toggle = document.getElementById('dark-mode-toggle');
    if (toggle) {
        toggle.checked = state.darkMode;
    }
    // Dark mode is default, so we don't need to apply any classes
}

// ===================================
// Navigation
// ===================================

function navigateTo(page) {
    state.currentPage = page;

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });

    // Close profile dropdown
    closeProfileDropdown();

    // Load page content
    loadPageContent(page);
}

function loadPageContent(page) {
    const contentArea = document.getElementById('content-area');

    switch (page) {
        case 'home':
            loadHomePage();
            break;
        case 'movies':
            loadMoviesPage();
            break;
        case 'series':
            loadSeriesPage();
            break;
        case 'shuffle':
            loadShufflePage();
            break;
        case 'trending':
            loadTrendingPage();
            break;
        case 'categories':
            loadCategoriesPage();
            break;
        case 'kids':
            loadKidsPage();
            break;
        case 'mylist':
            loadMyListPage();
            break;
        case 'history':
            loadHistoryPage();
            break;
        case 'favorites':
            loadFavoritesPage();
            break;
        case 'downloads':
            loadDownloadsPage();
            break;
        case 'settings':
            loadSettingsPage();
            break;
        default:
            loadHomePage();
    }
}

// ===================================
// Page Loaders
// ===================================

function loadHomePage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Welcome back, ${state.currentProfile.name}!</h1>
            <p class="page-subtitle">Continue watching or discover something new</p>
        </div>
        <div id="movie-list" class="movie-grid">
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p class="loading-text">Loading movies...</p>
            </div>
        </div>
    `;

    fetchAndDisplayMovies();
}

function loadMoviesPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Movies</h1>
            <p class="page-subtitle">Browse our collection of movies</p>
        </div>
        <div id="movie-list" class="movie-grid">
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p class="loading-text">Loading movies...</p>
            </div>
        </div>
    `;

    fetchAndDisplayMovies();
}

function loadSeriesPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">TV Shows</h1>
            <p class="page-subtitle">Browse our collection of TV shows</p>
        </div>
        <div id="series-list" class="movie-grid">
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p class="loading-text">Loading TV shows...</p>
            </div>
        </div>
    `;

    fetchAndDisplaySeries();
}

function loadShufflePage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="shuffle-container">
            <svg class="shuffle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="16 3 21 3 21 8"></polyline>
                <line x1="4" y1="20" x2="21" y2="3"></line>
                <polyline points="21 16 21 21 16 21"></polyline>
                <line x1="15" y1="15" x2="21" y2="21"></line>
                <line x1="4" y1="4" x2="9" y2="9"></line>
            </svg>
            <h1 class="shuffle-title">Random Pick</h1>
            <p class="shuffle-subtitle">Can't decide what to watch? Let us pick for you!</p>
            <p class="shuffle-message" id="shuffle-message">No movies to shuffle yet</p>
            <div class="shuffle-actions">
                <button class="btn-shuffle" onclick="shuffleContent()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="16 3 21 3 21 8"></polyline>
                        <line x1="4" y1="20" x2="21" y2="3"></line>
                    </svg>
                    <span>Shuffle Again</span>
                </button>
                <button class="btn-watch-now" onclick="watchShuffled()">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                    <span>Watch Now</span>
                </button>
            </div>
        </div>
    `;

    // Load movies for shuffling
    fetchMoviesForShuffle();
}

function loadTrendingPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Trending</h1>
            <p class="page-subtitle">What's popular right now</p>
        </div>
        <div id="movie-list" class="movie-grid">
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p class="loading-text">Loading trending content...</p>
            </div>
        </div>
    `;

    fetchAndDisplayMovies();
}

function loadCategoriesPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Categories</h1>
            <p class="page-subtitle">Browse by genre</p>
        </div>
        <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
            Categories feature coming soon!
        </p>
    `;
}

function loadKidsPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">For Kids</h1>
            <p class="page-subtitle">Family-friendly content</p>
        </div>
        <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
            Kids content coming soon!
        </p>
    `;
}

function loadMyListPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">My List</h1>
            <p class="page-subtitle">Your saved content</p>
        </div>
        <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
            Your list is empty. Add some content to get started!
        </p>
    `;
}

function loadHistoryPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Watch History</h1>
            <p class="page-subtitle">Recently watched</p>
        </div>
        <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
            No watch history yet. Start watching to see your history here!
        </p>
    `;
}

function loadFavoritesPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Favorites</h1>
            <p class="page-subtitle">Your favorite content</p>
        </div>
        <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
            No favorites yet. Mark content as favorite to see them here!
        </p>
    `;
}

function loadDownloadsPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Downloads</h1>
            <p class="page-subtitle">Your downloaded content</p>
        </div>
        <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
            No downloads yet. Download content to watch offline!
        </p>
    `;
}

function loadSettingsPage() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="settings-container">
            <div class="settings-header">
                <div class="settings-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M12 1v6m0 6v6m5.2-13.2l-4.2 4.2m0 6l-4.2 4.2M23 12h-6m-6 0H1m18.2 5.2l-4.2-4.2m-6 0l-4.2 4.2"></path>
                    </svg>
                </div>
                <div>
                    <h1 class="page-title">Settings</h1>
                    <p class="page-subtitle">Manage your account and preferences</p>
                </div>
            </div>

            <!-- Account Section -->
            <div class="settings-section">
                <div class="section-header">
                    <h3 class="section-title">Account</h3>
                    <p class="section-description">Manage your account settings</p>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Profile Settings</h4>
                        <p>Edit your profile information</p>
                    </div>
                    <div class="setting-control">
                        <button class="btn-manage">Manage</button>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Subscription</h4>
                        <p>Premium Plan • $15.99/month</p>
                    </div>
                    <div class="setting-control">
                        <button class="btn-change-plan">Change Plan</button>
                    </div>
                </div>
            </div>

            <!-- Appearance Section -->
            <div class="settings-section">
                <div class="section-header">
                    <h3 class="section-title">Appearance</h3>
                    <p class="section-description">Customize how StreamFlix looks</p>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Dark Mode</h4>
                        <p>Use dark theme</p>
                    </div>
                    <div class="setting-control">
                        <div class="toggle-switch">
                            <input type="checkbox" id="settings-dark-mode" checked onchange="toggleDarkMode()">
                            <label for="settings-dark-mode"></label>
                        </div>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Language</h4>
                        <p>Choose your preferred language</p>
                    </div>
                    <div class="setting-control">
                        <select>
                            <option>English</option>
                            <option>Spanish</option>
                            <option>French</option>
                            <option>German</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Playback Section -->
            <div class="settings-section">
                <div class="section-header">
                    <h3 class="section-title">Playback</h3>
                    <p class="section-description">Control how content plays</p>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Default Quality</h4>
                        <p>Choose default video quality</p>
                    </div>
                    <div class="setting-control">
                        <select>
                            <option>Auto</option>
                            <option>1080p</option>
                            <option>720p</option>
                            <option>480p</option>
                        </select>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Autoplay Next Episode</h4>
                        <p>Automatically play the next episode</p>
                    </div>
                    <div class="setting-control">
                        <div class="toggle-switch">
                            <input type="checkbox" id="autoplay-toggle" checked>
                            <label for="autoplay-toggle"></label>
                        </div>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Content Previews</h4>
                        <p>Show previews when browsing</p>
                    </div>
                    <div class="setting-control">
                        <div class="toggle-switch">
                            <input type="checkbox" id="previews-toggle" checked>
                            <label for="previews-toggle"></label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Privacy & Security Section -->
            <div class="settings-section">
                <div class="section-header">
                    <h3 class="section-title">Privacy & Security</h3>
                    <p class="section-description">Manage your privacy settings</p>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Watch History</h4>
                        <p>Track what you watch</p>
                    </div>
                    <div class="setting-control">
                        <div class="toggle-switch">
                            <input type="checkbox" id="history-toggle" checked>
                            <label for="history-toggle"></label>
                        </div>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Personalized Recommendations</h4>
                        <p>Get content suggestions based on your activity</p>
                    </div>
                    <div class="setting-control">
                        <div class="toggle-switch">
                            <input type="checkbox" id="recommendations-toggle" checked>
                            <label for="recommendations-toggle"></label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Danger Zone -->
            <div class="settings-section danger-zone">
                <div class="section-header">
                    <h3 class="section-title">Danger Zone</h3>
                    <p class="section-description">Irreversible actions</p>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Clear Watch History</h4>
                        <p>Permanently delete all watch history</p>
                    </div>
                    <div class="setting-control">
                        <button class="btn-danger">Clear History</button>
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-info">
                        <h4>Delete Account</h4>
                        <p>Permanently delete your account and all data</p>
                    </div>
                    <div class="setting-control">
                        <button class="btn-danger">Delete Account</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ===================================
// API Calls
// ===================================

async function fetchAndDisplayMovies() {
    try {
        const response = await fetch(`${API_BASE}/movies/?limit=${ITEMS_PER_PAGE}&offset=0`);
        const data = await response.json();

        state.allMovies = data.results || [];
        displayMovies(state.allMovies);
    } catch (error) {
        console.error('Error fetching movies:', error);
        document.getElementById('movie-list').innerHTML = `
            <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                Error loading movies. Please try again later.
            </p>
        `;
    }
}

async function fetchAndDisplaySeries() {
    try {
        const response = await fetch(`${API_BASE}/series/?limit=${ITEMS_PER_PAGE}&offset=0`);
        const data = await response.json();

        state.allSeries = data.results || [];
        displaySeries(state.allSeries);
    } catch (error) {
        console.error('Error fetching series:', error);
        document.getElementById('series-list').innerHTML = `
            <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                Error loading TV shows. Please try again later.
            </p>
        `;
    }
}

async function fetchMoviesForShuffle() {
    try {
        const response = await fetch(`${API_BASE}/movies/?limit=100&offset=0`);
        const data = await response.json();
        state.allMovies = data.results || [];

        if (state.allMovies.length > 0) {
            document.getElementById('shuffle-message').textContent =
                `${state.allMovies.length} movies available for shuffling`;
        }
    } catch (error) {
        console.error('Error fetching movies for shuffle:', error);
    }
}

// ===================================
// Display Functions
// ===================================

function displayMovies(movies) {
    const movieList = document.getElementById('movie-list');

    if (!movies || movies.length === 0) {
        movieList.innerHTML = `
            <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary); grid-column: 1 / -1;">
                No movies found.
            </p>
        `;
        return;
    }

    movieList.innerHTML = movies.map(movie => `
        <div class="movie-card" onclick='openWatchModal(${JSON.stringify(movie).replace(/'/g, "&apos;")})'>
            <img src="${movie.poster_url || '/static/images/placeholder.jpg'}" 
                 alt="${movie.title}" 
                 class="movie-poster"
                 onerror="this.src='/static/images/placeholder.jpg'">
            <div class="movie-source">${getSourceName(movie.site)}</div>
            <div class="movie-info">
                <h3 class="movie-title">${movie.title}</h3>
                <div class="movie-meta">
                    <span class="movie-year">${movie.release_year || 'N/A'}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function displaySeries(series) {
    const seriesList = document.getElementById('series-list');

    if (!series || series.length === 0) {
        seriesList.innerHTML = `
            <p style="text-align: center; padding: 60px 20px; color: var(--text-secondary); grid-column: 1 / -1;">
                No TV shows found.
            </p>
        `;
        return;
    }

    seriesList.innerHTML = series.map(show => `
        <div class="movie-card">
            <img src="${show.poster_url || '/static/images/placeholder.jpg'}" 
                 alt="${show.name}" 
                 class="movie-poster"
                 onerror="this.src='/static/images/placeholder.jpg'">
            <div class="movie-source">${getSourceName(show.site)}</div>
            <div class="movie-info">
                <h3 class="movie-title">${show.name}</h3>
            </div>
        </div>
    `).join('');
}

function getSourceName(site) {
    const sourceMap = {
        '1flix.to': '1Flix',
        'goojara.to': 'Goojara',
        'sflix.ps': 'Sflix',
        'vidsrc': 'VidSrc'
    };
    return sourceMap[site] || site;
}

// ===================================
// Movie Player Modal
// ===================================

function openWatchModal(movie) {
    state.currentMovie = movie;
    const modal = document.getElementById('watchModal');

    // Update movie details
    document.getElementById('modal-title').textContent = movie.title;
    document.getElementById('modal-synopsis').textContent = movie.synopsis || 'No synopsis available.';

    // Display available links
    displayAvailableLinks(movie);

    // Show modal
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';

    // Load first available link
    if (movie.streaming_links && movie.streaming_links.length > 0) {
        loadStreamingLink(movie.streaming_links[0], 0);
    }
}

function closeWatchModal() {
    const modal = document.getElementById('watchModal');
    modal.classList.remove('show');
    document.body.style.overflow = '';

    // Clear player
    const player = document.getElementById('embed-player');
    player.src = '';
}

function displayAvailableLinks(movie) {
    const linksList = document.getElementById('available-links-list');

    if (!movie.streaming_links || movie.streaming_links.length === 0) {
        linksList.innerHTML = `
            <p style="text-align: center; padding: 20px; color: var(--text-secondary);">
                No streaming links available
            </p>
        `;
        return;
    }

    linksList.innerHTML = movie.streaming_links.map((link, index) => `
        <div class="link-item ${index === 0 ? 'active' : ''}" onclick="loadStreamingLink(${JSON.stringify(link).replace(/'/g, "&apos;")}, ${index})">
            <div class="link-header">
                <span class="link-name">${getSourceName(link.site || movie.site)}</span>
                <div class="link-badges">
                    <span class="badge badge-quality">720p</span>
                    <span class="badge badge-language">EN</span>
                </div>
            </div>
            <div class="link-url">${link.url}</div>
        </div>
    `).join('');
}

function loadStreamingLink(link, index) {
    const player = document.getElementById('embed-player');
    const loading = document.getElementById('iframe-loading');

    // Show loading
    loading.style.display = 'flex';

    // Update active link
    document.querySelectorAll('.link-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });

    // Load URL
    player.src = link.url;

    // Hide loading after delay
    setTimeout(() => {
        loading.style.display = 'none';
    }, 2000);
}

function refreshLinks() {
    if (state.currentMovie) {
        displayAvailableLinks(state.currentMovie);
    }
}

// ===================================
// Shuffle Feature
// ===================================

function shuffleContent() {
    if (state.allMovies.length === 0) {
        alert('No movies available to shuffle');
        return;
    }

    const randomIndex = Math.floor(Math.random() * state.allMovies.length);
    const randomMovie = state.allMovies[randomIndex];

    document.getElementById('shuffle-message').innerHTML = `
        <strong style="color: var(--text-primary); font-size: 20px;">${randomMovie.title}</strong><br>
        <span style="color: var(--text-secondary);">${randomMovie.release_year || 'N/A'}</span>
    `;

    state.currentMovie = randomMovie;
}

function watchShuffled() {
    if (state.currentMovie) {
        openWatchModal(state.currentMovie);
    } else {
        alert('Please shuffle first to select a movie');
    }
}

// ===================================
// Search
// ===================================

function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
}

function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();

    if (!query) return;

    state.currentSearch = query;

    // Filter movies based on search
    const filteredMovies = state.allMovies.filter(movie =>
        movie.title.toLowerCase().includes(query.toLowerCase())
    );

    displayMovies(filteredMovies);
}

// ===================================
// Sidebar Toggle
// ===================================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
}

// ===================================
// Utility Functions
// ===================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

console.log('StreamFlix App Loaded Successfully');
