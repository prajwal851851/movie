import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { MovieCard } from '../components/MovieCard';
import { SkeletonGrid } from '../components/LoadingSpinner';
import { apiService } from '../services/api.service';
import { FeaturedMovieHero } from '../components/FeaturedMovieHero';
import { FilterDropdown } from '../components/FilterDropdown';
import { InstantSearch } from '../components/InstantSearch';
import type { Movie } from '../types';

const ITEMS_PER_PAGE = 54;

export const Kids: React.FC = () => {
    const [movies, setMovies] = useState<Movie[]>([]);
    const [featuredMovie, setFeaturedMovie] = useState<Movie | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [genreFilter, setGenreFilter] = useState('');
    const [genres, setGenres] = useState<string[]>([]);
    const [yearFilter, setYearFilter] = useState('');
    const [years, setYears] = useState<number[]>([]);
    const [localSearchQuery, setLocalSearchQuery] = useState('');
    const [searchOpen, setSearchOpen] = useState(false);
    const [searchParams, setSearchParams] = useSearchParams();

    const MAX_ITEMS = 200;

    // Initial Sync from URL
    useEffect(() => {
        const urlGenre = searchParams.get('genre') || '';
        const urlSearch = searchParams.get('search') || searchParams.get('q') || '';
        const urlYear = searchParams.get('year') || '';

        setGenreFilter(urlGenre);
        setSearchQuery(urlSearch);
        setLocalSearchQuery(urlSearch);
        setYearFilter(urlYear);

        setMovies([]);
        setCurrentPage(1);
        setHasMore(true);
        loadKidsContent(1, true, { genre: urlGenre, search: urlSearch, year: urlYear });
    }, [searchParams]);

    // Initial Load
    useEffect(() => {
        const init = async () => {
            await Promise.all([loadGenres(), loadYears()]);
        };
        init();
    }, []);


    const loadGenres = async () => {
        try {
            const genresData = await apiService.getGenres();
            setGenres(genresData);
        } catch (error) {
            console.error('Error loading genres:', error);
        }
    };

    const loadYears = async () => {
        try {
            const yearsData = await apiService.getYears();
            setYears(yearsData);
        } catch (error) {
            console.error('Error loading years:', error);
        }
    };

    // Handle filter changes (Debounced)
    useEffect(() => {
        if (loading && !searchParams.get('genre') && !searchParams.get('search') && !searchParams.get('year')) return;

        const timeout = setTimeout(() => {
            const newParams: Record<string, string> = {};
            if (searchQuery) newParams.search = searchQuery;
            if (genreFilter) newParams.genre = genreFilter;
            if (yearFilter) newParams.year = yearFilter;

            setSearchParams(newParams, { replace: true });
        }, 500);
        return () => clearTimeout(timeout);
    }, [searchQuery, genreFilter, yearFilter]);

    const loadKidsContent = async (page: number, isReset: boolean = false, overrides?: { search?: string, genre?: string, year?: string }) => {
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

            const currentSearch = overrides?.search !== undefined ? overrides.search : searchQuery;
            const currentGenre = overrides?.genre !== undefined ? overrides.genre : genreFilter;
            const currentYear = overrides?.year !== undefined ? overrides.year : yearFilter;

            const data = await apiService.getMovies({
                limit: ITEMS_PER_PAGE,
                offset: offset,
                is_kids: true,
                search: currentSearch || undefined,
                genre: currentGenre || undefined,
                year: currentYear ? parseInt(currentYear) : undefined,
                year_min: (currentSearch || currentGenre || currentYear) ? undefined : 2011,
                ordering: (currentSearch || currentGenre || currentYear) ? '-year' : 'random'
            });

            if (isReset) {
                setMovies(data.results);
                setTotalCount(data.count);
                if (data.results.length > 0) {
                    setFeaturedMovie(data.results[0]);
                }
            } else {
                setMovies(prev => [...prev, ...data.results]);
            }

            const nextOffset = offset + data.results.length;
            setHasMore(data.results.length === ITEMS_PER_PAGE && nextOffset < MAX_ITEMS);
            setCurrentPage(page);
        } catch (err) {
            console.error('Error loading kids content:', err);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    const loadMore = () => {
        if (loadingMore || !hasMore) return;
        loadKidsContent(currentPage + 1);
    };

    useEffect(() => {
        const handleScroll = () => {
            if (window.innerHeight + document.documentElement.scrollTop < document.documentElement.offsetHeight - 800 || loadingMore || !hasMore) return;
            loadMore();
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [loadingMore, hasMore, currentPage]);

    return (
        <div className="min-h-screen bg-dark-900 pb-20">
            {/* Hero Section */}
            {!searchQuery && !genreFilter && !yearFilter && featuredMovie && <FeaturedMovieHero movie={featuredMovie} />}

            {/* Sticky Filter Bar */}
            <div className="sticky top-[60px] z-40 px-6 py-4 flex flex-wrap items-center justify-between gap-4 bg-dark-900/95 backdrop-blur-md border-b border-white/5 shadow-lg transition-all duration-300">
                <div className="flex items-baseline gap-4">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <span className="text-yellow-400">🧸</span> Kids
                    </h2>

                    <FilterDropdown
                        label="All Genres"
                        value={genreFilter}
                        options={genres}
                        onChange={(val: string) => {
                            setGenreFilter(val);
                        }}
                    />

                    <FilterDropdown
                        label="All Years"
                        value={yearFilter}
                        options={years.map(String)}
                        onChange={(val: string) => {
                            setYearFilter(val);
                        }}
                    />
                </div>

                <div className="flex items-center gap-4">
                    {(searchQuery || genreFilter || yearFilter) && (
                        <span className="text-gray-400 text-sm whitespace-nowrap hidden sm:inline-block">
                            Found {totalCount} titles{searchQuery ? ` for "${searchQuery}"` : ''}{genreFilter ? ` in ${genreFilter}` : ''}{yearFilter ? ` for ${yearFilter}` : ''}
                        </span>
                    )}

                    <div className="relative flex items-center">
                        {searchOpen ? (
                            <div className="flex items-center gap-2 animate-fade-in bg-white/5 backdrop-blur-md rounded-full px-2 py-1 ring-1 ring-yellow-400/20">
                                <InstantSearch
                                    value={localSearchQuery}
                                    onChange={setLocalSearchQuery}
                                    onSearch={(val) => {
                                        setSearchQuery(val);
                                    }}
                                    placeholder="Search magic..."
                                    className="w-48 sm:w-64"
                                    autoFocus
                                />
                                <button
                                    onClick={() => {
                                        setSearchOpen(false);
                                        setLocalSearchQuery('');
                                        setSearchQuery('');
                                    }}
                                    className="text-gray-400 hover:text-white transition-colors p-1"
                                >
                                    ✕
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={() => setSearchOpen(true)}
                                className="p-2 text-yellow-400/60 hover:text-yellow-400 transition-all hover:scale-110"
                                aria-label="Open Search"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Results Info */}
            {(searchQuery || genreFilter || yearFilter) && (
                <div className="px-6 md:px-12 pt-8">
                    <h3 className="text-xl font-black text-white uppercase tracking-widest flex items-center gap-2">
                        <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                        Search Results
                    </h3>
                </div>
            )}

            {/* Grid */}
            <div className="px-6 md:px-12 mt-8 relative z-10">
                {loading ? (
                    <SkeletonGrid count={ITEMS_PER_PAGE} />
                ) : (
                    <>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-4 gap-y-10 animate-fade-in">
                            {movies.map((movie, index) => (
                                <MovieCard key={`${movie.imdb_id}-${index}`} movie={movie} />
                            ))}
                        </div>

                        {movies.length === 0 && (
                            <div className="text-center py-32">
                                <span className="text-6xl block mb-6">🏜️</span>
                                <h3 className="text-2xl font-bold text-white">No magic found here</h3>
                                <p className="text-dark-400 mt-2">Try searching for something else!</p>
                            </div>
                        )}

                        {/* Loader & Message */}
                        <div className="mt-16 flex flex-col items-center justify-center py-10 border-t border-white/5">
                            {loadingMore && (
                                <div className="flex items-center gap-3 text-gray-400">
                                    <div className="w-6 h-6 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                                    <span className="font-bold tracking-widest text-xs uppercase">Loading More...</span>
                                </div>
                            )}

                            {!hasMore && movies.length > 0 && (
                                <div className="text-center space-y-4 animate-fade-in">
                                    <div className="text-4xl">🔎</div>
                                    <p className="text-gray-400 text-lg font-medium">
                                        You loaded too much.
                                    </p>
                                    <p className="text-yellow-400 font-bold text-xl uppercase tracking-tighter italic">
                                        Please use search to find your movie or TV show
                                    </p>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
