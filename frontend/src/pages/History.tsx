// History page - Grid of recently watched movies

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MovieCard } from '../components/MovieCard';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';

export const History: React.FC = () => {
    const { watchHistory, clearHistory, removeFromHistory } = useApp();

    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-dark-900 pt-24 px-6">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">Watch History</h1>
                        <p className="text-dark-400 font-medium">Continue watching where you left off</p>
                    </div>

                    {isAuthenticated && watchHistory.length > 0 && (
                        <button
                            onClick={() => {
                                if (window.confirm('Clear your entire watch history? This cannot be undone.')) {
                                    clearHistory();
                                }
                            }}
                            className="px-6 py-2 bg-white/5 hover:bg-red-500/10 text-dark-300 hover:text-red-500 border border-white/10 hover:border-red-500/50 rounded-xl transition-all text-sm font-bold flex items-center gap-2"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Clear All
                        </button>
                    )}
                </div>

                {!isAuthenticated ? (
                    <div className="text-center py-20 bg-dark-800/50 backdrop-blur-xl border border-white/5 rounded-3xl animate-scale-in">
                        <div className="bg-primary/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <svg className="w-10 h-10 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <h2 className="text-white text-2xl font-bold mb-3">Sync your watch history</h2>
                        <p className="text-dark-400 mb-8 max-w-md mx-auto">Sign in to keep track of what you've watched across all your devices and get better recommendations.</p>
                        <button
                            onClick={() => navigate('/login')}
                            className="px-10 py-4 bg-primary hover:bg-red-700 text-white font-black rounded-2xl transition-all shadow-2xl active:scale-95"
                        >
                            Sign In to Account
                        </button>
                    </div>
                ) : watchHistory.length > 0 ? (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6 animate-fade-in">
                        {watchHistory.map((item, index) => (
                            <div key={item.imdb_id} className="relative group/history">
                                <MovieCard
                                    movie={{
                                        imdb_id: item.imdb_id,
                                        title: item.title,
                                        poster_url: item.poster_url,
                                        content_type: item.contentType as any,
                                    } as any}
                                    showProgress={true}
                                    progress={item.progress}
                                    delay={index * 30}
                                />
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        removeFromHistory(item.imdb_id);
                                    }}
                                    className="absolute -top-2 -right-2 w-8 h-8 bg-dark-800 hover:bg-red-500 text-white rounded-full flex items-center justify-center shadow-lg border border-white/10 opacity-0 group-hover/history:opacity-100 transition-all z-20"
                                    title="Remove from history"
                                >
                                    ✕
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (

                    <div className="text-center py-20 bg-dark-800/20 border border-white/5 rounded-3xl">
                        <div className="text-6xl mb-6 opacity-30">🕒</div>
                        <h2 className="text-white text-xl font-bold mb-2">No watch history</h2>
                        <p className="text-dark-500">Items you watch will appear here so you can easily find them again.</p>
                        <button
                            onClick={() => navigate('/')}
                            className="mt-8 text-primary font-bold hover:underline"
                        >
                            Start Watching
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
