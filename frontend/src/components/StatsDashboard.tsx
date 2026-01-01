import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api.service';
import type { Stats } from '../types';

export const StatsDashboard: React.FC = () => {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await apiService.getStats();
                setStats(data);
            } catch (error) {
                console.error('Error fetching stats:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12 animate-pulse">
            {[1, 2, 3, 4].map(i => (
                <div key={i} className="bg-dark-800/50 h-32 rounded-2xl border border-white/5" />
            ))}
        </div>
    );

    if (!stats) return null;

    return (
        <div className="space-y-8 mb-12">
            {/* Primary Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-primary/20 to-transparent p-6 rounded-2xl border border-primary/20 backdrop-blur-sm">
                    <p className="text-dark-400 text-sm font-bold uppercase tracking-wider mb-1">Total Content</p>
                    <h3 className="text-3xl font-black text-white">{stats.total_items.toLocaleString()}</h3>
                    <div className="flex gap-4 mt-2 text-xs font-semibold">
                        <span className="text-primary">{stats.total_movies} Movies</span>
                        <span className="text-blue-400">{stats.total_series} Series</span>
                    </div>
                </div>

                <div className="bg-dark-800/40 p-6 rounded-2xl border border-white/5 backdrop-blur-sm">
                    <p className="text-dark-400 text-sm font-bold uppercase tracking-wider mb-1">Active Links</p>
                    <h3 className="text-3xl font-black text-white">{stats.total_streaming_links.toLocaleString()}</h3>
                    <p className="text-green-500 text-xs font-semibold mt-2">
                        Across {stats.items_with_links} verified titles
                    </p>
                </div>

                <div className="bg-dark-800/40 p-6 rounded-2xl border border-white/5 backdrop-blur-sm">
                    <p className="text-dark-400 text-sm font-bold uppercase tracking-wider mb-1">Top Genre</p>
                    <h3 className="text-3xl font-black text-white">{Object.keys(stats.genres)[0]}</h3>
                    <p className="text-dark-500 text-xs font-semibold mt-2 uppercase">
                        {stats.genres[Object.keys(stats.genres)[0]]} titles
                    </p>
                </div>

                <div className="bg-dark-800/40 p-6 rounded-2xl border border-white/5 backdrop-blur-sm">
                    <p className="text-dark-400 text-sm font-bold uppercase tracking-wider mb-1">Sources</p>
                    <h3 className="text-3xl font-black text-white">{Object.keys(stats.movies_by_site).length}</h3>
                    <div className="flex -space-x-2 mt-2">
                        {Object.keys(stats.movies_by_site).slice(0, 4).map((site, i) => (
                            <div key={site} className={`w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold border-2 border-dark-900 ${i % 2 === 0 ? 'bg-primary text-white' : 'bg-blue-600 text-white'
                                }`}>
                                {site.charAt(0).toUpperCase()}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Genre Distribution */}
            <div className="bg-dark-800/20 p-6 rounded-3xl border border-white/5 overflow-hidden relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                <h4 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                    <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                    Genre Distribution
                </h4>
                <div className="flex flex-wrap gap-2">
                    {Object.entries(stats.genres).map(([genre, count]) => (
                        <div
                            key={genre}
                            className="bg-white/5 hover:bg-white/10 border border-white/10 px-4 py-2 rounded-xl transition-all hover:scale-105"
                        >
                            <span className="text-gray-300 text-xs font-semibold">{genre}</span>
                            <span className="ml-2 text-primary font-bold text-xs">{count}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
