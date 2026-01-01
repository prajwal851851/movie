// Favorites page - Grid of favorited movies

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MovieCard } from '../components/MovieCard';
import { LoadingPage } from '../components/LoadingSpinner';
import { apiService } from '../services/api.service';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import type { Movie } from '../types';

export const Favorites: React.FC = () => {
    const { favorites } = useApp();
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [movies, setMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isAuthenticated) {
            loadFavorites();
        } else {
            setMovies([]);
            setLoading(false);
        }
    }, [favorites, isAuthenticated]);

    const loadFavorites = async () => {
        if (favorites.length === 0) {
            setMovies([]);
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            const data = await apiService.getMovies({
                imdb_ids: favorites.join(','),
                limit: 100
            });
            setMovies(data.results);
        } catch (error) {
            console.error('Error loading favorites:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingPage />;

    return (
        <div className="min-h-screen bg-dark-900 pt-24 px-6">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">My Favorites</h1>
                        <p className="text-dark-400 font-medium">Movies and series you've marked as favorites</p>
                    </div>
                </div>

                {!isAuthenticated ? (
                    <div className="text-center py-20 bg-dark-800/50 backdrop-blur-xl border border-white/5 rounded-3xl animate-scale-in">
                        <div className="bg-primary/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <svg className="w-10 h-10 text-primary" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                            </svg>
                        </div>
                        <h2 className="text-white text-2xl font-bold mb-3">Sign in to see your favorites</h2>
                        <p className="text-dark-400 mb-8 max-w-md mx-auto">Your favorites list is synced across all your devices when you're signed in.</p>
                        <button
                            onClick={() => navigate('/login')}
                            className="px-10 py-4 bg-primary hover:bg-red-700 text-white font-black rounded-2xl transition-all shadow-2xl active:scale-95"
                        >
                            Sign In to Account
                        </button>
                    </div>
                ) : movies.length > 0 ? (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6 animate-fade-in">
                        {movies.map((movie, index) => (
                            <MovieCard key={movie.imdb_id} movie={movie} delay={index * 30} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-dark-800/20 border border-white/5 rounded-3xl">
                        <div className="text-6xl mb-6 opacity-30">❤️</div>
                        <h2 className="text-white text-xl font-bold mb-2">No favorites yet</h2>
                        <p className="text-dark-500">Add movies you love to this list to watch them later.</p>
                        <button
                            onClick={() => navigate('/movies')}
                            className="mt-8 text-primary font-bold hover:underline"
                        >
                            Explore Movies
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
