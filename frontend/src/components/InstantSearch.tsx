import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api.service';
import type { Movie } from '../types';

interface InstantSearchProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    contentType?: 'movie' | 'series';
    autoFocus?: boolean;
    onSearch?: (value: string) => void;
}

export const InstantSearch: React.FC<InstantSearchProps> = ({
    value,
    onChange,
    placeholder = "Search...",
    className = "",
    contentType,
    autoFocus = false,
    onSearch
}) => {
    const [suggestions, setSuggestions] = useState<Movie[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const navigate = useNavigate();
    const containerRef = useRef<HTMLDivElement>(null);
    const debounceTimerRef = useRef<any>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const fetchSuggestions = async (query: string) => {
        if (!query.trim() || query.length < 2) {
            setSuggestions([]);
            setIsOpen(false);
            return;
        }

        setLoading(true);
        try {
            const data = await apiService.getMovies({
                search: query,
                content_type: contentType,
                limit: 6,
                ordering: '-year'
            });
            setSuggestions(data.results);
            setIsOpen(data.results.length > 0);
            setSelectedIndex(-1);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;
        onChange(newValue);

        if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = setTimeout(() => {
            fetchSuggestions(newValue);
        }, 300);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev));
        } else if (e.key === 'Enter') {
            if (selectedIndex >= 0) {
                e.preventDefault();
                handleSelect(suggestions[selectedIndex]);
            } else if (value.trim()) {
                e.preventDefault();
                setIsOpen(false);
                if (onSearch) {
                    onSearch(value.trim());
                } else {
                    navigate(`/search?search=${encodeURIComponent(value.trim())}`);
                }
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
        }
    };

    const handleSelect = (movie: Movie) => {
        setIsOpen(false);
        navigate(`/watch/${movie.imdb_id}`);
    };

    return (
        <div className={`relative ${className}`} ref={containerRef}>
            <div className="relative">
                <input
                    type="text"
                    value={value}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    onFocus={() => value.length >= 2 && suggestions.length > 0 && setIsOpen(true)}
                    placeholder={placeholder}
                    autoFocus={autoFocus}
                    className="w-full bg-black/50 border border-white/30 text-white text-sm px-4 py-2 rounded-full focus:border-white transition-all placeholder-gray-400 outline-none"
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    {loading && <div className="w-3 h-3 border border-primary border-t-transparent rounded-full animate-spin"></div>}
                    <button
                        onClick={() => value.trim() && onSearch && onSearch(value.trim())}
                        className={`p-1 transition-colors ${value.trim() ? 'text-primary' : 'text-gray-400'}`}
                        title="Search"
                        type="button"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Suggestions Dropdown */}
            {isOpen && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-dark-800 border border-white/10 rounded-lg shadow-2xl overflow-hidden z-[100] animate-fade-in backdrop-blur-xl">
                    <div className="max-h-[400px] overflow-y-auto">
                        {suggestions.map((movie, index) => (
                            <div
                                key={movie.imdb_id}
                                onClick={() => handleSelect(movie)}
                                onMouseEnter={() => setSelectedIndex(index)}
                                className={`flex items-center gap-4 p-3 cursor-pointer transition-colors ${index === selectedIndex ? 'bg-primary/20 text-white' : 'text-gray-300 hover:bg-white/5'
                                    }`}
                            >
                                <div className="w-10 h-14 shrink-0 overflow-hidden rounded bg-dark-900">
                                    {movie.poster_url ? (
                                        <img src={movie.poster_url} alt="" className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-xs">🎬</div>
                                    )}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-bold text-sm truncate">{movie.title}</div>
                                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                                        <span>{movie.year}</span>
                                        <span className="px-1 border border-gray-700 rounded text-[10px] uppercase">
                                            {movie.content_type === 'series' ? 'TV' : 'Movie'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
