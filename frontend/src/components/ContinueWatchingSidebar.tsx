import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export const ContinueWatchingSidebar: React.FC = () => {
    const { watchHistory } = useApp();
    const navigate = useNavigate();

    // Get last 6 items that have been opened (even if 0 progress)
    const recentHistory = [...watchHistory]
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, 7);

    const formatTime = (seconds?: number) => {
        if (!seconds) return '';
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        let res = '';
        if (hrs > 0) res += `${hrs}h `;
        if (mins > 0 || hrs > 0) res += `${mins}m `;
        res += `${secs}s`;
        return res;
    };

    return (
        <div className="bg-dark-800/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 h-fit sticky top-24">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <span className="text-primary">●</span> Continue Watching
                </h3>
                <span className="text-dark-400 text-xs font-medium uppercase tracking-wider">Last 7</span>
            </div>

            <div className="space-y-4">
                {recentHistory.length > 0 ? (
                    recentHistory.map((item) => (
                        <div
                            key={item.imdb_id + item.timestamp}
                            onClick={() => navigate(`/watch/${item.imdb_id}`)}
                            className="group flex gap-4 p-2 rounded-xl hover:bg-white/5 transition-all cursor-pointer"
                        >
                            {/* Mini Poster */}
                            <div className="relative w-20 aspect-[2/3] shrink-0 rounded-lg overflow-hidden shadow-lg">
                                {item.poster_url ? (
                                    <img
                                        src={item.poster_url}
                                        alt={item.title}
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                                    />
                                ) : (
                                    <div className="w-full h-full bg-dark-700 flex items-center justify-center text-xl">🎬</div>
                                )}

                                {/* Play Icon Overlay */}
                                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                    <svg className="w-8 h-8 text-white fill-current" viewBox="0 0 24 24">
                                        <path d="M8 5v14l11-7z" />
                                    </svg>
                                </div>

                                {/* Tiny Progress Bar on Poster */}
                                <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
                                    <div
                                        className="h-full bg-primary"
                                        style={{ width: `${item.progress}%` }}
                                    />
                                </div>
                            </div>

                            {/* Info */}
                            <div className="flex flex-col justify-center min-w-0">
                                <h4 className="text-white font-semibold text-sm line-clamp-1 mb-1 group-hover:text-primary transition-colors">
                                    {item.title}
                                </h4>

                                {item.contentType === 'series' && item.season && item.episode ? (
                                    <p className="text-primary/80 text-[10px] font-bold uppercase tracking-wider mb-1">
                                        S{item.season} : E{item.episode}
                                    </p>
                                ) : (
                                    <p className="text-dark-400 text-[10px] uppercase font-bold tracking-wider mb-1">
                                        Movie
                                    </p>
                                )}

                                <div className="flex items-center gap-2 text-dark-500 text-[10px]">
                                    <span>Left at:</span>
                                    <span className="text-dark-300 font-medium">{formatTime(item.currentTime)}</span>
                                </div>

                                <div className="mt-2 text-[10px] text-dark-400 font-medium">
                                    {Math.round(item.progress)}% Complete
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="py-12 px-4 text-center border-2 border-dashed border-white/5 rounded-2xl">
                        <div className="text-3xl mb-3 opacity-30">🍿</div>
                        <p className="text-dark-400 text-xs">Your "Continue Watching" list will appear here once you start a movie!</p>
                    </div>
                )}
            </div>

            <button
                onClick={() => navigate('/history')}
                className="w-full mt-6 py-3 border border-white/10 rounded-xl text-xs font-bold text-dark-300 hover:bg-white/5 hover:text-white transition-all uppercase tracking-widest"
            >
                View Full History
            </button>
        </div>
    );
};
