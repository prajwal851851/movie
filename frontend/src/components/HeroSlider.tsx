import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Movie } from '../types';
import { useApp } from '../context/AppContext';

interface HeroSliderProps {
    movies: Movie[];
}

export const HeroSlider: React.FC<HeroSliderProps> = ({ movies }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const navigate = useNavigate();
    const { toggleFavorite, isFavorite, addToList, isInList } = useApp();

    const nextSlide = useCallback(() => {
        setCurrentIndex((prev) => (prev + 1) % movies.length);
    }, [movies.length]);

    const prevSlide = () => {
        setCurrentIndex((prev) => (prev - 1 + movies.length) % movies.length);
    };

    useEffect(() => {
        const interval = setInterval(() => {
            nextSlide();
        }, 8000); // 8 seconds per slide

        return () => clearInterval(interval);
    }, [nextSlide]);

    if (!movies.length) return null;

    const currentMovie = movies[currentIndex];

    // Preload next image
    useEffect(() => {
        const nextIndex = (currentIndex + 1) % movies.length;
        const img = new Image();
        if (movies[nextIndex]?.poster_url) {
            img.src = movies[nextIndex].poster_url;
        }
    }, [currentIndex, movies]);

    const handlePlay = (e: React.MouseEvent) => {
        e.stopPropagation();
        navigate(`/watch/${currentMovie.imdb_id}`);
    };

    return (
        <div className="relative h-[70vh] md:h-[80vh] w-full overflow-hidden group bg-dark-900">
            {/* Background Images */}
            {movies.map((movie, index) => (
                <div
                    key={movie.imdb_id}
                    className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${index === currentIndex ? 'opacity-100 z-10' : 'opacity-0 z-0'
                        }`}
                >
                    {movie.poster_url ? (
                        <img
                            src={movie.poster_url}
                            alt={movie.title}
                            className="w-full h-full object-cover object-top"
                        />
                    ) : (
                        <div className="w-full h-full bg-dark-800" />
                    )}
                    {/* Gradient Overlays (Matching FeaturedMovieHero) */}
                    <div className="absolute inset-0 bg-gradient-to-t from-dark-900 via-dark-900/60 to-transparent" />
                    <div className="absolute inset-0 bg-gradient-to-r from-dark-900 via-dark-900/40 to-transparent" />
                </div>
            ))}

            {/* Content */}
            <div className="relative z-20 h-full max-w-7xl mx-auto px-6 md:px-12 lg:px-16 flex flex-col justify-end pb-20 md:pb-24">
                <div className="max-w-3xl space-y-6 animate-fade-in-up">
                    {/* Badges (Matching FeaturedMovieHero) */}
                    <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-primary text-white text-xs font-bold uppercase tracking-wider rounded-sm">
                            Trending Now
                        </span>
                        <span className="px-3 py-1 border border-white/30 text-white text-xs font-bold uppercase tracking-wider rounded-sm">
                            {currentMovie.content_type === 'series' ? 'Series' : 'Movie'}
                        </span>
                    </div>

                    {/* Title (Matching FeaturedMovieHero) */}
                    <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-white leading-tight drop-shadow-2xl">
                        {currentMovie.title}
                    </h1>

                    {/* Meta Info */}
                    <div className="flex items-center gap-4 text-white/90 text-sm md:text-base font-medium">
                        <span className="text-green-400 font-bold">98% Match</span>
                        {currentMovie.year && <span>{currentMovie.year}</span>}
                        <span className="border border-white/40 px-2 py-0.5 text-xs rounded-sm">HD</span>
                    </div>

                    {/* Synopsis */}
                    {currentMovie.synopsis && (
                        <p className="text-white/80 text-lg line-clamp-2 md:line-clamp-3 max-w-2xl text-shadow-sm">
                            {currentMovie.synopsis}
                        </p>
                    )}

                    {/* Buttons (Matching FeaturedMovieHero style) */}
                    <div className="flex flex-wrap items-center gap-4 pt-4">
                        <button
                            onClick={handlePlay}
                            className="bg-white text-black px-8 py-3 rounded text-lg font-bold flex items-center gap-2 hover:bg-white/90 transition-all transform hover:scale-105"
                        >
                            <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z" />
                            </svg>
                            Play
                        </button>

                        <button
                            onClick={() => addToList(currentMovie.imdb_id)}
                            className="bg-gray-500/30 backdrop-blur-sm text-white px-8 py-3 rounded text-lg font-bold flex items-center gap-2 hover:bg-gray-500/50 transition-all transform hover:scale-105"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isInList(currentMovie.imdb_id) ? 'M5 13l4 4L19 7' : 'M12 4v16m8-8H4'} />
                            </svg>
                            {isInList(currentMovie.imdb_id) ? 'In List' : 'My List'}
                        </button>

                        <div className="flex gap-2">
                            <button
                                onClick={() => toggleFavorite(currentMovie.imdb_id)}
                                className={`w-12 h-12 flex items-center justify-center border-2 rounded-full transition-colors ${isFavorite(currentMovie.imdb_id) ? 'border-primary text-primary' : 'border-gray-500 hover:border-white text-gray-400'}`}
                            >
                                <svg className={`w-5 h-5 ${isFavorite(currentMovie.imdb_id) ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Navigation Arrows */}
            <button
                onClick={(e) => { e.stopPropagation(); prevSlide(); }}
                className="absolute left-4 top-1/2 -translate-y-1/2 z-30 w-12 h-12 flex items-center justify-center rounded-full bg-black/30 hover:bg-red-600/80 text-white backdrop-blur-sm transition-all duration-300 opacity-0 group-hover:opacity-100 transform hover:scale-110"
            >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
            </button>
            <button
                onClick={(e) => { e.stopPropagation(); nextSlide(); }}
                className="absolute right-4 top-1/2 -translate-y-1/2 z-30 w-12 h-12 flex items-center justify-center rounded-full bg-black/30 hover:bg-red-600/80 text-white backdrop-blur-sm transition-all duration-300 opacity-0 group-hover:opacity-100 transform hover:scale-110"
            >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
            </button>

            {/* Dots Indicators */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30 flex gap-2">
                {movies.map((_, index) => (
                    <button
                        key={index}
                        onClick={(e) => { e.stopPropagation(); setCurrentIndex(index); }}
                        className={`w-3 h-3 rounded-full transition-all duration-300 ${index === currentIndex ? 'bg-red-600 w-8' : 'bg-white/50 hover:bg-white'
                            }`}
                    />
                ))}
            </div>
        </div>
    );
};
