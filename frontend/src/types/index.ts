// Type definitions for the movie streaming application

export interface Movie {
    imdb_id: string;
    title: string;
    year?: number;
    synopsis?: string;
    poster_url?: string;
    content_type: 'movie' | 'series';
    source_site: string;
    source_url?: string;
    links: StreamingLink[];
    reviews?: Review[];
    average_rating?: number;
    created_at?: string;
    updated_at?: string;
    metadata?: SeriesMetadata;
}

export interface SeriesMetadata {
    seasons: Season[];
    number_of_episodes?: number;
    number_of_seasons?: number;
    status?: string;
    genres?: string[];
}

export interface Season {
    season_number: number;
    episode_count: number;
    name?: string;
    air_date?: string;
    poster_path?: string;
}

export interface StreamingLink {
    id: number;
    stream_url: string;
    server_name: string;
    quality: string;
    language: string;
    is_active: boolean;
    needs_proxy?: boolean;
    link_id?: number;
}

export interface Review {
    id: number;
    movie: string; // IMDB ID
    user: number;
    user_email: string;
    user_name: string;
    rating: number; // 1-5
    comment: string;
    created_at: string;
    updated_at: string;
}

export interface WatchProgress {
    imdb_id: string;
    progress: number; // 0-100
    currentTime?: number; // actual seconds
    season?: number;
    episode?: number;
    timestamp: number;
    title: string;
    poster_url?: string;
    contentType?: 'movie' | 'series';
}

export interface Download {
    imdb_id: string;
    title: string;
    poster_url?: string;
    size: number; // in MB
    progress: number; // 0-100
    status: 'downloading' | 'completed' | 'paused' | 'failed';
}

export interface UserPreferences {
    theme: 'dark' | 'light';
    language: string;
    subtitles: boolean;
    autoplay: boolean;
    quality: 'auto' | 'hd' | 'sd';
}

export interface AppState {
    movies: Movie[];
    favorites: string[]; // IMDb IDs
    myList: string[];
    downloads: Download[];
    watchHistory: WatchProgress[];
    preferences: UserPreferences;
}

export interface ApiResponse<T> {
    results: T[];
    count: number;
    next: string | null;
    previous: string | null;
}

export interface Stats {
    total_movies: number;
    total_series: number;
    total_items: number;
    movies_by_site: Record<string, number>;
    items_with_links: number;
    total_streaming_links: number;
    genres: Record<string, number>;
}

export interface MovieFilters {
    content_type?: 'movie' | 'series';
    search?: string;
    year?: number;
    source_site?: string;
    limit?: number;
    offset?: number;
    ordering?: string;
    genre?: string;
    imdb_ids?: string;
    is_kids?: boolean;
    is_upcoming?: boolean;
    year_min?: number;
    year_max?: number;
}
