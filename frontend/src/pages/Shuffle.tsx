import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api.service';
import { useApp } from '../context/AppContext';
import type { Movie } from '../types';

export const Shuffle: React.FC = () => {
    const [shuffleType, setShuffleType] = useState<'movie' | 'series'>('movie');
    const [selectedYear, setSelectedYear] = useState<string>('');
    const [selectedGenre, setSelectedGenre] = useState<string>('');
    const [genres, setGenres] = useState<string[]>([]);
    const [movies, setMovies] = useState<Movie[]>([]);
    const [winner, setWinner] = useState<Movie | null>(null);
    const [isShuffling, setIsShuffling] = useState(false);
    const [hasStarted, setHasStarted] = useState(false);
    const [scrollPosition, setScrollPosition] = useState(0);
    const [transitionDuration, setTransitionDuration] = useState(0);
    const navigate = useNavigate();
    const { toggleFavorite, isFavorite, addToList, isInList } = useApp();

    useEffect(() => {
        const fetchGenres = async () => {
            try {
                const data = await apiService.getGenres();
                setGenres(data);
            } catch (error) {
                console.error('Error fetching genres:', error);
            }
        };
        fetchGenres();
    }, []);

    // Configuration
    const ITEM_HEIGHT = 400; // Height of each poster in the reel (pixels)
    const WINNER_INDEX = 25; // The index to land on
    const TOTAL_ITEMS = 30; // Total items to fetch
    const ANIMATION_DURATION = 4000; // 4 seconds

    const startShuffle = async (typeOverride?: 'movie' | 'series') => {
        const type = typeOverride || shuffleType;
        // Reset animation state instantly
        setIsShuffling(true);
        setHasStarted(true);
        setWinner(null);
        setTransitionDuration(0); // Disable transition for instant reset
        setScrollPosition(0);     // Jump to top

        try {
            console.log(`🎲 Shuffling ${type}: Year=${selectedYear}, Genre=${selectedGenre}`);

            // Fetch a batch of movies/series with filters
            const data = await apiService.getMovies({
                content_type: type,
                ordering: 'random',
                limit: TOTAL_ITEMS,
                year: selectedYear ? parseInt(selectedYear) : undefined,
                genre: selectedGenre || undefined
            });

            console.log(`✅ Shuffle results: ${data.results.length} items found`);

            if (data.results.length > 0) {
                // Pre-select the winning movie from results
                const winnerIndexInResults = Math.floor(Math.random() * data.results.length);
                const winningMovie = data.results[winnerIndexInResults];

                // Build the reel items
                let reelItems: Movie[] = [];
                // Fill up to WINNER_INDEX
                while (reelItems.length < WINNER_INDEX) {
                    reelItems = [...reelItems, ...data.results];
                }

                // Ensure the item at WINNER_INDEX is exactly our winning movie
                reelItems = reelItems.slice(0, WINNER_INDEX);
                reelItems.push(winningMovie);

                // Add some padding items after the winner
                reelItems = [...reelItems, ...data.results].slice(0, WINNER_INDEX + 5);

                setMovies(reelItems);

                // Trigger animation
                setTimeout(() => {
                    setTransitionDuration(ANIMATION_DURATION);
                    requestAnimationFrame(() => {
                        setScrollPosition(WINNER_INDEX * ITEM_HEIGHT);
                    });

                    // Set winner state exactly to the pre-selected movie
                    setTimeout(() => {
                        setWinner(winningMovie);
                        setIsShuffling(false);
                    }, ANIMATION_DURATION);
                }, 100);
            } else {
                // Zero items found
                setIsShuffling(false);
                setWinner(null);
                setMovies([]);
                // We'll show a message in the UI for this state
            }

        } catch (error) {
            console.error('Error fetching shuffle items:', error);
            setIsShuffling(false);
            setHasStarted(false);
        }
    };

    const handlePlay = () => {
        if (winner) {
            navigate(`/watch/${winner.imdb_id}`);
        }
    };

    // Shared Button Style
    const ShuffleButton = ({ onClick, label, isPrimary = false }: { onClick: () => void, label: string, isPrimary?: boolean }) => (
        <button
            onClick={onClick}
            className={`group relative inline-flex items-center justify-center px-8 py-4 text-lg font-bold text-white transition-all duration-300 rounded-full focus:outline-none focus:ring-4 overflow-hidden shadow-lg hover:scale-105 active:scale-95 ${isPrimary
                ? 'bg-primary hover:bg-red-700 focus:ring-red-500/30 shadow-primary/40'
                : 'bg-dark-700 hover:bg-dark-600 focus:ring-gray-500/30 shadow-black/40'
                }`}
        >
            <div className={`absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full ${isPrimary ? 'group-hover:animate-shimmer' : ''}`} />
            <span className="relative z-10 flex items-center gap-3">
                <span className="uppercase tracking-widest">{label}</span>
                <svg className="w-5 h-5 transition-transform duration-300 group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
            </span>
        </button>
    );

    // Initial Screen
    if (!hasStarted) {
        return (
            <div className="min-h-screen bg-dark-900 flex flex-col items-center justify-center p-6 relative overflow-hidden">
                {/* Decorative Background */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px] animate-pulse" />
                    <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] animate-pulse delay-1000" />
                </div>

                <div className="relative z-10 text-center space-y-12 max-w-4xl mx-auto w-full">

                    <div className="space-y-6 animate-fade-in-up">
                        <div className="inline-flex items-center justify-center p-4 bg-dark-800/50 backdrop-blur-md border border-white/10 rounded-2xl shadow-xl mb-4 group-hover:scale-110 transition-transform duration-500">
                            <svg className="w-16 h-16 text-primary drop-shadow-[0_0_15px_rgba(229,9,20,0.5)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>

                        <h1 className="text-6xl md:text-8xl font-black text-white tracking-tighter drop-shadow-2xl">
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400">
                                Decision Time?
                            </span>
                        </h1>
                        <p className="text-2xl text-gray-400 font-light max-w-2xl mx-auto leading-relaxed">
                            Can't decide what to watch? Let our randomizer pick the perfect {shuffleType === 'movie' ? 'movie' : 'series'} for you.
                        </p>
                    </div>

                    {/* Shuffle Type Selector */}
                    <div className="flex flex-col items-center gap-8">
                        <div className="flex bg-dark-800/80 p-1.5 rounded-2xl border border-white/5 backdrop-blur-md shadow-2xl">
                            <button
                                onClick={() => setShuffleType('movie')}
                                className={`px-12 py-3 rounded-xl font-bold transition-all duration-300 ${shuffleType === 'movie'
                                    ? 'bg-primary text-white shadow-lg'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                Movies
                            </button>
                            <button
                                onClick={() => setShuffleType('series')}
                                className={`px-12 py-3 rounded-xl font-bold transition-all duration-300 ${shuffleType === 'series'
                                    ? 'bg-primary text-white shadow-lg'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                TV Series
                            </button>
                        </div>

                        {/* Filters */}
                        <div className="flex flex-wrap justify-center gap-4 animate-fade-in delay-200">
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-gray-500 font-bold uppercase tracking-wider ml-1">Year</label>
                                <select
                                    value={selectedYear}
                                    onChange={(e) => setSelectedYear(e.target.value)}
                                    className="bg-dark-800/80 border border-white/10 rounded-xl px-6 py-3 text-white font-bold outline-none focus:ring-2 focus:ring-primary/50 transition-all cursor-pointer min-w-[140px]"
                                >
                                    <option value="">Any Year</option>
                                    {Array.from({ length: 76 }, (_, i) => 2025 - i).map(year => (
                                        <option key={year} value={year}>{year}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-gray-500 font-bold uppercase tracking-wider ml-1">Genre</label>
                                <select
                                    value={selectedGenre}
                                    onChange={(e) => setSelectedGenre(e.target.value)}
                                    className="bg-dark-800/80 border border-white/10 rounded-xl px-6 py-3 text-white font-bold outline-none focus:ring-2 focus:ring-primary/50 transition-all cursor-pointer min-w-[180px]"
                                >
                                    <option value="">Any Genre</option>
                                    {genres.map(genre => (
                                        <option key={genre} value={genre}>{genre}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <ShuffleButton onClick={() => startShuffle()} label={`Shuffle ${shuffleType === 'movie' ? 'Movies' : 'Series'}`} isPrimary={true} />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 flex items-center justify-center p-6 relative overflow-hidden">
            {/* Background Image of Winner (faded) */}
            {winner && (
                <div className="absolute inset-0 z-0 animate-fade-in">
                    <img
                        src={winner.poster_url}
                        alt={winner.title}
                        className="w-full h-full object-cover opacity-20 blur-xl scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-dark-900 via-dark-900/90 to-dark-900/40" />
                </div>
            )}

            <div className="relative z-10 w-full max-w-6xl mx-auto flex flex-col md:flex-row gap-12 items-center">

                {/* The "Reel" / Poster Display */}
                <div className="relative w-72 h-[450px] md:w-96 md:h-[600px] bg-dark-800 rounded-2xl overflow-hidden shadow-2xl shadow-black ring-4 ring-dark-700 flex-shrink-0">

                    {/* Scrolling Container */}
                    <div
                        className="absolute top-0 left-0 right-0 w-full ease-[cubic-bezier(0.25,0.1,0.25,1)]"
                        style={{
                            transform: `translateY(-${scrollPosition}px)`,
                            transitionProperty: 'transform',
                            transitionDuration: `${transitionDuration}ms`,
                            marginTop: isShuffling ? '0px' : '100px'
                        }}
                    >
                        {movies.map((m, idx) => (
                            <div
                                key={`${m.imdb_id}-${idx}`}
                                className="w-full h-[400px] flex items-center justify-center p-2"
                            >
                                <img
                                    src={m.poster_url}
                                    alt={m.title}
                                    className="h-full w-auto object-cover rounded-lg shadow-md"
                                />
                            </div>
                        ))}
                    </div>

                    {/* Gradient Overlays to simulate 3D cylinder effect */}
                    <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-dark-900 to-transparent z-20 pointer-events-none" />
                    <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-dark-900 to-transparent z-20 pointer-events-none" />

                    {/* Selection Indicator Line */}
                    {!winner && isShuffling && (
                        <div className="absolute top-1/2 left-0 right-0 h-1 bg-primary/50 z-30 transform -translate-y-1/2 shadow-[0_0_20px_rgba(229,9,20,0.5)]" />
                    )}
                </div>

                {/* Result Details - Only show when winner is determined */}
                {winner && !isShuffling ? (
                    <div className="flex-1 text-center md:text-left space-y-8 animate-fade-in-up">
                        <div className="space-y-4">
                            <span className="inline-block px-4 py-1.5 bg-success/20 text-success rounded-full text-sm font-bold tracking-wider uppercase border border-success/20">
                                Winner Selected!
                            </span>
                            <h1 className="text-4xl md:text-6xl font-bold text-white leading-tight">
                                {winner.title}
                            </h1>
                            <div className="flex items-center justify-center md:justify-start gap-4 text-gray-300 text-lg">
                                <span className="text-white font-semibold">{winner.year}</span>
                                <span>•</span>
                                <span className="capitalize">{winner.content_type}</span>
                            </div>
                        </div>

                        <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto md:mx-0">
                            {winner.synopsis}
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center md:justify-start gap-4">
                            <button
                                onClick={handlePlay}
                                className="w-full sm:w-auto px-8 py-4 bg-primary hover:bg-red-700 text-white text-lg font-bold rounded-full shadow-xl shadow-primary/25 transition-all transform hover:scale-105 flex items-center justify-center gap-2"
                            >
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                                </svg>
                                Watch Now
                            </button>

                            <ShuffleButton onClick={() => startShuffle()} label="Shuffle Again" isPrimary={false} />
                        </div>

                        <div className="flex items-center justify-center md:justify-start gap-8 pt-4 border-t border-dark-700/50">
                            <button
                                onClick={() => toggleFavorite(winner.imdb_id)}
                                className={`flex items-center gap-2 group transition-colors ${isFavorite(winner.imdb_id) ? 'text-primary' : 'text-gray-400 hover:text-white'}`}
                            >
                                <svg className={`w-6 h-6 transition-transform group-hover:scale-110 ${isFavorite(winner.imdb_id) ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                                </svg>
                                <span>Favorite</span>
                            </button>
                            <button
                                onClick={() => isInList(winner.imdb_id) ? null : addToList(winner.imdb_id)}
                                className={`flex items-center gap-2 group transition-colors ${isInList(winner.imdb_id) ? 'text-success' : 'text-gray-400 hover:text-white'}`}
                            >
                                <svg className="w-6 h-6 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isInList(winner.imdb_id) ? 'M5 13l4 4L19 7' : 'M12 4v16m8-8H4'} />
                                </svg>
                                <span>{isInList(winner.imdb_id) ? 'In List' : 'My List'}</span>
                            </button>
                        </div>
                    </div>
                ) : !isShuffling && movies.length === 0 ? (
                    <div className="flex-1 text-center space-y-6 animate-fade-in-up">
                        <div className="inline-flex items-center justify-center p-4 bg-dark-800/50 rounded-2xl border border-white/5 shadow-xl mb-4">
                            <svg className="w-12 h-12 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 9.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <h2 className="text-3xl font-bold text-white">No matches found!</h2>
                        <p className="text-gray-400">Try choosing a different year or genre.</p>
                        <div className="flex justify-center md:justify-start">
                            <ShuffleButton onClick={() => setHasStarted(false)} label="Change Filters" isPrimary={false} />
                        </div>
                    </div>
                ) : (
                    <div className="flex-1 text-center text-white/50 animate-pulse text-2xl font-light">
                        Choosing your next favorite...
                    </div>
                )}
            </div>
        </div>
    );
};
