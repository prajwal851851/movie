import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { MovieCard } from '../components/MovieCard';
import { SkeletonGrid } from '../components/LoadingSpinner';
import { apiService } from '../services/api.service';
import { InstantSearch } from '../components/InstantSearch';
import { Pagination } from '../components/Pagination';
import type { Movie } from '../types';

const ITEMS_PER_PAGE = 54;

export const Upcoming: React.FC = () => {
    const [movies, setMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [searchOpen, setSearchOpen] = useState(false);

    // Filters
    const [searchQuery, setSearchQuery] = useState('');
    const [localSearchQuery, setLocalSearchQuery] = useState('');

    const [searchParams, setSearchParams] = useSearchParams();

    // Initial Sync from URL
    useEffect(() => {
        const urlSearch = searchParams.get('search') || searchParams.get('q') || '';
        const urlPage = parseInt(searchParams.get('page') || '1');

        if (urlSearch !== searchQuery) {
            setSearchQuery(urlSearch);
            setLocalSearchQuery(urlSearch);
        }
        if (urlPage !== currentPage) setCurrentPage(urlPage);
    }, [searchParams]);

    // Initial Load
    useEffect(() => {
        const init = async () => {
            const urlPage = parseInt(searchParams.get('page') || '1');
            await loadMovies(urlPage);
        };
        init();
    }, []);

    // Filter Changes Logic
    useEffect(() => {
        const timeout = setTimeout(() => {
            const newParams: Record<string, string> = {};
            if (searchQuery) newParams.search = searchQuery;

            if (currentPage !== 1 && searchQuery) {
                setCurrentPage(1);
            } else if (currentPage === 1) {
                loadMovies(1);
            }

            setSearchParams(newParams, { replace: true });
        }, 500);
        return () => clearTimeout(timeout);
    }, [searchQuery]);

    // Page Change Logic
    useEffect(() => {
        loadMovies(currentPage);
    }, [currentPage]);

    const loadMovies = async (page: number = currentPage) => {
        setLoading(true);
        try {
            const offset = (page - 1) * ITEMS_PER_PAGE;
            const data = await apiService.getMovies({
                limit: ITEMS_PER_PAGE,
                offset: offset,
                search: searchQuery || undefined,
                is_upcoming: true,
                ordering: '-year,-imdb_id'
            });

            setMovies(data.results);
            setTotalCount(data.count);
        } catch (err) {
            console.error('Error loading upcoming movies:', err);
        } finally {
            setLoading(false);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    const handlePageChange = (page: number) => {
        setCurrentPage(page);
        const newParams = new URLSearchParams(searchParams);
        newParams.set('page', page.toString());
        setSearchParams(newParams);
    };

    const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

    return (
        <div className="min-h-screen bg-dark-900 pb-20">
            {/* Header / Filter Bar */}
            <div className="pt-[100px] px-6 md:px-12 mb-8">
                <div className="flex flex-wrap items-center justify-between gap-6 pb-6 border-b border-white/10">
                    <div className="space-y-1">
                        <h2 className="text-3xl md:text-4xl font-black text-white">Upcoming</h2>
                        <p className="text-dark-400 font-medium">Coming soon to StreamFlix</p>
                    </div>

                    <div className="flex items-center gap-6">
                        {searchQuery && (
                            <span className="text-gray-400 text-sm whitespace-nowrap hidden sm:inline-block">
                                Found {totalCount} matching titles
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
                                            setCurrentPage(1);
                                        }}
                                        placeholder="Search upcoming..."
                                        className="w-48 sm:w-64"
                                        autoFocus
                                    />
                                    <button
                                        onClick={() => {
                                            setSearchOpen(false);
                                            setLocalSearchQuery('');
                                            setSearchQuery('');
                                            setCurrentPage(1);
                                        }}
                                        className="text-gray-400 hover:text-white transition-colors p-1"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setSearchOpen(true)}
                                    className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl text-white transition-all hover:scale-105"
                                    aria-label="Open Search"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Content Grid */}
            <div className="px-6 md:px-12">
                {loading ? (
                    <SkeletonGrid count={12} />
                ) : (
                    <>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-4 gap-y-10 animate-fade-in">
                            {movies.map((movie, index) => (
                                <MovieCard key={`${movie.imdb_id}-${index}`} movie={movie} />
                            ))}
                        </div>

                        {movies.length === 0 && (
                            <div className="text-center py-24 bg-white/5 rounded-3xl border border-white/5 mx-auto max-w-2xl">
                                <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl">
                                    <svg className="w-10 h-10 text-dark-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <p className="text-white text-xl font-bold">No upcoming titles found.</p>
                                <p className="text-gray-500 mt-2">Check back later for new releases!</p>
                            </div>
                        )}

                        {/* Pagination Component */}
                        {totalPages > 1 && (
                            <div className="mt-20 flex justify-center">
                                <Pagination
                                    currentPage={currentPage}
                                    totalPages={totalPages}
                                    onPageChange={handlePageChange}
                                />
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};
