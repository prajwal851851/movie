// My List page - Grid of movies in user's list

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MovieCard } from '../components/MovieCard';
import { LoadingPage } from '../components/LoadingSpinner';
import { apiService } from '../services/api.service';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { StatsDashboard } from '../components/StatsDashboard';
import type { Movie } from '../types';

export const MyList: React.FC = () => {
    const { myList } = useApp();
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [movies, setMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'items' | 'stats'>('items');

    useEffect(() => {
        if (isAuthenticated) {
            loadList();
        } else {
            setMovies([]);
            setLoading(false);
        }
    }, [myList, isAuthenticated]);

    const loadList = async () => {
        if (myList.length === 0) {
            setMovies([]);
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            const data = await apiService.getMovies({
                imdb_ids: myList.join(','),
                limit: 100
            });
            setMovies(data.results);
        } catch (error) {
            console.error('Error loading watchlist:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingPage />;

    return (
        <div className="min-h-screen bg-dark-900 pt-24 px-6">
            <div className="max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-5xl font-black text-white tracking-tighter mb-2">My Library</h1>
                        <p className="text-dark-400 font-medium">Manage your personal collection and database insights</p>
                    </div>

                    {/* Tab Selector */}
                    <div className="flex p-1 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-xl">
                        <button
                            onClick={() => setActiveTab('items')}
                            className={`px-8 py-2.5 rounded-xl text-sm font-black uppercase tracking-widest transition-all ${activeTab === 'items'
                                ? 'bg-primary text-white shadow-lg'
                                : 'text-dark-400 hover:text-white'
                                }`}
                        >
                            Saved Items
                        </button>
                        <button
                            onClick={() => setActiveTab('stats')}
                            className={`px-8 py-2.5 rounded-xl text-sm font-black uppercase tracking-widest transition-all ${activeTab === 'stats'
                                ? 'bg-primary text-white shadow-lg'
                                : 'text-dark-400 hover:text-white'
                                }`}
                        >
                            Statistics
                        </button>
                    </div>
                </div>

                {!isAuthenticated ? (
                    <div className="text-center py-20 bg-dark-800/50 backdrop-blur-xl border border-white/5 rounded-3xl animate-scale-in">
                        <div className="bg-primary/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <svg className="w-10 h-10 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                            </svg>
                        </div>
                        <h2 className="text-white text-2xl font-bold mb-3">Keep track of your shows</h2>
                        <p className="text-dark-400 mb-8 max-w-md mx-auto">Create a personal list of movies and TV shows you want to watch later.</p>
                        <button
                            onClick={() => navigate('/login')}
                            className="px-10 py-4 bg-primary hover:bg-red-700 text-white font-black rounded-2xl transition-all shadow-2xl active:scale-95"
                        >
                            Sign In to Account
                        </button>
                    </div>
                ) : activeTab === 'stats' ? (
                    <div className="animate-fade-in">
                        <StatsDashboard />
                    </div>
                ) : movies.length > 0 ? (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6 animate-fade-in">
                        {movies.map((movie, index) => (
                            <MovieCard key={movie.imdb_id} movie={movie} delay={index * 30} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-dark-800/20 border border-white/5 rounded-3xl animate-scale-in">
                        <div className="text-6xl mb-6 opacity-30">📂</div>
                        <h2 className="text-white text-xl font-bold mb-2">Your list is empty</h2>
                        <p className="text-dark-500">Plan your next movie night by adding items to My List.</p>
                        <button
                            onClick={() => navigate('/movies')}
                            className="mt-8 text-primary font-bold hover:underline"
                        >
                            Browse Content
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
