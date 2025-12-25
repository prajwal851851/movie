// Configuration
const API_BASE = '/api';
const ITEMS_PER_PAGE = 12;
const PLAYER_TIMEOUT = 10000; // 10 seconds

// State Management
const state = {
    allMovies: [],
    allSeries: [],
    currentMovieOffset: 0,
    currentSeriesOffset: 0,
    hasMoreMovies: true,
    hasMoreSeries: true,
    isLoading: false,
    displayedMovieIds: new Set(),
    displayedSeriesNames: new Set(),
    currentSearch: '',
    currentYear: '',
    currentSource: '',
    currentContentType: 'movie',
    currentPlayerTimeout: null
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Initialize Application
async function initializeApp() {
    console.log('Initializing Movie Streamer...');
    await loadInitialMovies();
    await populateYearFilter();
    await fetchStats();
}

// Search Functions
function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
}

function performSearch() {
    state.currentSearch = document.getElementById('search-input').value.trim();
    console.log('Searching for:', state.currentSearch);
    resetAndReload();
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    state.currentSearch = '';
    resetAndReload();
}

function filterByYear() {
    state.currentYear = document.getElementById('year-filter').value;
    console.log('Filtering by year:', state.currentYear);
    resetAndReload();
}

function filterBySource() {
    state.currentSource = document.getElementById('source-filter').value;
    console.log('Filtering by source:', state.currentSource);
    resetAndReload();
}

// Page Navigation
function showPage(page) {
    state.currentContentType = page === 'movies' ? 'movie' : 'series';
    
    // Toggle page visibility
    document.getElementById('movies-page').classList.toggle('active', page === 'movies');
    document.getElementById('series-page').classList.toggle('active', page === 'series');
    
    // Toggle button styles
    document.getElementById('movies-nav-btn').classList.toggle('active', page === 'movies');
    document.getElementById('series-nav-btn').classList.toggle('active', page === 'series');
    
    resetAndReload();
}

// Reset and Reload
function resetAndReload() {
    state.currentMovieOffset = 0;
    state.currentSeriesOffset = 0;
    state.hasMoreMovies = true;
    state.hasMoreSeries = true;
    state.displayedMovieIds.clear();
    state.displayedSeriesNames.clear();
    
    document.getElementById('load-more-movies-container').style.display = 'none';
    document.getElementById('load-more-series-container').style.display = 'none';
    
    loadInitialMovies();
}

// Build API URL
function buildApiUrl(base, offset) {
    let url = `${base}?limit=${ITEMS_PER_PAGE}&offset=${offset}&content_type=${state.currentContentType}`;
    if (state.currentSearch) url += `&search=${encodeURIComponent(state.currentSearch)}`;
    if (state.currentYear) url += `&year=${state.currentYear}`;
    if (state.currentSource) url += `&source_site=${state.currentSource}`;
    return url;
}

// Fetch Stats
async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE}/movies/stats/`);
        const stats = await response.json();
        document.getElementById('total-movies').textContent = stats.total_movies || 0;
        document.getElementById('movies-with-links').textContent = stats.movies_with_links || 0;
        document.getElementById('status-indicator').textContent = 'Ready';
    } catch (error) {
        console.error('Error fetching stats:', error);
        document.getElementById('status-indicator').textContent = 'Error';
    }
}

// Populate Year Filter
async function populateYearFilter() {
    try {
        const response = await fetch(`${API_BASE}/movies/years/`);
        const years = await response.json();
        const select = document.getElementById('year-filter');
        select.innerHTML = '<option value="">All Years</option>';
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading years:', error);
    }
}

// Load Initial Movies
async function loadInitialMovies() {
    updateStatus('Loading content...', 'loading');
    
    try {
        const moviesUrl = buildApiUrl(`${API_BASE}/movies/`, 0);
        
        // Temporarily switch to series for series request
        const originalType = state.currentContentType;
        state.currentContentType = 'series';
        const seriesUrl = buildApiUrl(`${API_BASE}/movies/`, 0);
        state.currentContentType = originalType;

        const [moviesData, seriesData] = await Promise.all([
            fetch(moviesUrl).then(r => r.json()),
            fetch(seriesUrl).then(r => r.json())
        ]);

        // Update movies
        state.allMovies = moviesData.results || [];
        state.currentMovieOffset = state.allMovies.length;
        state.hasMoreMovies = moviesData.next !== null;

        // Update series
        state.allSeries = seriesData.results || [];
        state.currentSeriesOffset = state.allSeries.length;
        state.hasMoreSeries = seriesData.next !== null;

        // Display content
        displayMovies(state.allMovies, false);
        displaySeries(state.allSeries, false);

        // Show load more buttons if needed
        if (state.allMovies.length > 0 && state.hasMoreMovies) {
            document.getElementById('load-more-movies-container').style.display = 'block';
        }
        if (state.allSeries.length > 0 && state.hasMoreSeries) {
            document.getElementById('load-more-series-container').style.display = 'block';
        }

        updateStatus('Content loaded successfully', 'success');
        fetchStats();
        
    } catch (error) {
        console.error('Error loading content:', error);
        updateStatus('Error loading content. Please try again.', 'error');
    }
}

// Load More Movies
async function loadMoreMovies() {
    if (!state.hasMoreMovies || state.isLoading) return;
    
    state.isLoading = true;
    const btn = document.getElementById('load-more-movies-btn');
    btn.disabled = true;
    btn.textContent = 'Loading...';
    
    try {
        const url = buildApiUrl(`${API_BASE}/movies/`, state.currentMovieOffset);
        const response = await fetch(url);
        const data = await response.json();
        
        const newMovies = data.results || [];
        
        if (newMovies.length > 0) {
            state.allMovies = state.allMovies.concat(newMovies);
            state.currentMovieOffset += newMovies.length;
            state.hasMoreMovies = data.next !== null;
            
            displayMovies(newMovies, true);
            
            if (!state.hasMoreMovies) {
                document.getElementById('load-more-movies-container').style.display = 'none';
            } else {
                btn.disabled = false;
                btn.textContent = 'Load More Movies';
            }
        } else {
            state.hasMoreMovies = false;
            document.getElementById('load-more-movies-container').style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading more movies:', error);
        btn.disabled = false;
        btn.textContent = 'Load More Movies';
    } finally {
        state.isLoading = false;
    }
}

// Load More Series
async function loadMoreSeries() {
    if (!state.hasMoreSeries || state.isLoading) return;
    
    state.isLoading = true;
    const btn = document.getElementById('load-more-series-btn');
    btn.disabled = true;
    btn.textContent = 'Loading...';
    
    try {
        const originalType = state.currentContentType;
        state.currentContentType = 'series';
        const url = buildApiUrl(`${API_BASE}/movies/`, state.currentSeriesOffset);
        state.currentContentType = originalType;
        
        const response = await fetch(url);
        const data = await response.json();
        
        const newSeries = data.results || [];
        
        if (newSeries.length > 0) {
            state.allSeries = state.allSeries.concat(newSeries);
            state.currentSeriesOffset += newSeries.length;
            state.hasMoreSeries = data.next !== null;
            
            displaySeries(newSeries, true);
            
            if (!state.hasMoreSeries) {
                document.getElementById('load-more-series-container').style.display = 'none';
            } else {
                btn.disabled = false;
                btn.textContent = 'Load More Series';
            }
        } else {
            state.hasMoreSeries = false;
            document.getElementById('load-more-series-container').style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading more series:', error);
        btn.disabled = false;
        btn.textContent = 'Load More Series';
    } finally {
        state.isLoading = false;
    }
}

// Display Movies
function displayMovies(movies, append = false) {
    const list = document.getElementById('movie-list');
    
    if (!append) {
        list.innerHTML = '';
        state.displayedMovieIds.clear();
    }
    
    if (movies.length === 0 && !append) {
        list.innerHTML = '<div class="loading-container"><p>No movies found.</p></div>';
        return;
    }
    
    movies.forEach(movie => {
        if (append && state.displayedMovieIds.has(movie.imdb_id)) return;
        if (!movie.poster_url) return;
        
        state.displayedMovieIds.add(movie.imdb_id);
        
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <img src="${movie.poster_url}" alt="${movie.title}" loading="lazy">
            <div class="movie-source">${getSourceName(movie.source_site)}</div>
            <h3>${movie.title} ${movie.year ? `(${movie.year})` : ''}</h3>
        `;
        card.onclick = () => openWatchModal(movie);
        list.appendChild(card);
    });
}

// Display Series
function displaySeries(seriesArray, append = false) {
    const list = document.getElementById('series-list');
    
    if (!append) {
        list.innerHTML = '';
        state.displayedSeriesNames.clear();
    }
    
    if (seriesArray.length === 0 && !append) {
        list.innerHTML = '<div class="loading-container"><p>No series found.</p></div>';
        return;
    }

    // Group by series name
    const byName = {};
    seriesArray.forEach(series => {
        const name = series.title.replace(/\s*S\d+,?\s*E\d+.*/, '').trim();
        if (!byName[name]) byName[name] = [];
        byName[name].push(series);
    });

    Object.keys(byName).forEach(name => {
        if (append && state.displayedSeriesNames.has(name)) return;
        
        const episodes = byName[name];
        const first = episodes[0];
        
        if (!first.poster_url) return;
        
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <img src="${first.poster_url}" alt="${name}" loading="lazy">
            <div class="movie-source">${getSourceName(first.source_site)}</div>
            <h3>${name}</h3>
            <p style="padding:10px;font-size:0.9em;color:#ccc;">${episodes.length} episode${episodes.length > 1 ? 's' : ''}</p>
        `;
        card.onclick = () => openSeriesModal(name, episodes);
        list.appendChild(card);
        state.displayedSeriesNames.add(name);
    });
}

// Get Source Name
function getSourceName(site) {
    const names = {
        '1flix.to': '1F',
        'goojara.to': 'GJ',
        'sflix.ps': 'SF'
    };
    return names[site] || site;
}

// Open Watch Modal
async function openWatchModal(movie) {
    document.getElementById('modal-title').textContent = `${movie.title} ${movie.year ? `(${movie.year})` : ''}`;
    document.getElementById('modal-synopsis').textContent = movie.synopsis || 'No synopsis available.';
    document.getElementById('server-list').innerHTML = '';
    document.getElementById('embed-player').src = '';
    document.getElementById('player-error').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/watch/${movie.imdb_id}/`);
        const data = await response.json();
        
        const links = data.links.filter(link => link.is_active && link.stream_url);

        if (links.length > 0) {
            // Load first server
            setupPlayer(links[0].stream_url, links[0].server_name || 'Default', 'embed-player', 'iframe-loading');
            
            // Create server list
            links.forEach((link, index) => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#';
                a.id = `srv-${index}`;
                a.innerHTML = `${link.server_name || 'Server'} <span class="server-badge">${link.quality}</span>`;
                a.onclick = (e) => {
                    e.preventDefault();
                    setupPlayer(link.stream_url, link.server_name || 'Server', 'embed-player', 'iframe-loading');
                    document.querySelectorAll('#server-list a').forEach(el => el.classList.remove('active'));
                    a.classList.add('active');
                };
                li.appendChild(a);
                document.getElementById('server-list').appendChild(li);
            });
            
            // Set first server as active
            setTimeout(() => {
                const firstServer = document.getElementById('srv-0');
                if (firstServer) firstServer.classList.add('active');
            }, 100);
            
        } else {
            document.getElementById('server-list').innerHTML = '<li style="color:#888;">⚠️ No working streaming links available</li>';
            document.getElementById('player-error').style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error loading watch data:', error);
        document.getElementById('server-list').innerHTML = '<li style="color:#e50914;">❌ Error loading streaming links</li>';
        document.getElementById('player-error').style.display = 'block';
    }
    
    document.getElementById('watchModal').style.display = "block";
}

// Setup Player
function setupPlayer(url, serverName, playerId, loadingId) {
    console.log(`Setting up player: ${serverName}`, url);
    
    const player = document.getElementById(playerId);
    const loading = document.getElementById(loadingId);
    const errorDiv = playerId === 'embed-player' ? 
        document.getElementById('player-error') : 
        document.getElementById('series-player-error');
    
    // Clear existing timeout
    if (state.currentPlayerTimeout) {
        clearTimeout(state.currentPlayerTimeout);
    }
    
    // Show loading
    loading.style.display = 'flex';
    errorDiv.style.display = 'none';
    player.style.opacity = '0.3';
    
    // Clear current source
    player.src = 'about:blank';
    
    // Set timeout for loading
    state.currentPlayerTimeout = setTimeout(() => {
        loading.style.display = 'none';
        errorDiv.style.display = 'block';
        player.style.opacity = '1';
        console.warn('Player loading timeout');
    }, PLAYER_TIMEOUT);
    
    // Load new source after a brief delay
    setTimeout(() => {
        try {
            player.src = url;
            console.log('Player source set');
        } catch (error) {
            console.error('Error setting player source:', error);
            clearTimeout(state.currentPlayerTimeout);
            loading.style.display = 'none';
            errorDiv.style.display = 'block';
            player.style.opacity = '1';
        }
    }, 300);
    
    // Handle load event
    player.onload = () => {
        console.log('Player loaded successfully');
        clearTimeout(state.currentPlayerTimeout);
        setTimeout(() => {
            loading.style.display = 'none';
            player.style.opacity = '1';
        }, 1000);
    };
    
    // Handle error
    player.onerror = () => {
        console.error('Player error');
        clearTimeout(state.currentPlayerTimeout);
        loading.style.display = 'none';
        errorDiv.style.display = 'block';
        player.style.opacity = '1';
    };
}

// Close Watch Modal
function closeWatchModal() {
    document.getElementById('watchModal').style.display = "none";
    document.getElementById('embed-player').src = 'about:blank';
    if (state.currentPlayerTimeout) {
        clearTimeout(state.currentPlayerTimeout);
    }
}

// Open Series Modal
async function openSeriesModal(name, episodes) {
    document.getElementById('series-modal-title').textContent = name;
    
    // Group by season
    const seasonMap = {};
    episodes.forEach(ep => {
        const match = ep.title.match(/S(\d+),?\s*E(\d+)/);
        if (match) {
            const seasonNum = match[1];
            if (!seasonMap[seasonNum]) seasonMap[seasonNum] = [];
            seasonMap[seasonNum].push({
                episode: ep,
                episodeNum: match[2]
            });
        }
    });
    
    const seasons = Object.keys(seasonMap).sort((a, b) => parseInt(a) - parseInt(b));
    
    // Populate season select
    const seasonSelect = document.getElementById('season-select');
    seasonSelect.innerHTML = '';
    seasons.forEach(season => {
        const option = document.createElement('option');
        option.value = season;
        option.textContent = `Season ${season}`;
        seasonSelect.appendChild(option);
    });
    
    // Store season map globally
    window.currentSeasonMap = seasonMap;
    
    // Update episode select
    updateEpisodeSelect(seasonSelect.value);
    
    // Add event listener
    seasonSelect.onchange = () => updateEpisodeSelect(seasonSelect.value);
    
    // Reset player
    document.getElementById('series-server-list').innerHTML = '';
    document.getElementById('series-embed-player').style.display = 'none';
    document.getElementById('series-embed-player').src = '';
    document.getElementById('series-player-error').style.display = 'none';
    
    document.getElementById('seriesModal').style.display = "block";
}

// Update Episode Select
function updateEpisodeSelect(season) {
    const episodeSelect = document.getElementById('episode-select');
    episodeSelect.innerHTML = '';
    
    const episodes = window.currentSeasonMap[season].sort((a, b) => 
        parseInt(a.episodeNum) - parseInt(b.episodeNum)
    );
    
    episodes.forEach(epData => {
        const option = document.createElement('option');
        option.value = `E${epData.episodeNum}`;
        option.textContent = `Episode ${epData.episodeNum}`;
        option.dataset.episode = JSON.stringify(epData);
        episodeSelect.appendChild(option);
    });
}

// Play Selected Episode
async function playSelectedEpisode() {
    const episodeSelect = document.getElementById('episode-select');
    const selectedOption = episodeSelect.selectedOptions[0];
    
    if (!selectedOption) return;
    
    const epData = JSON.parse(selectedOption.dataset.episode);
    const episode = epData.episode;
    
    try {
        const response = await fetch(`${API_BASE}/watch/${episode.imdb_id}/`);
        const data = await response.json();
        
        const links = data.links.filter(link => link.is_active && link.stream_url);
        const serverList = document.getElementById('series-server-list');
        serverList.innerHTML = '';
        
        if (links.length > 0) {
            // Show player
            document.getElementById('series-embed-player').style.display = 'block';
            
            // Setup first server
            setupPlayer(links[0].stream_url, links[0].server_name || 'Default', 'series-embed-player', 'series-iframe-loading');
            
            // Create server list
            links.forEach((link, index) => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#';
                a.id = `ssrv-${index}`;
                a.innerHTML = `${link.server_name || 'Server'} <span class="server-badge">${link.quality}</span>`;
                a.onclick = (e) => {
                    e.preventDefault();
                    setupPlayer(link.stream_url, link.server_name || 'Server', 'series-embed-player', 'series-iframe-loading');
                    document.querySelectorAll('#series-server-list a').forEach(el => el.classList.remove('active'));
                    a.classList.add('active');
                };
                li.appendChild(a);
                serverList.appendChild(li);
            });
            
            // Set first server as active
            setTimeout(() => {
                const firstServer = document.getElementById('ssrv-0');
                if (firstServer) firstServer.classList.add('active');
            }, 100);
            
        } else {
            serverList.innerHTML = '<li style="color:#888;">⚠️ No working streaming links</li>';
            document.getElementById('series-player-error').style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error loading episode:', error);
        document.getElementById('series-server-list').innerHTML = '<li style="color:#e50914;">❌ Error loading episode</li>';
        document.getElementById('series-player-error').style.display = 'block';
    }
}

// Close Series Modal
function closeSeriesModal() {
    document.getElementById('seriesModal').style.display = "none";
    document.getElementById('series-embed-player').src = 'about:blank';
    if (state.currentPlayerTimeout) {
        clearTimeout(state.currentPlayerTimeout);
    }
}

// Refresh All Movies
async function refreshAllMovies() {
    updateStatus('Starting refresh for all sites...', 'loading');
    
    try {
        const csrftoken = getCookie('csrftoken');
        const response = await fetch(`${API_BASE}/movies/refresh/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateStatus(data.message, 'success');
            
            // Reload after 60 seconds
            setTimeout(() => {
                updateStatus('Reloading content...', 'loading');
                loadInitialMovies();
            }, 60000);
        } else {
            updateStatus('Failed to start refresh', 'error');
        }
    } catch (error) {
        console.error('Error refreshing:', error);
        updateStatus('Error starting refresh', 'error');
    }
}

// Update Status
function updateStatus(message, type = 'info') {
    const statusElement = document.getElementById('status');
    const indicatorElement = document.getElementById('status-indicator');
    
    statusElement.textContent = message;
    
    if (type === 'loading') {
        indicatorElement.textContent = 'Loading...';
    } else if (type === 'success') {
        indicatorElement.textContent = 'Ready';
    } else if (type === 'error') {
        indicatorElement.textContent = 'Error';
    }
    
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Get Cookie (for CSRF)
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

// Modal close on outside click
window.onclick = (event) => {
    if (event.target == document.getElementById('watchModal')) {
        closeWatchModal();
    }
    if (event.target == document.getElementById('seriesModal')) {
        closeSeriesModal();
    }
};

console.log('Movie Streamer App Loaded Successfully');