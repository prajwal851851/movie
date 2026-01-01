// Search page - Search with pagination (50 per page)

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

import { MovieCard } from '../components/MovieCard';
import { SkeletonGrid } from '../components/LoadingSpinner';

import { apiService } from '../services/api.service';
import { InstantSearch } from '../components/InstantSearch';
import type { Movie } from '../types';


const ITEMS_PER_LOAD = 24;

export const Search: React.FC = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const [query, setQuery] = useState(searchParams.get('q') || searchParams.get('search') || '');
    const [genre, setGenre] = useState(searchParams.get('genre') || '');
    const [movies, setMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [offset, setOffset] = useState(0);
    const [totalCount, setTotalCount] = useState(0);


    // Sync query from URL
    useEffect(() => {
        const urlSearch = searchParams.get('q') || searchParams.get('search') || '';
        const urlGenre = searchParams.get('genre') || '';

        if (urlSearch !== query || urlGenre !== genre) {
            setQuery(urlSearch);
            setGenre(urlGenre);
            // If URL changed externally, trigger search reset
            handleSearchReset(urlSearch, urlGenre);
        }
    }, [searchParams]);

    // Initial search if query or genre exists in URL
    useEffect(() => {
        const initialQuery = searchParams.get('q') || searchParams.get('search') || '';
        const initialGenre = searchParams.get('genre') || '';
        if (initialQuery || initialGenre) {
            handleSearchReset(initialQuery, initialGenre);
        }
    }, []);

    const handleSearchReset = (searchQuery: string, genreFilter: string = '') => {
        setOffset(0);
        setMovies([]);
        setHasMore(true);
        performSearch(searchQuery, genreFilter, 0, true);
    };

    const performSearch = async (searchQuery: string, genreFilter: string, currentOffset: number, isReset: boolean = false) => {
        if (!searchQuery.trim() && !genreFilter) {
            setMovies([]);
            setTotalCount(0);
            return;
        }

        try {
            if (isReset) {
                setLoading(true);
            } else {
                setLoadingMore(true);
            }

            const data = await apiService.getMovies({
                search: searchQuery || undefined,
                genre: genreFilter || undefined,
                limit: ITEMS_PER_LOAD,
                offset: currentOffset,
                ordering: '-year,-imdb_id'
            });

            if (isReset) {
                setMovies(data.results);
                setTotalCount(data.count);
            } else {
                setMovies(prev => [...prev, ...data.results]);
            }

            setOffset(currentOffset + ITEMS_PER_LOAD);
            setHasMore(data.results.length === ITEMS_PER_LOAD);
        } catch (error) {
            console.error('Search error:', error);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    const loadMore = () => {
        if (loadingMore || !hasMore || (!query && !genre)) return;
        performSearch(query, genre, offset);
    };

    // Infinite Scroll detection
    useEffect(() => {
        const handleScroll = () => {
            if (window.innerHeight + document.documentElement.scrollTop < document.documentElement.offsetHeight - 500 || loadingMore || !hasMore) return;
            loadMore();
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [loadingMore, hasMore, offset, query, genre]);



    return (
        <div className="min-h-screen bg-dark-900 pb-20 pt-24">
            <div className="px-6 md:px-12">
                {/* Search Bar & Header */}
                <div className="mb-12 max-w-4xl">
                    <h1 className="text-4xl font-black text-white mb-6 tracking-tight">
                        {genre ? (
                            <>
                                <span className="text-primary font-bold">{genre}</span> Content
                            </>
                        ) : (
                            <>
                                Search <span className="text-primary font-bold">Results</span>
                            </>
                        )}
                    </h1>

                    <InstantSearch
                        value={query}
                        onChange={(val) => {
                            setQuery(val);
                            if (val.trim()) {
                                handleSearchReset(val, genre);
                            }
                        }}
                        placeholder="Search for movies, TV shows, or actors..."
                        className="w-full"
                    />

                    {(query || genre) && !loading && (
                        <p className="text-gray-400 mt-4 font-medium animate-fade-in">
                            Found <span className="text-white">{totalCount}</span> results
                            {query && <> for "<span className="text-white">{query}</span>"</>}
                            {genre && <> in <span className="text-white">{genre}</span></>}
                        </p>
                    )}
                </div>

                {/* Grid */}
                {loading ? (
                    <SkeletonGrid count={24} />
                ) : movies.length > 0 ? (
                    <div className="space-y-12">
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-6 gap-y-10 animate-fade-in">
                            {movies.map((movie, index) => (
                                <MovieCard key={`${movie.imdb_id}-${index}`} movie={movie} delay={index % 12 * 50} />
                            ))}
                        </div>

                        {/* Loading Sentinel */}
                        <div className="h-24 flex items-center justify-center">
                            {loadingMore && (
                                <div className="flex items-center gap-3 text-gray-400">
                                    <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                                    <span className="font-bold tracking-widest text-xs uppercase">Loading More Results...</span>
                                </div>
                            )}
                            {!hasMore && movies.length > 0 && (
                                <div className="text-gray-600 text-sm font-medium">
                                    You've reached the end of search results
                                </div>
                            )}
                        </div>
                    </div>
                ) : query && !loading ? (
                    <div className="text-center py-24 bg-dark-800/20 border border-white/5 rounded-3xl animate-scale-in">
                        <div className="text-6xl mb-6 grayscale opacity-50">🔍</div>
                        <h2 className="text-white text-2xl font-bold mb-2">No results found</h2>
                        <p className="text-gray-500 max-w-md mx-auto">We couldn't find any matches {query && `for "${query}"`} {genre && `in genre "${genre}"`}. Try checking your spelling or use more general keywords.</p>
                        <button
                            onClick={() => { setQuery(''); setGenre(''); handleSearchReset('', ''); setSearchParams({}); }}
                            className="mt-8 text-primary font-bold hover:underline"
                        >
                            Clear Filters
                        </button>
                    </div>
                ) : (
                    <div className="text-center py-24 bg-dark-800/20 border border-white/5 rounded-3xl">
                        <div className="text-6xl mb-6 opacity-20">🎥</div>
                        <h2 className="text-white text-2xl font-bold mb-2">Discover content</h2>
                        <p className="text-gray-500">Search for movies and TV shows or filter by genre from our vast library.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

