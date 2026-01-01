// API service for communicating with Django backend

import type { Movie, ApiResponse, Stats, MovieFilters, Review } from '../types';

const API_BASE = '/api';

class ApiService {
    /**
     * Fetch movies with filters and pagination
     */
    async getMovies(filters: MovieFilters = {}): Promise<ApiResponse<Movie>> {
        const params = new URLSearchParams();
        params.append('_t', Date.now().toString());

        // Backend expects 'page' and 'page_size', but frontend sends 'limit' and 'offset'
        // Convert offset to page number
        if (filters.limit) {
            params.append('page_size', filters.limit.toString());
            if (filters.offset !== undefined) {
                const page = Math.floor(filters.offset / filters.limit) + 1;
                params.append('page', page.toString());
            }
        }

        if (filters.content_type) params.append('content_type', filters.content_type);
        if (filters.search) params.append('search', filters.search);
        if (filters.year) params.append('year', filters.year.toString());
        if (filters.source_site) params.append('source_site', filters.source_site);
        if (filters.ordering) params.append('ordering', filters.ordering);
        if (filters.genre) params.append('genre', filters.genre);
        if (filters.imdb_ids) params.append('imdb_ids', filters.imdb_ids);
        if (filters.is_kids) params.append('is_kids', 'true');
        if (filters.is_upcoming) params.append('is_upcoming', 'true');
        if (filters.year_min) params.append('year_min', filters.year_min.toString());
        if (filters.year_max) params.append('year_max', filters.year_max.toString());

        const url = `${API_BASE}/movies/?${params}`;
        console.log(`🔍 Fetching: ${url}`);
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch movies');
        return response.json();
    }

    /**
     * Get movie details by IMDb ID
     */
    async getMovieDetails(imdbId: string): Promise<Movie> {
        const response = await fetch(`${API_BASE}/movies/${imdbId}/`);
        if (!response.ok) throw new Error('Failed to fetch movie details');
        return response.json();
    }

    /**
     * Get streaming links for a movie
     */
    async getStreamingLinks(imdbId: string): Promise<Movie> {
        const response = await fetch(`${API_BASE}/watch/${imdbId}/`);
        if (!response.ok) throw new Error('Failed to fetch streaming links');
        return response.json();
    }

    /**
     * Get statistics
     */
    async getStats(): Promise<Stats> {
        const response = await fetch(`${API_BASE}/movies/stats/`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        return response.json();
    }

    /**
     * Get available years for filtering
     */
    async getYears(): Promise<number[]> {
        const response = await fetch(`${API_BASE}/movies/years/`);
        if (!response.ok) throw new Error('Failed to fetch years');
        return response.json();
    }

    /**
     * Get available genres for filtering
     */
    async getGenres(): Promise<string[]> {
        const response = await fetch(`${API_BASE}/movies/genres/`);
        if (!response.ok) throw new Error('Failed to fetch genres');
        return response.json();
    }

    /**
     * Auth Methods
     */
    async login(data: any) {
        return this.request('/auth/login/', 'POST', data, false);
    }

    async register(data: any) {
        return this.request('/auth/register/', 'POST', data, false);
    }

    async verifyOTP(email: string, otp_code: string) {
        return this.request('/auth/verify-otp/', 'POST', { email, otp_code }, false);
    }

    async resendOTP(email: string) {
        return this.request('/auth/resend-otp/', 'POST', { email }, false);
    }

    async forgotPassword(email: string) {
        return this.request('/auth/forgot-password/', 'POST', { email }, false);
    }

    async resetPassword(data: any) {
        return this.request('/auth/reset-password/', 'POST', data, false);
    }

    async getProfile() {
        return this.request('/auth/profile/', 'GET');
    }

    /**
     * User specific content methods
     */
    async getWatchlist() {
        return this.request('/watchlist/', 'GET');
    }

    async addToWatchlist(movieId: string) {
        return this.request('/watchlist/', 'POST', { movie: movieId });
    }

    async removeFromWatchlist(id: number) {
        return this.request(`/watchlist/${id}/`, 'DELETE');
    }

    async getFavorites() {
        return this.request('/favorites/', 'GET');
    }

    async addToFavorites(movieId: string) {
        return this.request('/favorites/', 'POST', { movie: movieId });
    }

    async removeFromFavorites(id: number) {
        return this.request(`/favorites/${id}/`, 'DELETE');
    }

    async getHistory() {
        return this.request('/history/', 'GET');
    }

    async updateHistory(data: any) {
        return this.request('/history/', 'POST', data);
    }

    async deleteHistoryItem(id: number) {
        return this.request(`/history/${id}/`, 'DELETE');
    }

    async clearAllHistory() {
        return this.request('/history/clear_all/', 'DELETE');
    }

    async getReviews(imdbId: string): Promise<Review[]> {
        return this.request(`/reviews/?movie=${imdbId}`, 'GET', null, false);
    }

    async postReview(data: { movie: string; rating: number; comment: string }) {
        return this.request('/reviews/', 'POST', data);
    }


    async getUserStatus(imdbId: string) {
        const response = await this.request(`/movies/${imdbId}/user_status/`, 'GET');
        return response;
    }

    /**
     * Helper for authenticated requests
     */
    private async request(path: string, method: string = 'GET', body: any = null, auth: boolean = true) {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };

        if (auth) {
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }

        const options: RequestInit = {
            method,
            headers,
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE}${path}`, options);

        if (response.status === 204) return null;
        if (!response.ok) {
            let errorMessage = 'Request failed';
            try {
                const errorData = await response.json();

                // DRF often returns { email: ["..."], non_field_errors: ["..."] }
                // or { detail: "..." } or { error: "..." }
                if (typeof errorData === 'object' && errorData !== null) {
                    if (errorData.error) errorMessage = errorData.error;
                    else if (errorData.message) errorMessage = errorData.message;
                    else if (errorData.detail) errorMessage = errorData.detail;
                    else {
                        // Extract first validation error if it's a field-specific error
                        const firstKey = Object.keys(errorData)[0];
                        const errors = errorData[firstKey];
                        if (Array.isArray(errors)) {
                            errorMessage = `${firstKey}: ${errors[0]}`;
                        } else if (typeof errors === 'string') {
                            errorMessage = errors;
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to parse error response", e);
            }
            throw new Error(errorMessage);
        }


        return response.json();
    }

    /**
     * Build proxy URL for problematic servers
     */
    getProxyUrl(imdbId: string, linkId: number): string {
        return `/player/${imdbId}/${linkId}/`;
    }

    /**
     * Refresh all sites (trigger scraping)
     */
    async refreshAllSites(): Promise<{ status: string; message: string }> {
        const csrfToken = this.getCsrfToken();
        const response = await fetch(`${API_BASE}/movies/refresh/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error('Failed to refresh sites');
        return response.json();
    }

    /**
     * Refresh specific site
     */
    async refreshSite(site: string): Promise<{ status: string; message: string }> {
        const csrfToken = this.getCsrfToken();
        const response = await fetch(`${API_BASE}/movies/refresh-site/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ site }),
        });
        if (!response.ok) throw new Error('Failed to refresh site');
        return response.json();
    }

    /**
     * Get CSRF token from cookies
     */
    private getCsrfToken(): string {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name + '=')) {
                return decodeURIComponent(trimmed.substring(name.length + 1));
            }
        }
        return '';
    }
}


export const apiService = new ApiService();
