// Configuration
const API_BASE = '/api';
const ITEMS_PER_PAGE = 12;
const PLAYER_TIMEOUT = 10000;

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

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing Movie Streamer...');
    await loadInitialMovies();
    await populateYearFilter();
    await fetchStats();
}

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

function showPage(page) {
    state.currentContentType = page === 'movies' ? 'movie' : 'series';

    document.getElementById('movies-page').classList.toggle('active', page === 'movies');
    document.getElementById('series-page').classList.toggle('active', page === 'series');

    document.getElementById('movies-nav-btn').classList.toggle('active', page === 'movies');
    document.getElementById('series-nav-btn').classList.toggle('active', page === 'series');

    resetAndReload();
}

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

function buildApiUrl(base, offset) {
    let url = `${base}?limit=${ITEMS_PER_PAGE}&offset=${offset}&content_type=${state.currentContentType}`;
    if (state.currentSearch) url += `&search=${encodeURIComponent(state.currentSearch)}`;
    if (state.currentYear) url += `&year=${state.currentYear}`;
    if (state.currentSource) url += `&source_site=${state.currentSource}`;
    return url;
}

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

async function loadInitialMovies() {
    updateStatus('Loading content...', 'loading');

    try {
        const moviesUrl = buildApiUrl(`${API_BASE}/movies/`, 0);

        const originalType = state.currentContentType;
        state.currentContentType = 'series';
        const seriesUrl = buildApiUrl(`${API_BASE}/movies/`, 0);
        state.currentContentType = originalType;

        const [moviesData, seriesData] = await Promise.all([
            fetch(moviesUrl).then(r => r.json()),
            fetch(seriesUrl).then(r => r.json())
        ]);

        state.allMovies = moviesData.results || [];
        state.currentMovieOffset = state.allMovies.length;
        state.hasMoreMovies = moviesData.next !== null;

        state.allSeries = seriesData.results || [];
        state.currentSeriesOffset = state.allSeries.length;
        state.hasMoreSeries = seriesData.next !== null;

        displayMovies(state.allMovies, false);
        displaySeries(state.allSeries, false);

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

function getSourceName(site) {
    const names = {
        '1flix.to': '1F',
        'goojara.to': 'GJ',
        'sflix.ps': 'SF'
    };
    return names[site] || site;
}

// UPDATED: Enhanced openWatchModal with proxy support
async function openWatchModal(movie) {
    document.getElementById('modal-title').textContent = `${movie.title} ${movie.year ? `(${movie.year})` : ''}`;
    document.getElementById('modal-synopsis').textContent = movie.synopsis || 'No synopsis available.';
    document.getElementById('server-list').innerHTML = '';
    document.getElementById('embed-player').src = '';
    document.getElementById('player-error').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/watch/${movie.imdb_id}/`);
        const data = await response.json();

        console.log('\n' + '='.repeat(60));
        console.log('🔍 API Response for movie:', movie.title);
        console.log('='.repeat(60));

        const links = data.links.filter(link => link.is_active && link.stream_url);

        console.log(`Found ${links.length} active links:`);
        links.forEach((link, i) => {
            console.log(`\n${i + 1}. ${link.server_name}:`);
            console.log(`   URL: ${link.stream_url.substring(0, 60)}...`);
            console.log(`   Needs Proxy: ${link.needs_proxy}`);
            console.log(`   Link ID: ${link.link_id}`);
        });
        console.log('='.repeat(60) + '\n');

        if (links.length > 0) {
            // Load first server
            setupPlayer(
                links[0].stream_url,
                links[0].server_name || 'Default',
                'embed-player',
                'iframe-loading',
                links[0].needs_proxy,
                movie.imdb_id,
                links[0].link_id
            );

            // Create server list
            links.forEach((link, index) => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#';
                a.id = `srv-${index}`;
                a.innerHTML = `${link.server_name || 'Server'} <span class="server-badge">${link.quality}</span>`;

                // Add proxy indicator if needed
                if (link.needs_proxy) {
                    a.innerHTML += ' <span style="color:#4CAF50;font-size:0.8em;">🔒</span>';
                }

                a.onclick = (e) => {
                    e.preventDefault();
                    setupPlayer(
                        link.stream_url,
                        link.server_name || 'Server',
                        'embed-player',
                        'iframe-loading',
                        link.needs_proxy,
                        movie.imdb_id,
                        link.link_id
                    );
                    document.querySelectorAll('#server-list a').forEach(el => el.classList.remove('active'));
                    a.classList.add('active');
                };
                li.appendChild(a);
                document.getElementById('server-list').appendChild(li);
            });

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

    // Show ad-blocker suggestion modal (once per session)
    setTimeout(() => {
        showAdBlockerSuggestion();
    }, 1000);
}

// UPDATED: setupPlayer with proxy support
function setupPlayer(url, serverName, playerId, loadingId, needsProxy = false, imdbId = null, linkId = null) {
    console.log(`🎬 Setting up player:`, {
        server: serverName,
        url: url.substring(0, 60) + '...',
        needsProxy: needsProxy,
        imdbId: imdbId,
        linkId: linkId
    });

    const player = document.getElementById(playerId);
    const loading = document.getElementById(loadingId);
    const errorDiv = playerId === 'embed-player' ?
        document.getElementById('player-error') :
        document.getElementById('series-player-error');

    if (state.currentPlayerTimeout) {
        clearTimeout(state.currentPlayerTimeout);
    }

    loading.style.display = 'flex';
    errorDiv.style.display = 'none';
    player.style.opacity = '0.3';

    player.src = 'about:blank';

    state.currentPlayerTimeout = setTimeout(() => {
        loading.style.display = 'none';
        player.style.opacity = '1';
        console.warn('Player loading timeout - but video may still work');
    }, PLAYER_TIMEOUT);

    setTimeout(() => {
        try {
            // Use proxy for problematic servers
            if (needsProxy && imdbId && linkId) {
                const proxyUrl = `/player/${imdbId}/${linkId}/`;
                console.log('🔒 Using PROXY:', proxyUrl);
                player.src = proxyUrl;
            } else {
                console.log('▶️ Direct embed:', url.substring(0, 60) + '...');
                player.src = url;
            }
        } catch (error) {
            console.error('Error setting player source:', error);
            clearTimeout(state.currentPlayerTimeout);
            loading.style.display = 'none';
            errorDiv.style.display = 'block';
            player.style.opacity = '1';
        }
    }, 300);

    player.onload = () => {
        console.log('Player loaded successfully');
        clearTimeout(state.currentPlayerTimeout);
        setTimeout(() => {
            loading.style.display = 'none';
            player.style.opacity = '1';
        }, 1000);
    };

    player.onerror = () => {
        console.error('Player error');
        clearTimeout(state.currentPlayerTimeout);
        loading.style.display = 'none';
        errorDiv.style.display = 'block';
        player.style.opacity = '1';
    };
}

function closeWatchModal() {
    document.getElementById('watchModal').style.display = "none";
    document.getElementById('embed-player').src = 'about:blank';
    if (state.currentPlayerTimeout) {
        clearTimeout(state.currentPlayerTimeout);
    }
}

// UPDATED: Enhanced openSeriesModal with proxy support
async function openSeriesModal(name, episodes) {
    document.getElementById('series-modal-title').textContent = name;

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

    const seasonSelect = document.getElementById('season-select');
    seasonSelect.innerHTML = '';
    seasons.forEach(season => {
        const option = document.createElement('option');
        option.value = season;
        option.textContent = `Season ${season}`;
        seasonSelect.appendChild(option);
    });

    window.currentSeasonMap = seasonMap;

    updateEpisodeSelect(seasonSelect.value);

    seasonSelect.onchange = () => updateEpisodeSelect(seasonSelect.value);

    document.getElementById('series-server-list').innerHTML = '';
    document.getElementById('series-embed-player').style.display = 'none';
    document.getElementById('series-embed-player').src = '';
    document.getElementById('series-player-error').style.display = 'none';

    document.getElementById('seriesModal').style.display = "block";
}

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

// UPDATED: playSelectedEpisode with proxy support
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
            document.getElementById('series-embed-player').style.display = 'block';

            setupPlayer(
                links[0].stream_url,
                links[0].server_name || 'Default',
                'series-embed-player',
                'series-iframe-loading',
                links[0].needs_proxy,
                episode.imdb_id,
                links[0].link_id
            );

            links.forEach((link, index) => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#';
                a.id = `ssrv-${index}`;
                a.innerHTML = `${link.server_name || 'Server'} <span class="server-badge">${link.quality}</span>`;

                if (link.needs_proxy) {
                    a.innerHTML += ' <span style="color:#4CAF50;font-size:0.8em;">🔒</span>';
                }

                a.onclick = (e) => {
                    e.preventDefault();
                    setupPlayer(
                        link.stream_url,
                        link.server_name || 'Server',
                        'series-embed-player',
                        'series-iframe-loading',
                        link.needs_proxy,
                        episode.imdb_id,
                        link.link_id
                    );
                    document.querySelectorAll('#series-server-list a').forEach(el => el.classList.remove('active'));
                    a.classList.add('active');
                };
                li.appendChild(a);
                serverList.appendChild(li);
            });

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

function closeSeriesModal() {
    document.getElementById('seriesModal').style.display = "none";
    document.getElementById('series-embed-player').src = 'about:blank';
    if (state.currentPlayerTimeout) {
        clearTimeout(state.currentPlayerTimeout);
    }
}

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

window.onclick = (event) => {
    if (event.target == document.getElementById('watchModal')) {
        closeWatchModal();
    }
    if (event.target == document.getElementById('seriesModal')) {
        closeSeriesModal();
    }
};

// Ad-blocker suggestion modal functions
function showAdBlockerSuggestion() {
    // Check if user has dismissed the modal before (session-based)
    if (sessionStorage.getItem('adBlockerSuggestionShown') !== 'true') {
        const modal = document.getElementById('adBlockerModal');
        if (modal) {
            modal.classList.add('show');
            // Mark as shown for this session
            sessionStorage.setItem('adBlockerSuggestionShown', 'true');
        }
    }
}

function closeAdBlockerSuggestion() {
    const modal = document.getElementById('adBlockerModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

console.log('Movie Streamer App Loaded Successfully');