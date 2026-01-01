import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { MovieCard } from '../components/MovieCard';
import { SkeletonGrid } from '../components/LoadingSpinner';
import { apiService } from '../services/api.service';
import { FeaturedMovieHero } from '../components/FeaturedMovieHero';
import { MovieCarousel } from '../components/MovieCarousel';
import { FilterDropdown } from '../components/FilterDropdown';
import { InstantSearch } from '../components/InstantSearch';
import type { Movie } from '../types';

const ITEMS_PER_PAGE = 54; // Better for grids (divisible by 2, 3, 6, 9)

export const Movies: React.FC = () => {
    const [movies, setMovies] = useState<Movie[]>([]);
    const [featuredMovie, setFeaturedMovie] = useState<Movie | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [searchOpen, setSearchOpen] = useState(false);

    // Filters
    const [searchQuery, setSearchQuery] = useState('');
    const [yearFilter, setYearFilter] = useState('');
    const [years, setYears] = useState<number[]>([]);
    const [recommendedMovies, setRecommendedMovies] = useState<Movie[]>([]);
    const [genreFilter, setGenreFilter] = useState('');
    const [genres, setGenres] = useState<string[]>([]);
    const [localSearchQuery, setLocalSearchQuery] = useState('');

    const [searchParams, setSearchParams] = useSearchParams();

    const MAX_ITEMS = 150;

    // Initial Sync from URL
    useEffect(() => {
        const urlGenre = searchParams.get('genre') || '';
        const urlSearch = searchParams.get('search') || searchParams.get('q') || '';
        const urlYear = searchParams.get('year') || '';

        // Update state but DON'T rely on it for the immediate load
        setGenreFilter(urlGenre);
        setSearchQuery(urlSearch);
        setLocalSearchQuery(urlSearch);
        setYearFilter(urlYear);

        // When URL params change, we reset to page 1 and load with NEW values directly
        setMovies([]);
        setCurrentPage(1);
        setHasMore(true);
        loadMovies(1, true, { genre: urlGenre, search: urlSearch, year: urlYear });
    }, [searchParams]);

    // Initial Load
    useEffect(() => {
        const init = async () => {
            await Promise.all([loadYears(), loadGenres(), loadRecommendations()]);
        };
        init();
    }, []);


    const loadRecommendations = async () => {
        try {
            const data = await apiService.getMovies({
                content_type: 'movie',
                limit: 15,
                year_min: 2017,
                ordering: 'random'
            });
            setRecommendedMovies(data.results);
        } catch (error) {
            console.error('Error loading movie recommendations:', error);
        }
    };

    // Filter Changes Logic (Debounced)
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
    }, [searchQuery, yearFilter, genreFilter]);

    const loadYears = async () => {
        try {
            const yearsData = await apiService.getYears();
            setYears(yearsData);
        } catch (error) {
            console.error('Error loading years:', error);
        }
    };

    const loadGenres = async () => {
        try {
            const genresData = await apiService.getGenres();
            const filteredGenres = genresData.filter(g =>
                !["Action & Adventure", "Sci-Fi & Fantasy", "Soap", "Talk", "War & Politics"].includes(g)
            );
            setGenres(filteredGenres);
        } catch (error) {
            console.error('Error loading genres:', error);
        }
    };

    const loadMovies = async (page: number, isReset: boolean = false, overrides?: { search?: string, genre?: string, year?: string }) => {
        if (isReset) {
            setLoading(true);
        } else {
            setLoadingMore(true);
        }

        try {
            const offset = (page - 1) * ITEMS_PER_PAGE;

            // Check if we reached the limit
            if (offset >= MAX_ITEMS) {
                setHasMore(false);
                return;
            }

            // Use overrides if provided (prevents stale state bug)
            const currentSearch = overrides?.search !== undefined ? overrides.search : searchQuery;
            const currentGenre = overrides?.genre !== undefined ? overrides.genre : genreFilter;
            const currentYear = overrides?.year !== undefined ? overrides.year : yearFilter;

            const data = await apiService.getMovies({
                content_type: 'movie',
                limit: ITEMS_PER_PAGE,
                offset: offset,
                search: currentSearch || undefined,
                year: currentYear ? parseInt(currentYear) : undefined,
                year_min: (currentSearch || currentYear || currentGenre) ? undefined : 2011,
                genre: currentGenre || undefined,
                ordering: (currentSearch || currentYear || currentGenre) ? '-year,-imdb_id' : 'random'
            });

            if (isReset) {
                setMovies(data.results);
                setTotalCount(data.count);
                if (data.results.length > 0) {
                    const random = data.results[Math.floor(Math.random() * Math.min(data.results.length, 10))];
                    setFeaturedMovie(random);
                }
            } else {
                setMovies(prev => [...prev, ...data.results]);
            }

            const nextOffset = offset + data.results.length;
            setHasMore(data.results.length === ITEMS_PER_PAGE && nextOffset < MAX_ITEMS);
            setCurrentPage(page);
        } catch (err) {
            console.error('Error loading movies:', err);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    const loadMore = () => {
        if (loadingMore || !hasMore) return;
        loadMovies(currentPage + 1);
    };

    // Infinite Scroll detection
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
            {/* Hero Section - Only on start and no filters */}
            {!searchQuery && !yearFilter && !genreFilter && featuredMovie && <FeaturedMovieHero movie={featuredMovie} />}

            {/* Filter Bar (Sticky) */}
            <div className="sticky top-[60px] z-40 px-6 py-4 flex flex-wrap items-center justify-between gap-4 bg-dark-900/95 backdrop-blur-md border-b border-white/5 shadow-lg transition-all duration-300">
                <div className="flex items-baseline gap-4">
                    <h2 className="text-2xl font-bold text-white">Movies</h2>

                    <FilterDropdown
                        label="All Genres"
                        value={genreFilter}
                        options={genres}
                        onChange={(val) => {
                            setGenreFilter(val);
                        }}
                    />

                    <FilterDropdown
                        label="All Years"
                        value={yearFilter}
                        options={years.map(String)}
                        onChange={(val) => {
                            setYearFilter(val);
                        }}
                    />
                </div>

                <div className="flex items-center gap-4">
                    {(searchQuery || yearFilter || genreFilter) && (
                        <span className="text-gray-400 text-sm whitespace-nowrap hidden sm:inline-block">
                            Found {totalCount} titles{searchQuery ? ` for "${searchQuery}"` : ''}{genreFilter ? ` in ${genreFilter}` : ''}{yearFilter ? ` for ${yearFilter}` : ''}
                        </span>
                    )}

                    <div className="relative flex items-center">
                        {searchOpen ? (
                            <div className="flex items-center gap-2 animate-fade-in">
                                <InstantSearch
                                    value={localSearchQuery}
                                    onChange={setLocalSearchQuery}
                                    onSearch={(val) => {
                                        setSearchQuery(val);
                                    }}
                                    placeholder="Search movies..."
                                    className="w-48 sm:w-64"
                                    contentType="movie"
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
                                className="p-2 text-gray-400 hover:text-white transition-all hover:scale-110"
                                aria-label="Open Search"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Content Grid */}
            <div className={`px-6 md:px-12 space-y-8 ${!searchQuery && !yearFilter && !genreFilter ? 'mt-4' : 'pt-10'}`}>
                {/* Recommended Carousel - Only start */}
                {!searchQuery && !yearFilter && !genreFilter && recommendedMovies.length > 0 && (
                    <div className="-mx-6 md:-mx-12">
                        <MovieCarousel
                            title="Recommended for You"
                            movies={recommendedMovies}
                        />
                    </div>
                )}

                {/* Main Grid Header */}
                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                    <h3 className="text-xl font-semibold text-gray-200 uppercase tracking-wider">
                        {searchQuery || yearFilter || genreFilter ? 'Search Results' : 'Explore All Movies'}
                    </h3>
                    {movies.length > 0 && <span className="text-sm text-gray-500 font-bold">{totalCount} Total Items</span>}
                </div>

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
                            <div className="text-center py-20">
                                <p className="text-gray-400 text-xl font-medium">No titles found.</p>
                                <p className="text-gray-600 mt-2">Try adjusting your filters.</p>
                            </div>
                        )}

                        {/* Infinite Scroll Loader & End Message */}
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
    );
};
