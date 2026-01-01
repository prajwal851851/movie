// Global application context for state management

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import type { AppState, WatchProgress, Download, UserPreferences } from '../types';
import { useAuth } from './AuthContext';
import { apiService } from '../services/api.service';

interface AppContextType extends AppState {
    // Favorites
    toggleFavorite: (imdbId: string) => void;
    isFavorite: (imdbId: string) => boolean;

    // My List
    addToList: (imdbId: string) => void;
    removeFromList: (imdbId: string) => void;
    isInList: (imdbId: string) => boolean;

    // Watch Progress
    setProgress: (imdbId: string, progress: number, title: string, posterUrl?: string, currentTime?: number, season?: number, episode?: number, contentType?: 'movie' | 'series') => void;
    getProgress: (imdbId: string) => number;
    getWatchItem: (imdbId: string) => WatchProgress | undefined;
    removeFromHistory: (imdbId: string) => void;
    clearHistory: () => void;

    // Downloads
    addDownload: (download: Download) => void;
    removeDownload: (imdbId: string) => void;
    updateDownloadProgress: (imdbId: string, progress: number) => void;

    // Preferences
    updatePreferences: (prefs: Partial<UserPreferences>) => void;
}

const defaultPreferences: UserPreferences = {
    theme: 'dark',
    language: 'en',
    subtitles: true,
    autoplay: true,
    quality: 'auto',
};

const defaultState: AppState = {
    movies: [],
    favorites: [],
    myList: [],
    downloads: [],
    watchHistory: [],
    preferences: defaultPreferences,
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [state, setState] = useState<AppState>(defaultState);

    // Initial load from localStorage (only for guest or as temporary fallback)
    useEffect(() => {
        const saved = localStorage.getItem('appState');
        if (saved) {
            try {
                setState(prev => ({ ...prev, ...JSON.parse(saved) }));
            } catch (e) {
                console.error("Failed to parse appState", e);
            }
        }
    }, []);

    // Fetch user data from backend if authenticated
    useEffect(() => {
        if (isAuthenticated) {
            const fetchData = async () => {
                try {
                    const [favs, wl, hist] = await Promise.all([
                        apiService.getFavorites(),
                        apiService.getWatchlist(),
                        apiService.getHistory()
                    ]);

                    setState(prev => ({
                        ...prev,
                        favorites: favs.map((f: any) => f.movie),
                        myList: wl.map((w: any) => w.movie),
                        watchHistory: hist.map((h: any) => ({
                            imdb_id: h.movie,
                            progress: h.progress,
                            currentTime: h.current_time,
                            season: h.season,
                            episode: h.episode,
                            last_watched: new Date(h.last_watched).getTime(),
                            title: h.movie_details.title,
                            poster_url: h.movie_details.poster_url,
                            contentType: h.movie_details.content_type
                        }))
                    }));
                } catch (err) {
                    console.error("Failed to fetch user data", err);
                }
            };
            fetchData();
        } else {
            // Restore from localStorage for guests
            const saved = localStorage.getItem('appState');
            if (saved) {
                try {
                    setState(prev => ({ ...prev, ...JSON.parse(saved) }));
                } catch (e) { }
            } else {
                setState(defaultState);
            }
        }
    }, [isAuthenticated]);

    // Save to localStorage for guests
    useEffect(() => {
        if (!isAuthenticated) {
            localStorage.setItem('appState', JSON.stringify(state));
        }
    }, [state, isAuthenticated]);

    const requireAuth = () => {
        if (!isAuthenticated) {
            navigate('/login');
            return false;
        }
        return true;
    };

    // Favorites
    const toggleFavorite = async (imdbId: string) => {
        if (!requireAuth()) return;

        const isFav = state.favorites.includes(imdbId);
        try {
            if (isFav) {
                // Find internal ID for deletion
                const favs = await apiService.getFavorites();
                const favItem = favs.find((f: any) => f.movie === imdbId);
                if (favItem) await apiService.removeFromFavorites(favItem.id);
            } else {
                await apiService.addToFavorites(imdbId);
            }

            setState(prev => ({
                ...prev,
                favorites: isFav
                    ? prev.favorites.filter(id => id !== imdbId)
                    : [...prev.favorites, imdbId],
            }));
        } catch (err) {
            console.error("Failed to toggle favorite", err);
        }
    };

    const isFavorite = (imdbId: string) => state.favorites.includes(imdbId);

    // My List
    const addToList = async (imdbId: string) => {
        if (!requireAuth()) return;

        if (!state.myList.includes(imdbId)) {
            try {
                await apiService.addToWatchlist(imdbId);
                setState(prev => ({ ...prev, myList: [...prev.myList, imdbId] }));
            } catch (err) {
                console.error("Failed to add to list", err);
            }
        }
    };

    const removeFromList = async (imdbId: string) => {
        if (!requireAuth()) return;

        try {
            const wl = await apiService.getWatchlist();
            const wlItem = wl.find((w: any) => w.movie === imdbId);
            if (wlItem) await apiService.removeFromWatchlist(wlItem.id);

            setState(prev => ({
                ...prev,
                myList: prev.myList.filter(id => id !== imdbId),
            }));
        } catch (err) {
            console.error("Failed to remove from list", err);
        }
    };

    const isInList = (imdbId: string) => state.myList.includes(imdbId);

    // Watch Progress
    const setProgress = async (
        imdbId: string,
        progress: number,
        title: string,
        posterUrl?: string,
        currentTime?: number,
        season?: number,
        episode?: number,
        contentType?: 'movie' | 'series'
    ) => {
        // Local update first
        const updatedItem: WatchProgress = {
            imdb_id: imdbId,
            progress,
            currentTime,
            season,
            episode,
            contentType,
            timestamp: Date.now(),
            title,
            poster_url: posterUrl,
        };

        setState(prev => {
            const filtered = prev.watchHistory.filter(w => w.imdb_id !== imdbId);
            return {
                ...prev,
                watchHistory: [updatedItem, ...filtered],
            };
        });

        // Sync to backend if authenticated
        if (isAuthenticated) {
            try {
                await apiService.updateHistory({
                    movie: imdbId,
                    progress,
                    current_time: currentTime,
                    season,
                    episode
                });
            } catch (err) {
                console.error("Failed to sync history", err);
            }
        }
    };

    const getWatchItem = (imdbId: string) => state.watchHistory.find(w => w.imdb_id === imdbId);

    const removeFromHistory = async (imdbId: string) => {
        // Optimistic update
        const originalHistory = [...state.watchHistory];
        setState(prev => ({
            ...prev,
            watchHistory: prev.watchHistory.filter(w => w.imdb_id !== imdbId)
        }));

        if (isAuthenticated) {
            try {
                const hist = await apiService.getHistory();
                const item = hist.find((h: any) => h.movie === imdbId);
                if (item) {
                    await apiService.deleteHistoryItem(item.id);
                }
            } catch (err) {
                console.error("Failed to remove from history", err);
                setState(prev => ({ ...prev, watchHistory: originalHistory }));
            }
        }
    };

    const clearHistory = async () => {
        const originalHistory = [...state.watchHistory];
        setState(prev => ({ ...prev, watchHistory: [] }));

        if (isAuthenticated) {
            try {
                await apiService.clearAllHistory();
            } catch (err) {
                console.error("Failed to clear history", err);
                setState(prev => ({ ...prev, watchHistory: originalHistory }));
            }
        }
    };

    const getProgress = (imdbId: string): number => {
        const item = state.watchHistory.find(w => w.imdb_id === imdbId);
        return item?.progress || 0;
    };

    // Downloads
    const addDownload = (download: Download) => {
        if (!state.downloads.find(d => d.imdb_id === download.imdb_id)) {
            setState(prev => ({ ...prev, downloads: [...prev.downloads, download] }));
        }
    };

    const removeDownload = (imdbId: string) => {
        setState(prev => ({
            ...prev,
            downloads: prev.downloads.filter(d => d.imdb_id !== imdbId),
        }));
    };

    const updateDownloadProgress = (imdbId: string, progress: number) => {
        setState(prev => ({
            ...prev,
            downloads: prev.downloads.map(d =>
                d.imdb_id === imdbId ? { ...d, progress } : d
            ),
        }));
    };

    // Preferences
    const updatePreferences = (prefs: Partial<UserPreferences>) => {
        setState(prev => ({
            ...prev,
            preferences: { ...prev.preferences, ...prefs },
        }));
    };

    const value: AppContextType = {
        ...state,
        toggleFavorite,
        isFavorite,
        addToList,
        removeFromList,
        isInList,
        setProgress,
        getProgress,
        getWatchItem,
        removeFromHistory,
        clearHistory,
        addDownload,
        removeDownload,
        updateDownloadProgress,
        updatePreferences,
    };

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useApp must be used within AppProvider');
    }
    return context;
};
