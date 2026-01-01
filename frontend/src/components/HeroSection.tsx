// HeroSection component - Large featured movie banner

import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { Movie } from '../types';
import { useApp } from '../context/AppContext';

interface HeroSectionProps {
    movie: Movie;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ movie }) => {
    const navigate = useNavigate();
    const { toggleFavorite, isFavorite, addToList, isInList } = useApp();

    const handlePlay = () => {
        navigate(`/watch/${movie.imdb_id}`);
    };

    const handleMoreInfo = () => {
        navigate(`/detail/${movie.imdb_id}`);
    };

    return (
        <div className="relative h-[70vh] min-h-[500px] w-full overflow-hidden">
            {/* Background Image */}
            <div className="absolute inset-0">
                {movie.poster_url ? (
                    <img
                        src={movie.poster_url}
                        alt={movie.title}
                        className="w-full h-full object-cover object-center"
                    />
                ) : (
                    <div className="w-full h-full bg-dark-800" />
                )}
                {/* Gradient Overlays */}
                <div className="absolute inset-0 bg-gradient-to-r from-black via-black/70 to-transparent" />
                <div className="absolute inset-0 bg-gradient-to-t from-dark-900 via-transparent to-transparent" />
            </div>

            {/* Content */}
            <div className="relative h-full max-w-7xl mx-auto px-6 flex items-center">
                <div className="max-w-2xl">
                    {/* Title */}
                    <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-4 text-shadow">
                        {movie.title}
                    </h1>

                    {/* Year */}
                    {movie.year && (
                        <p className="text-xl text-dark-200 mb-4 text-shadow">{movie.year}</p>
                    )}

                    {/* Synopsis */}
                    {movie.synopsis && (
                        <p className="text-base sm:text-lg text-dark-200 mb-6 line-clamp-3 text-shadow">
                            {movie.synopsis}
                        </p>
                    )}

                    {/* Buttons */}
                    <div className="flex flex-wrap gap-4">
                        <button
                            onClick={handlePlay}
                            className="flex items-center gap-2 bg-white text-black font-semibold px-8 py-3 rounded hover:bg-dark-200 transition-colors duration-300"
                        >
                            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                            </svg>
                            Play
                        </button>

                        <button
                            onClick={handleMoreInfo}
                            className="flex items-center gap-2 bg-dark-600/80 text-white font-semibold px-8 py-3 rounded hover:bg-dark-500/80 transition-colors duration-300"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                            More Info
                        </button>

                        <button
                            onClick={() => toggleFavorite(movie.imdb_id)}
                            className="flex items-center justify-center w-12 h-12 bg-dark-600/80 text-white rounded-full hover:bg-dark-500/80 transition-colors duration-300"
                            aria-label={isFavorite(movie.imdb_id) ? 'Remove from favorites' : 'Add to favorites'}
                        >
                            <svg
                                className="w-6 h-6"
                                fill={isFavorite(movie.imdb_id) ? 'currentColor' : 'none'}
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                                />
                            </svg>
                        </button>

                        <button
                            onClick={() => isInList(movie.imdb_id) ? null : addToList(movie.imdb_id)}
                            className="flex items-center justify-center w-12 h-12 bg-dark-600/80 text-white rounded-full hover:bg-dark-500/80 transition-colors duration-300"
                            aria-label={isInList(movie.imdb_id) ? 'In my list' : 'Add to my list'}
                        >
                            <svg
                                className="w-6 h-6"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d={isInList(movie.imdb_id) ? 'M5 13l4 4L19 7' : 'M12 4v16m8-8H4'}
                                />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
