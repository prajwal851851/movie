// MovieCard component - Displays movie poster with hover effects

import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { Movie } from '../types';
import { Badge } from './Badge';
import { useApp } from '../context/AppContext';

interface MovieCardProps {
    movie: Movie;
    delay?: number;
    showProgress?: boolean;
    progress?: number;
}

export const MovieCard: React.FC<MovieCardProps> = ({
    movie,
    delay = 0,
    showProgress = false,
    progress = 0,
}) => {
    const navigate = useNavigate();
    const { addToList, removeFromList, isInList, toggleFavorite, isFavorite } = useApp();

    const handleClick = () => {
        navigate(`/watch/${movie.imdb_id}`);
    };

    const handleListClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (isInList(movie.imdb_id)) {
            removeFromList(movie.imdb_id);
        } else {
            addToList(movie.imdb_id);
        }
    };

    const handleFavoriteClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        toggleFavorite(movie.imdb_id);
    };

    return (
        <div
            className="relative group/card cursor-pointer card-hover"
            style={{ animationDelay: `${delay}ms` }}
            onClick={handleClick}
        >
            {/* Poster Image */}
            <div className="relative aspect-[2/3] overflow-hidden rounded-card bg-dark-800">
                {movie.poster_url && movie.poster_url.trim() !== '' ? (
                    <img
                        src={movie.poster_url}

                        alt={movie.title}
                        className="w-full h-full object-cover transition-transform duration-300 group-hover/card:scale-110"
                        loading="lazy"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-dark-500">
                        <span className="text-4xl">🎬</span>
                    </div>
                )}

                {/* Gradient Overlay */}
                <div className="absolute inset-0 gradient-overlay opacity-0 group-hover/card:opacity-100 transition-opacity duration-300 pointer-events-none" />

                {/* Hover Info */}
                <div className="absolute bottom-0 left-0 right-0 p-4 transform translate-y-full group-hover/card:translate-y-0 transition-transform duration-300 z-20">
                    <h3 className="text-white font-semibold text-sm mb-1 text-shadow line-clamp-2">
                        {movie.title}
                    </h3>
                    {movie.year && (
                        <p className="text-dark-300 text-xs text-shadow">{movie.year}</p>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="absolute top-3 left-3 z-30 flex flex-col gap-2 opacity-0 sm:opacity-40 group-hover/card:opacity-100 transition-all duration-300 transform -translate-x-2 group-hover/card:translate-x-0">
                    {/* My List Button */}
                    <button
                        onClick={handleListClick}
                        className={`p-1 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] hover:scale-125 hover:-translate-y-1 active:scale-90 ${isInList(movie.imdb_id)
                            ? 'text-primary drop-shadow-[0_0_8px_rgba(229,9,20,0.5)]'
                            : 'text-white/60 hover:text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]'
                            }`}
                        title={isInList(movie.imdb_id) ? "Remove from My List" : "Add to My List"}
                    >
                        {isInList(movie.imdb_id) ? (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                        ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                            </svg>
                        )}
                    </button>

                    {/* Favorite Button */}
                    <button
                        onClick={handleFavoriteClick}
                        className={`p-1 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] hover:scale-125 hover:-translate-y-1 active:scale-90 ${isFavorite(movie.imdb_id)
                            ? 'text-primary drop-shadow-[0_0_8px_rgba(229,9,20,0.5)]'
                            : 'text-white/60 hover:text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]'
                            }`}
                        title={isFavorite(movie.imdb_id) ? "Remove from Favorites" : "Add to Favorites"}
                    >
                        <svg className={`w-4 h-4 ${isFavorite(movie.imdb_id) ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                        </svg>
                    </button>
                </div>

                {/* Content Type Badge */}
                <div className="absolute top-2 right-2 z-20">
                    <Badge variant="type" text={movie.content_type === 'series' ? 'TV' : 'Movie'} />
                </div>
            </div>

            {/* Progress Bar */}
            {showProgress && progress > 0 && (
                <div className="mt-2">
                    <div className="w-full h-1 bg-dark-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
};



