// MovieCarousel component - Horizontal scrolling carousel

import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MovieCard } from './MovieCard';
import type { Movie } from '../types';

interface MovieCarouselProps {
    title: string;
    movies: Movie[];
    showProgress?: boolean;
    getProgress?: (imdbId: string) => number;
    viewAllLink?: string;
}

export const MovieCarousel: React.FC<MovieCarouselProps> = ({
    title,
    movies,
    showProgress = false,
    getProgress,
    viewAllLink,
}) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();
    const [isAtEnd, setIsAtEnd] = useState(false);
    const [isAtStart, setIsAtStart] = useState(true);

    const checkScrollPosition = () => {
        if (scrollRef.current) {
            const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
            setIsAtStart(scrollLeft <= 0);
            // Check if we are close to the end (within 10px)
            setIsAtEnd(Math.ceil(scrollLeft + clientWidth) >= scrollWidth - 10);
        }
    };

    useEffect(() => {
        checkScrollPosition();
        window.addEventListener('resize', checkScrollPosition);
        return () => window.removeEventListener('resize', checkScrollPosition);
    }, [movies]);

    const scroll = (direction: 'left' | 'right') => {
        if (scrollRef.current) {
            const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
            const scrollAmount = clientWidth * 0.8;

            if (direction === 'right') {
                // If we are already at the end and have a link, redirect
                if (isAtEnd && viewAllLink) {
                    navigate(viewAllLink);
                    return;
                }

                // If scrolling would take us to the end, just scroll to end
                const remaining = scrollWidth - (scrollLeft + clientWidth);
                if (remaining < scrollAmount) {
                    scrollRef.current.scrollBy({ left: remaining, behavior: 'smooth' });
                } else {
                    scrollRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
                }
            } else {
                scrollRef.current.scrollBy({
                    left: -scrollAmount,
                    behavior: 'smooth',
                });
            }
        }
    };

    if (movies.length === 0) return null;

    return (
        <div className="mb-8">
            {/* Title */}
            <h2 className="text-xl md:text-2xl font-bold text-white mb-4 px-6">{title}</h2>

            {/* Carousel Container */}
            <div className="relative group/carousel">
                {/* Left Arrow */}
                <button
                    onClick={() => scroll('left')}
                    className={`absolute left-0 top-0 bottom-0 z-10 w-12 bg-gradient-to-r from-dark-900 to-transparent transition-opacity duration-300 flex items-center justify-center
                        ${isAtStart ? 'opacity-0 pointer-events-none' : 'opacity-0 group-hover/carousel:opacity-100'}`}
                    aria-label="Scroll left"
                >
                    <svg
                        className="w-8 h-8 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 19l-7-7 7-7"
                        />
                    </svg>
                </button>

                {/* Scrollable Content */}
                <div
                    ref={scrollRef}
                    className="flex gap-4 overflow-x-auto hide-scrollbar px-6 py-2"
                    onScroll={checkScrollPosition}
                >
                    {movies.map((movie, index) => (
                        <div key={movie.imdb_id} className="flex-shrink-0 w-40 sm:w-48">
                            <MovieCard
                                movie={movie}
                                delay={index * 50}
                                showProgress={showProgress}
                                progress={getProgress ? getProgress(movie.imdb_id) : 0}
                            />
                        </div>
                    ))}


                </div>

                {/* Right Arrow */}
                <button
                    onClick={() => scroll('right')}
                    className={`absolute right-0 top-0 bottom-0 z-10 w-12 bg-gradient-to-l from-dark-900 to-transparent opacity-0 group-hover/carousel:opacity-100 transition-opacity duration-300 flex items-center justify-center`}
                    aria-label={isAtEnd && viewAllLink ? "View All" : "Scroll right"}
                >
                    <svg
                        className={`w-8 h-8 text-white transition-transform duration-200 ${isAtEnd && viewAllLink ? 'scale-125 text-primary' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        {isAtEnd && viewAllLink ? (
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M13 5l7 7-7 7M5 5l7 7-7 7"
                            />
                        ) : (
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 5l7 7-7 7"
                            />
                        )}
                    </svg>
                </button>
            </div>
        </div>
    );
};
