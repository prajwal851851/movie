import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { MovieCard } from '../components/MovieCard';
import { SkeletonGrid, SkeletonHero } from '../components/LoadingSpinner';
import { InstantSearch } from '../components/InstantSearch';
import { apiService } from '../services/api.service';
import type { Movie } from '../types';

const ITEMS_PER_PAGE = 54;

export const Trending: React.FC = () => {
    const [movies, setMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [localSearchQuery, setLocalSearchQuery] = useState('');
    const [searchOpen, setSearchOpen] = useState(false);
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();

    const MAX_ITEMS = 150;

    // Initial Load
    useEffect(() => {
        const urlSearch = searchParams.get('search') || searchParams.get('q') || '';

        setSearchQuery(urlSearch);
        setLocalSearchQuery(urlSearch);

        setMovies([]);
        setCurrentPage(1);
        setHasMore(true);
        loadTrending(1, true, urlSearch);
    }, [searchParams]);


    // Handle search changes (Debounced)
    useEffect(() => {
        const timeout = setTimeout(() => {
            const newParams: Record<string, string> = {};
            if (searchQuery) newParams.search = searchQuery;

            setSearchParams(newParams, { replace: true });
        }, 500);
        return () => clearTimeout(timeout);
    }, [searchQuery]);

    const loadTrending = async (page: number, isReset: boolean = false, overrideSearch?: string) => {
        if (isReset) {
            setLoading(true);
        } else {
            setLoadingMore(true);
        }

        try {
            const offset = (page - 1) * ITEMS_PER_PAGE;

            if (offset >= MAX_ITEMS) {
                setHasMore(false);
                return;
            }

            const currentSearch = overrideSearch !== undefined ? overrideSearch : searchQuery;

            const data = await apiService.getMovies({
                limit: ITEMS_PER_PAGE,
                offset: offset,
                search: currentSearch || undefined,
                year_min: currentSearch ? undefined : 2011,
                ordering: currentSearch ? '-year' : 'random'
            });

            if (isReset) {
                setMovies(data.results);
                setTotalCount(data.count);
            } else {
                setMovies(prev => [...prev, ...data.results]);
            }

            const nextOffset = offset + data.results.length;
            setHasMore(data.results.length === ITEMS_PER_PAGE && nextOffset < MAX_ITEMS);
            setCurrentPage(page);
        } catch (error) {
            console.error('Error loading trending:', error);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    const loadMore = () => {
        if (loadingMore || !hasMore) return;
        loadTrending(currentPage + 1);
    };

    useEffect(() => {
        const handleScroll = () => {
            if (window.innerHeight + document.documentElement.scrollTop < document.documentElement.offsetHeight - 800 || loadingMore || !hasMore) return;
            loadMore();
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [loadingMore, hasMore, currentPage]);

    if (loading && !movies.length) {
        return (
            <div className="min-h-screen bg-dark-900 pb-20">
                <SkeletonHero />
                <div className="max-w-7xl mx-auto px-6 mt-12">
                    <SkeletonGrid count={12} />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 pb-20">
            {/* Hero Section for Rank #1 - Only on start and no search */}
            {!searchQuery && movies.length > 0 && (
                <div className="relative group overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-t from-dark-900 via-transparent to-transparent z-10" />
                    <div className="h-[60vh] md:h-[70vh] lg:h-[80vh] relative">
                        <img
                            src={movies[0].poster_url}
                            alt={movies[0].title}
                            className="w-full h-full object-cover object-top blur-[2px] opacity-40 scale-105"
                        />
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <span className="text-[25vw] md:text-[20vw] font-black text-white/5 select-none animate-pulse">#1</span>
                        </div>
                    </div>

                    <div className="absolute inset-0 z-20 flex flex-col justify-end p-6 md:p-16 lg:p-24 max-w-5xl">
                        <div className="space-y-4 animate-slide-up">
                            <div className="flex items-center gap-3">
                                <span className="bg-primary text-white text-xs font-black px-3 py-1 rounded-sm uppercase tracking-widest">Trending #1</span>
                                <span className="text-white/60 font-bold">{movies[0].year}</span>
                            </div>
                            <h1 className="text-5xl md:text-7xl lg:text-8xl font-black text-white tracking-tighter drop-shadow-2xl">
                                {movies[0].title}
                            </h1>
                            <p className="text-white/70 text-lg md:text-xl max-w-2xl line-clamp-3">
                                {movies[0].synopsis}
                            </p>
                            <div className="flex gap-4 pt-6">
                                <button
                                    onClick={() => navigate(`/watch/${movies[0].imdb_id}`)}
                                    className="bg-white text-black px-10 py-4 rounded-xl text-lg font-black flex items-center gap-2 hover:bg-white/90 transition-all hover:scale-105 active:scale-95"
                                >
                                    <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                                    Watch Now
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className={`max-w-7xl mx-auto px-6 relative z-[60] ${!searchQuery ? '-mt-10' : 'pt-24'}`}>
                {/* Search Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                    <div>
                        <h2 className="text-4xl font-black text-white uppercase tracking-tighter italic">Trending <span className="text-primary italic">Now</span></h2>
                        <p className="text-gray-500 font-medium mt-1 uppercase tracking-widest text-xs">Live updates from globally popular titles</p>
                    </div>
                    <div className="relative flex items-center">
                        {searchOpen ? (
                            <div className="flex items-center gap-3 animate-fade-in bg-dark-800/80 backdrop-blur-md rounded-full px-2 py-1 ring-1 ring-white/10 shadow-2xl">
                                <InstantSearch
                                    value={localSearchQuery}
                                    onChange={setLocalSearchQuery}
                                    onSearch={(val) => {
                                        setSearchQuery(val);
                                    }}
                                    placeholder="Search trending titles..."
                                    className="w-64 sm:w-80"
                                    autoFocus
                                />
                                <button
                                    onClick={() => {
                                        setSearchOpen(false);
                                        setLocalSearchQuery('');
                                        setSearchQuery('');
                                    }}
                                    className="text-gray-400 hover:text-white transition-colors p-2"
                                >
                                    ✕
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={() => setSearchOpen(true)}
                                className="p-4 bg-white/5 hover:bg-white/10 text-white rounded-full transition-all hover:scale-110 shadow-xl ring-1 ring-white/10 group"
                                aria-label="Open Search"
                            >
                                <svg className="w-6 h-6 text-gray-400 group-hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 relative z-10">
                {/* Advanced Top 10 Ranking - Only on start */}
                {!searchQuery && movies.length >= 10 && (
                    <div className="mb-20">
                        <div className="flex items-center gap-4 mb-8">
                            <h2 className="text-3xl font-black text-white uppercase tracking-tighter italic">Top 10 This Week</h2>
                            <div className="h-[2px] flex-1 bg-gradient-to-r from-primary to-transparent" />
                        </div>
                        <div className="flex gap-6 overflow-x-auto no-scrollbar pb-10 -mx-6 px-6">
                            {movies.slice(0, 10).map((movie, index) => (
                                <div
                                    key={movie.imdb_id}
                                    className="relative flex-shrink-0 group cursor-pointer"
                                    onClick={() => navigate(`/watch/${movie.imdb_id}`)}
                                >
                                    <span className="absolute -left-4 md:-left-8 bottom-0 text-[100px] md:text-[160px] font-black text-transparent stroke-white/20 stroke-1 select-none z-10 transition-all group-hover:text-primary/20 group-hover:stroke-primary group-hover:scale-110"
                                        style={{ WebkitTextStroke: '2px rgba(255,255,255,0.2)' }}>
                                        {index + 1}
                                    </span>

                                    <div className="ml-10 md:ml-20 w-36 md:w-56 aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl shadow-black/50 ring-1 ring-white/10 group-hover:ring-primary/50 group-hover:scale-105 transition-all duration-500">
                                        <img
                                            src={movie.poster_url}
                                            alt={movie.title}
                                            className="w-full h-full object-cover"
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-4 flex flex-col justify-end">
                                            <p className="text-white font-bold text-sm line-clamp-2">{movie.title}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* All Trending Grid */}
                <div className="space-y-8 relative z-10 mt-12">
                    <div className="flex items-center justify-between border-b border-white/5 pb-4">
                        <h2 className="text-2xl font-black text-white tracking-tight uppercase">
                            {!searchQuery ? 'Fresh Popular Content' : 'Search Results'}
                        </h2>
                        {totalCount > 0 && (
                            <span className="text-dark-500 text-sm font-bold bg-white/5 px-3 py-1 rounded-full uppercase tracking-wider">
                                {totalCount} Items
                            </span>
                        )}
                    </div>

                    {loading ? (
                        <SkeletonGrid count={ITEMS_PER_PAGE} />
                    ) : (
                        <>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-4 gap-y-10 animate-fade-in">
                                {movies.map((movie, index) => (
                                    <MovieCard key={`${movie.imdb_id}-${index}`} movie={movie} delay={index * 20} />
                                ))}
                            </div>

                            {movies.length === 0 && (
                                <div className="text-center py-20 text-gray-500">
                                    No results found for your search.
                                </div>
                            )}

                            {/* Loader & Message */}
                            <div className="mt-16 flex flex-col items-center justify-center py-10 border-t border-white/5">
                                {loadingMore && (
                                    <div className="flex items-center gap-3 text-gray-400">
                                        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                                        <span className="font-bold tracking-widest text-xs uppercase">Loading More...</span>
                                    </div>
                                )}

                                {!hasMore && movies.length > 0 && (
                                    <div className="text-center space-y-4 animate-fade-in">
                                        <div className="text-4xl">🔎</div>
                                        <p className="text-gray-400 text-lg font-medium">
                                            You loaded too much.
                                        </p>
                                        <p className="text-primary font-bold text-xl uppercase tracking-tighter italic">
                                            Please use search to find your movie or TV show
                                        </p>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
