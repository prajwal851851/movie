import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import type { Movie } from '../types';

interface FeaturedMovieHeroProps {
    movie: Movie | null;
}

export const FeaturedMovieHero: React.FC<FeaturedMovieHeroProps> = ({ movie }) => {
    const navigate = useNavigate();
    const { toggleFavorite, isFavorite, addToList, isInList } = useApp();

    if (!movie) return null;

    return (
        <div className="relative w-full h-[50vh] md:h-[60vh] lg:h-[70vh] mb-8 group">
            {/* Background Image */}
            <div className="absolute inset-0">
                <img
                    src={movie.poster_url} // Ideally this would be a backdrop, but poster works for now
                    alt={movie.title}
                    className="w-full h-full object-cover object-top"
                />
                {/* Gradient Overlays */}
                <div className="absolute inset-0 bg-gradient-to-t from-dark-900 via-dark-900/60 to-transparent" />
                <div className="absolute inset-0 bg-gradient-to-r from-dark-900 via-dark-900/40 to-transparent" />
            </div>

            {/* Content */}
            <div className="absolute bottom-0 left-0 right-0 p-6 md:p-12 lg:p-16 flex flex-col justify-end h-full">
                <div className="max-w-3xl space-y-4 md:space-y-6 transform translate-y-4 group-hover:translate-y-0 transition-transform duration-700">
                    {/* Badge */}
                    <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-primary text-white text-[10px] md:text-xs font-bold uppercase tracking-wider rounded-sm">
                            Featured
                        </span>
                        <span className="px-3 py-1 border border-white/30 text-white text-[10px] md:text-xs font-bold uppercase tracking-wider rounded-sm">
                            {movie.content_type}
                        </span>
                    </div>

                    {/* Title */}
                    <h1 className="text-3xl md:text-6xl lg:text-7xl font-black text-white leading-tight drop-shadow-2xl">
                        {movie.title}
                    </h1>

                    {/* Meta */}
                    <div className="flex items-center gap-4 text-white/90 text-sm md:text-base font-medium">
                        <span className="text-green-400">98% Match</span>
                        <span>{movie.year}</span>
                        {/* Fake Rating for feel */}
                        <span className="border border-white/40 px-2 py-0.5 text-xs rounded-sm">HD</span>
                    </div>

                    {/* Synopsis */}
                    <p className="text-white/80 text-lg line-clamp-3 md:line-clamp-4 max-w-2xl text-shadow-sm">
                        {movie.synopsis}
                    </p>

                    {/* Actions */}
                    <div className="flex flex-wrap items-center gap-4 pt-4">
                        <button
                            onClick={() => navigate(`/watch/${movie.imdb_id}`)}
                            className="bg-white text-black px-8 py-3 rounded text-lg font-bold flex items-center gap-2 hover:bg-white/90 transition-colors"
                        >
                            <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z" />
                            </svg>
                            Play
                        </button>

                        <button
                            onClick={() => addToList(movie.imdb_id)}
                            className="bg-gray-500/30 backdrop-blur-sm text-white px-8 py-3 rounded text-lg font-bold flex items-center gap-2 hover:bg-gray-500/50 transition-colors"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isInList(movie.imdb_id) ? 'M5 13l4 4L19 7' : 'M12 4v16m8-8H4'} />
                            </svg>
                            {isInList(movie.imdb_id) ? 'In List' : 'My List'}
                        </button>

                        <button
                            onClick={() => toggleFavorite(movie.imdb_id)}
                            className={`w-12 h-12 flex items-center justify-center border-2 rounded-full transition-colors ${isFavorite(movie.imdb_id) ? 'border-primary text-primary' : 'border-gray-500 hover:border-white text-gray-400'}`}
                        >
                            <svg className={`w-5 h-5 ${isFavorite(movie.imdb_id) ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
