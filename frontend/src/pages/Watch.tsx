import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Hls from 'hls.js';
import { apiService } from '../services/api.service';
import { useApp } from '../context/AppContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { MovieCarousel } from '../components/MovieCarousel';
import { ReviewSection } from '../components/ReviewSection';
import type { Movie, StreamingLink } from '../types';

export const Watch: React.FC = () => {
    const { imdbId } = useParams<{ imdbId: string }>();
    const navigate = useNavigate();
    const iframeRef = useRef<HTMLIFrameElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const reviewSectionRef = useRef<HTMLDivElement>(null);
    const hlsRef = useRef<Hls | null>(null);

    const [movie, setMovie] = useState<Movie | null>(null);
    const [relatedMovies, setRelatedMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);
    const [playerLoading, setPlayerLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedLink, setSelectedLink] = useState<StreamingLink | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [matchPercentage, setMatchPercentage] = useState(98);

    // TV Show State
    const [selectedSeason, setSelectedSeason] = useState(1);
    const [selectedEpisode, setSelectedEpisode] = useState(1);

    // AdBlock Modal State
    const [showAdBlockModal, setShowAdBlockModal] = useState(true);

    const { addToList, isInList, isFavorite, setProgress, getWatchItem } = useApp();
    const saveTimeoutRef = useRef<any>(null);

    useEffect(() => {
        if (imdbId) {
            // Reset modal state when movie changes
            setShowAdBlockModal(true);
            loadMovie();
        }
    }, [imdbId]);

    useEffect(() => {
        return () => {
            // Cleanup HLS on unmount
            if (hlsRef.current) {
                hlsRef.current.destroy();
            }
        };
    }, []);

    // Effect to handle actual mounting of video source when selectedLink changes or modal is dismissed
    useEffect(() => {
        if (!showAdBlockModal && selectedLink) {
            mountVideoSource(selectedLink);
        }
    }, [showAdBlockModal, selectedLink]);

    const loadMovie = async () => {
        try {
            setLoading(true);
            setError(null);
            setRelatedMovies([]); // Clear previous recommendations
            const data = await apiService.getStreamingLinks(imdbId!);
            setMovie(data);
            setMatchPercentage(Math.floor(Math.random() * (95 - 70 + 1)) + 70);

            // Check for previous progress
            const history = getWatchItem(imdbId!);
            if (history) {
                if (data.content_type === 'series') {
                    if (history.season) setSelectedSeason(history.season);
                    if (history.episode) setSelectedEpisode(history.episode);
                }
            }

            // Select first active link
            const activeLinks = data.links.filter(link => link.is_active && link.stream_url);
            if (activeLinks.length > 0) {
                setSelectedLink(activeLinks[0]);
                // We set selectedLink, but play will only happen after modal dismiss via useEffect
            } else {
                setError("opps!!! the movie likely not released or we don't have the link for this movie please visit later for this movie");
            }

            // Load recommendations based on content type and genres
            const contentType = data.content_type === 'series' ? 'series' : 'movie';
            const genres = (data.metadata as any)?.genres || [];
            loadRecommendations(contentType, genres);

        } catch (err) {
            console.error('Error loading movie:', err);
            setError("opps!!! the movie likely not released or we don't have the link for this movie please visit later for this movie");
        } finally {
            setLoading(false);
        }
    };

    const loadRecommendations = async (contentType: 'movie' | 'series', genres: string[] = []) => {
        try {
            // Priority: Fetch items with matching genres
            let allRelated: Movie[] = [];

            if (genres.length > 0) {
                // Fetch for each of the first 3 genres separately for max accuracy
                const genreToFetch = genres.slice(0, 3);

                const genrePromises = genreToFetch.map(g =>
                    apiService.getMovies({
                        content_type: contentType,
                        genre: g,
                        limit: 12,
                        ordering: 'random'
                    })
                );

                const responses = await Promise.all(genrePromises);

                // Collect and deduplicate
                const seenIds = new Set<string>();
                seenIds.add(imdbId!); // Exclude current

                responses.forEach(res => {
                    res.results.forEach(m => {
                        if (!seenIds.has(m.imdb_id)) {
                            allRelated.push(m);
                            seenIds.add(m.imdb_id);
                        }
                    });
                });
            }

            // The user specifically said "ONLY related to that currently watching movie or tv show genera"
            // So we will respect that and NOT backfill with random.

            setRelatedMovies(allRelated.slice(0, 20));
        } catch (err) {
            console.error('Error loading recommendations:', err);
        }
    };

    const handleServerSelect = (link: StreamingLink) => {
        // User manually selected a server
        setError(null);
        setPlayerLoading(true);
        setSelectedLink(link);
        // useEffect will trigger mountVideoSource
    };

    const mountVideoSource = (link: StreamingLink) => {
        // This function assumes refs are ready (guarded by !showAdBlockModal in useEffect)
        setPlayerLoading(true);

        const url = link.stream_url.toLowerCase();

        // Detect video type
        if (url.endsWith('.m3u8')) {
            // HLS stream
            loadHlsStream(link.stream_url);
        } else if (url.endsWith('.mp4') || url.endsWith('.webm')) {
            // Direct video file
            loadDirectVideo(link.stream_url);
        } else {
            // Iframe embed
            let finalUrl = link.stream_url;

            // Handle TV Show parameter injection for VidSrc
            if (movie?.content_type === 'series') {
                if (link.stream_url.includes('vidsrc.to')) {
                    finalUrl = `https://vidsrc.to/embed/tv/${imdbId}/${selectedSeason}/${selectedEpisode}`;
                } else if (link.stream_url.includes('vidsrc.me')) {
                    finalUrl = `https://vidsrc.me/embed/tv?imdb=${imdbId}&s=${selectedSeason}&e=${selectedEpisode}`;
                }
            }

            loadIframe(finalUrl, link);
        }

        setTimeout(() => setPlayerLoading(false), 1500);
    };

    // Reload video when season/episode changes
    useEffect(() => {
        if (movie?.content_type === 'series' && selectedLink && !showAdBlockModal) {
            mountVideoSource(selectedLink);
            // Save episode change immediately
            handleProgressUpdate();
        }
    }, [selectedSeason, selectedEpisode]);

    const isHlsOrDirect = selectedLink && (
        selectedLink.stream_url.toLowerCase().endsWith('.m3u8') ||
        selectedLink.stream_url.toLowerCase().endsWith('.mp4') ||
        selectedLink.stream_url.toLowerCase().endsWith('.webm')
    );

    const handleProgressUpdate = () => {
        if (!movie) return;

        const existingHistory = getWatchItem(movie.imdb_id);
        let progress = existingHistory?.progress || 0;
        let currentTime = existingHistory?.currentTime || 0;

        // Only update from videoRef if it has valid duration and has actually started or moved
        if (videoRef.current && videoRef.current.duration > 0) {
            const v = videoRef.current;
            // Prevent overwriting a good progress with 0 while the video is still loading/seeking
            const isActuallyStarted = v.currentTime > 0 || (v.seeking === false && v.readyState >= 2);

            if (isActuallyStarted) {
                currentTime = v.currentTime;
                progress = (currentTime / v.duration) * 100;
            }
        }

        setProgress(
            movie.imdb_id,
            progress,
            movie.title,
            movie.poster_url,
            currentTime,
            movie.content_type === 'series' ? selectedSeason : undefined,
            movie.content_type === 'series' ? selectedEpisode : undefined,
            movie.content_type
        );
    };

    // Unified progress tracking effect
    useEffect(() => {
        const video = videoRef.current;

        // Window level save (for closing tab/browser)
        const handleWindowExit = () => handleProgressUpdate();
        window.addEventListener('visibilitychange', handleWindowExit);
        window.addEventListener('pagehide', handleWindowExit);
        window.addEventListener('beforeunload', handleWindowExit);

        let timeUpdateInterval: any = null;

        const handleTimeUpdate = () => {
            const now = Date.now();
            const videoAny = video as any;
            if (videoAny && (!videoAny.lastSaved || now - videoAny.lastSaved > 5000)) {
                handleProgressUpdate();
                videoAny.lastSaved = now;
            }
        };

        const handlePause = () => handleProgressUpdate();

        const handleLoadedMetadata = () => {
            const history = getWatchItem(imdbId!);
            if (history && history.currentTime && history.currentTime > 0 && video) {
                const isSameEpisode = movie?.content_type !== 'series' ||
                    (history.season === selectedSeason && history.episode === selectedEpisode);

                if (isSameEpisode) {
                    video.currentTime = history.currentTime;
                }
            }
        };

        // If it's a video element (Direct/HLS)
        if (video) {
            video.addEventListener('timeupdate', handleTimeUpdate);
            video.addEventListener('pause', handlePause);
            video.addEventListener('loadedmetadata', handleLoadedMetadata);
        } else {
            // If it's an iframe (VidSrc etc), we can't track time, 
            // so we just save the fact that it's open every 30 seconds
            timeUpdateInterval = setInterval(handleProgressUpdate, 30000);
            // And save immediately on load
            handleProgressUpdate();
        }

        return () => {
            window.removeEventListener('visibilitychange', handleWindowExit);
            window.removeEventListener('pagehide', handleWindowExit);
            window.removeEventListener('beforeunload', handleWindowExit);

            if (video) {
                video.removeEventListener('timeupdate', handleTimeUpdate);
                video.removeEventListener('pause', handlePause);
                video.removeEventListener('loadedmetadata', handleLoadedMetadata);
            }
            if (timeUpdateInterval) clearInterval(timeUpdateInterval);

            // Critical: Final save on unmount or switch
            handleProgressUpdate();
        };
    }, [imdbId, selectedSeason, selectedEpisode, movie, isHlsOrDirect]);

    // Cleanup timeout
    useEffect(() => {
        return () => {
            if (saveTimeoutRef.current) {
                clearTimeout(saveTimeoutRef.current);
            }
        };
    }, []);

    const loadHlsStream = (url: string) => {
        // Wait a tick to ensure ref is populated if just rendered
        setTimeout(() => {
            if (!videoRef.current) return;

            // Cleanup previous HLS instance
            if (hlsRef.current) {
                hlsRef.current.destroy();
            }

            if (Hls.isSupported()) {
                const hls = new Hls({
                    enableWorker: true,
                    lowLatencyMode: true,
                });
                hls.loadSource(url);
                hls.attachMedia(videoRef.current);
                hls.on(Hls.Events.MANIFEST_PARSED, () => {
                    videoRef.current?.play().catch(e => console.log("Autoplay prevented", e));
                });
                hls.on(Hls.Events.ERROR, (_event, data) => {
                    console.error('HLS error:', data);
                    if (data.fatal) {
                        setError('Failed to load video stream');
                    }
                });
                hlsRef.current = hls;
            } else if (videoRef.current.canPlayType('application/vnd.apple.mpegurl')) {
                // Native HLS support (Safari)
                videoRef.current.src = url;
                videoRef.current.play().catch(e => console.log("Autoplay prevented", e));
            } else {
                setError('HLS not supported in this browser');
            }
        }, 0);
    };

    const loadDirectVideo = (url: string) => {
        setTimeout(() => {
            if (videoRef.current) {
                videoRef.current.src = url;
                videoRef.current.play().catch(e => console.log("Autoplay prevented", e));
            }
        }, 0);
    };

    const loadIframe = (url: string, link: StreamingLink) => {
        setTimeout(() => {
            if (!iframeRef.current) return;

            // Use the player proxy for all iframe-based servers to strip ads safely
            // Direct links are and often cause popups/redirects on standard browsers
            const baseUrl = apiService.getProxyUrl(imdbId!, link.link_id || link.id);
            const params = new URLSearchParams();
            if (movie?.content_type === 'series') {
                params.append('s', selectedSeason.toString());
                params.append('e', selectedEpisode.toString());
            }

            const proxyUrl = `${baseUrl}${params.toString() ? '?' + params.toString() : ''}`;

            // Check for known servers that block embedding entirely
            if (url.includes('1flix.to')) {
                setError('This server blocks embedding. Please try another server.');
            } else {
                iframeRef.current.src = proxyUrl;
            }
        }, 0);
    };

    const handleRefreshLinks = async () => {
        setRefreshing(true);
        await loadMovie();
        setRefreshing(false);
    };

    const handleModalDismiss = () => {
        setShowAdBlockModal(false);
        // useEffect will pick up the change and mount the video
    };

    const scrollToReviews = () => {
        reviewSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    if (loading) return <div className="min-h-screen bg-black flex items-center justify-center"><LoadingSpinner size="lg" /></div>;
    if (!movie) return <div className="min-h-screen bg-black flex items-center justify-center text-white">Movie not found</div>;

    const activeLinks = movie.links.filter(link => link.is_active && link.stream_url);
    const movieMetadata = movie.metadata as any;

    return (
        <div className="min-h-screen bg-dark-900 text-white font-sans flex flex-col">
            {/* Back Button */}
            <div className="fixed top-4 left-4 z-50">
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 bg-dark-800/90 text-white px-4 py-2 rounded-full hover:bg-dark-700 transition-colors shadow-lg border border-white/10"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back
                </button>
            </div>

            {/* Container for Centered Player */}
            <div className="flex-1 flex flex-col items-center justify-center pt-20 pb-8 px-4 bg-gradient-to-b from-dark-900 to-black">

                {/* Player Box - Reduced Width */}
                <div className="relative w-full max-w-4xl aspect-video bg-black rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] ring-1 ring-white/10 group">

                    {/* Cool Ad Block Modal */}
                    {showAdBlockModal && (
                        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md p-4 sm:p-6 animate-fade-in text-center overflow-y-auto">
                            <div className="bg-gradient-to-br from-gray-900 to-black border border-white/10 p-6 sm:p-10 max-w-lg w-full shadow-2xl rounded-3xl relative animate-fade-in transform transition-all scale-100 hover:scale-[1.01] duration-300 my-auto">

                                {/* Close Button for Mobile/General */}
                                <button
                                    onClick={handleModalDismiss}
                                    className="absolute top-4 right-4 text-white/40 hover:text-white p-3 z-20 transition-all hover:scale-110 active:scale-90 bg-white/5 hover:bg-white/10 rounded-full"
                                    aria-label="Close"
                                >
                                    <svg className="w-6 h-6 sm:w-8 sm:h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>

                                {/* Decorative Glow */}
                                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-1 bg-primary blur-lg opacity-70"></div>

                                {/* Icon */}
                                <div className="mx-auto w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mb-6">
                                    <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                    </svg>
                                </div>

                                <h3 className="text-2xl sm:text-3xl font-bold text-white mb-3">Enhance Your Experience</h3>
                                <p className="text-gray-400 mb-6 sm:mb-8 leading-relaxed text-xs sm:text-sm">
                                    We want you to have the best possible movie night. <br className="hidden sm:block" />
                                    For a smoother, safer, and ad-free experience, we recommend switching to a secure browser.
                                </p>

                                <div className="space-y-4">
                                    <a href="https://brave.com/download/" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-3 w-full px-4 sm:px-6 py-3 sm:py-4 bg-gradient-to-r from-[#FF5500] to-[#FF3300] hover:from-[#FF6600] hover:to-[#FF4400] text-white font-bold rounded-xl transition-all shadow-lg shadow-orange-500/20 group-hover:shadow-orange-500/30 text-sm sm:text-base">
                                        <img src="https://brave.com/static-assets/images/brave-logo-sans-text.svg" alt="Brave" className="w-5 h-5 sm:w-6 sm:h-6 invert" />
                                        <span>Download Brave Browser</span>
                                    </a>

                                    <div className="grid grid-cols-2 gap-3">
                                        <button
                                            onClick={(e) => {
                                                navigator.clipboard.writeText(window.location.href);
                                                const btn = e.currentTarget;
                                                const originalContent = btn.innerHTML;

                                                // Change button state
                                                btn.innerHTML = `
                                                    <div class="flex items-center gap-2 text-green-400">
                                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                                        <span>Copied!</span>
                                                    </div>
                                                `;
                                                btn.classList.add('bg-green-500/10', 'border-green-500/50');
                                                btn.classList.remove('bg-white/5', 'hover:bg-white/10');

                                                setTimeout(() => {
                                                    btn.innerHTML = originalContent;
                                                    btn.classList.remove('bg-green-500/10', 'border-green-500/50');
                                                    btn.classList.add('bg-white/5', 'hover:bg-white/10');
                                                }, 2000);
                                            }}
                                            className="flex items-center justify-center gap-2 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 font-semibold rounded-lg transition-all"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                                            <span>Copy Link</span>
                                        </button>

                                        <a href="https://ublockorigin.com/" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 font-semibold rounded-lg transition-all">
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                                            <span>Ad Blocker</span>
                                        </a>
                                    </div>

                                    <button
                                        onClick={handleModalDismiss}
                                        className="w-full py-3 mt-4 text-gray-500 hover:text-white text-sm font-medium transition-colors"
                                    >
                                        No thanks, I'll watch with ads
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Video Container */}
                    <div className="w-full h-full relative">
                        {playerLoading && !showAdBlockModal && (
                            <div className="absolute inset-0 bg-black flex items-center justify-center z-20">
                                <LoadingSpinner size="lg" />
                            </div>
                        )}

                        {!showAdBlockModal && error ? (
                            <div className="absolute inset-0 flex items-center justify-center z-10 p-6">
                                <div className="text-center space-y-6 max-w-md animate-fade-in">
                                    <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <svg className="w-10 h-10 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                        </svg>
                                    </div>
                                    <p className="text-xl sm:text-2xl font-black text-white leading-tight">
                                        {error}
                                    </p>
                                    <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
                                        <button
                                            onClick={() => selectedLink && handleServerSelect(selectedLink)}
                                            className="px-8 py-3 bg-primary text-white font-black rounded-xl hover:bg-red-700 transition-all shadow-lg active:scale-95"
                                        >
                                            Try Primary Server
                                        </button>
                                        <button
                                            onClick={handleRefreshLinks}
                                            className="px-8 py-3 bg-white/10 text-white font-black rounded-xl hover:bg-white/20 transition-all border border-white/10 active:scale-95"
                                        >
                                            Refresh Links
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : !showAdBlockModal && isHlsOrDirect ? (
                            <video ref={videoRef} className="w-full h-full object-contain" controls autoPlay />
                        ) : !showAdBlockModal && (
                            <iframe
                                ref={iframeRef}
                                className="w-full h-full border-0"
                                allowFullScreen
                                allow="autoplay; encrypted-media; picture-in-picture"
                            />
                        )}
                    </div>
                </div>

                {/* Content Section below player */}
                <div className="w-full max-w-7xl mt-12 space-y-12">

                    {/* Metadata & Server Selection */}
                    <div className="grid grid-cols-1 gap-12">
                        <div className="space-y-6">
                            {/* Header Info */}
                            <div className="space-y-4 text-center md:text-left">
                                <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-tight">{movie.title}</h1>
                                <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 sm:gap-4 text-xs sm:text-sm md:text-base text-gray-400 font-medium">
                                    <span className="text-green-500 font-bold">{matchPercentage}% Match</span>
                                    {movie.average_rating !== undefined && movie.average_rating > 0 && (
                                        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-yellow-400/10 border border-yellow-400/20 rounded-md">
                                            <span className="text-yellow-400 text-xs font-black">⭐</span>
                                            <span className="text-yellow-400 font-bold">
                                                {Math.round((movie.average_rating / 5) * 100)}%
                                                <span className="text-[10px] ml-1 opacity-70 uppercase tracking-tighter">User Score</span>
                                            </span>
                                        </div>
                                    )}
                                    <span>{movie.year}</span>
                                    <span className="border border-white/40 px-1.5 rounded text-xs text-white">HD</span>
                                    <span className="capitalize">{movie.content_type}</span>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center justify-center md:justify-start gap-6 pb-6 border-b border-gray-800">
                                <button
                                    onClick={() => addToList(movie.imdb_id)}
                                    className="flex flex-col items-center gap-1 group text-gray-400 hover:text-white transition-colors"
                                >
                                    <div className={`w-8 h-8 flex items-center justify-center border-2 rounded-full transition-colors ${isInList(movie.imdb_id) ? 'border-primary text-primary' : 'border-gray-500 group-hover:border-white'}`}>
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isInList(movie.imdb_id) ? 'M5 13l4 4L19 7' : 'M12 4v16m8-8H4'} />
                                        </svg>
                                    </div>
                                    <span className="text-xs font-bold uppercase tracking-wider">My List</span>
                                </button>

                                <button
                                    onClick={scrollToReviews}
                                    className="flex flex-col items-center gap-1 group text-gray-400 hover:text-white transition-colors"
                                >
                                    <div className={`w-8 h-8 flex items-center justify-center border-2 rounded-full transition-colors ${isFavorite(movie.imdb_id) ? 'border-primary text-primary' : 'border-gray-500 group-hover:border-white'}`}>
                                        <svg className={`w-4 h-4 ${isFavorite(movie.imdb_id) ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                                        </svg>
                                    </div>
                                    <span className="text-xs font-bold uppercase tracking-wider">Rate</span>
                                </button>
                            </div>

                            {/* Synopsis */}
                            <div className="text-base sm:text-lg leading-relaxed text-center md:text-left text-gray-300 max-w-4xl mx-auto md:mx-0 px-2 sm:px-0">
                                {movie.synopsis || "No synopsis available."}
                            </div>

                            {/* Extended Details */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-gray-800">
                                {movieMetadata && (
                                    <>
                                        {/* Left Side: Credits */}
                                        <div className="space-y-4">
                                            {movieMetadata.directors?.length > 0 && (
                                                <div>
                                                    <h4 className="text-gray-500 font-bold uppercase text-xs tracking-widest mb-1">Director</h4>
                                                    <p className="text-white font-medium">{movieMetadata.directors.join(', ')}</p>
                                                </div>
                                            )}
                                            {movieMetadata.writers?.length > 0 && (
                                                <div>
                                                    <h4 className="text-gray-500 font-bold uppercase text-xs tracking-widest mb-1">Writer</h4>
                                                    <p className="text-white font-medium">{movieMetadata.writers.join(', ')}</p>
                                                </div>
                                            )}
                                            {movieMetadata.genres?.length > 0 && (
                                                <div>
                                                    <h4 className="text-gray-500 font-bold uppercase text-xs tracking-widest mb-1">Genres</h4>
                                                    <div className="flex flex-wrap gap-2 mt-1">
                                                        {movieMetadata.genres.map((g: string) => (
                                                            <span key={g} className="text-xs bg-dark-800 px-2 py-1 rounded border border-white/5">{g}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Right Side: Technical Info */}
                                        <div className="space-y-4 text-sm">
                                            {movieMetadata.original_title && (
                                                <div>
                                                    <span className="text-gray-500">Original Title: </span>
                                                    <span className="text-gray-300">{movieMetadata.original_title}</span>
                                                </div>
                                            )}
                                            {movieMetadata.status && (
                                                <div>
                                                    <span className="text-gray-500">Status: </span>
                                                    <span className="text-gray-300">{movieMetadata.status}</span>
                                                </div>
                                            )}
                                            {movieMetadata.original_language && (
                                                <div>
                                                    <span className="text-gray-500">Language: </span>
                                                    <span className="text-gray-300 uppercase">{movieMetadata.original_language}</span>
                                                </div>
                                            )}
                                            {movieMetadata.budget > 0 && (
                                                <div>
                                                    <span className="text-gray-500">Budget: </span>
                                                    <span className="text-gray-300">${(movieMetadata.budget / 1000000).toFixed(1)}M</span>
                                                </div>
                                            )}
                                            {movieMetadata.revenue > 0 && (
                                                <div>
                                                    <span className="text-gray-500">Revenue: </span>
                                                    <span className="text-gray-300">${(movieMetadata.revenue / 1000000).toFixed(1)}M</span>
                                                </div>
                                            )}
                                            {movieMetadata.keywords?.length > 0 && (
                                                <div className="pt-2">
                                                    <h4 className="text-gray-500 font-bold uppercase text-[10px] tracking-widest mb-1">Keywords</h4>
                                                    <div className="flex flex-wrap gap-1">
                                                        {movieMetadata.keywords.slice(0, 10).map((k: string) => (
                                                            <span key={k} className="text-[10px] text-gray-500 italic">#{k.replace(/\s+/g, '')}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Server Selection */}
                            <div className="pt-6">
                                <div className="flex items-center justify-between mb-3 text-center md:text-left">
                                    <h3 className="text-gray-400 font-bold uppercase text-sm tracking-wider">Streaming Servers</h3>
                                    <button onClick={handleRefreshLinks} disabled={refreshing} className="text-xs text-gray-500 hover:text-white uppercase font-bold tracking-wider disabled:opacity-50">
                                        {refreshing ? 'Refreshing...' : 'Refresh'}
                                    </button>
                                </div>
                                <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                                    {activeLinks.map(link => (
                                        <button
                                            key={link.id}
                                            onClick={() => handleServerSelect(link)}
                                            className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${selectedLink?.id === link.id
                                                ? 'bg-white text-black shadow-lg scale-105'
                                                : 'bg-dark-800 text-gray-300 hover:bg-dark-700'
                                                }`}
                                        >
                                            {link.server_name}
                                            {link.quality && <span className="ml-2 text-xs opacity-75 font-normal">{link.quality}</span>}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* TV Show: Seasons & Episodes */}
                    {movie.content_type === 'series' && movie.metadata?.seasons && (
                        <div className="space-y-6 animate-fade-in py-8 border-y border-gray-800/50">
                            <div className="flex items-center justify-between">
                                <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                                    <span className="text-primary text-3xl">▦</span> Episodes
                                </h3>

                                {/* Season Selector */}
                                <div className="relative">
                                    <select
                                        value={selectedSeason}
                                        onChange={(e) => {
                                            setSelectedSeason(Number(e.target.value));
                                            setSelectedEpisode(1); // Reset episode
                                        }}
                                        className="appearance-none bg-dark-800 border border-gray-700 text-white py-2 pl-4 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary cursor-pointer font-semibold transition-all hover:bg-dark-700"
                                    >
                                        {movie.metadata?.seasons.map(season => (
                                            <option key={season.season_number} value={season.season_number}>
                                                {season.name || `Season ${season.season_number}`}
                                            </option>
                                        ))}
                                    </select>
                                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-400">
                                        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
                                    </div>
                                </div>
                            </div>

                            {/* Enhanced Visibility Episode Selector */}
                            <div className="mt-8 bg-black/40 rounded-2xl border border-white/5 p-6 backdrop-blur-sm">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3">
                                        <div className="w-1 h-6 bg-primary rounded-full" />
                                        <h4 className="text-xs font-black uppercase tracking-[0.25em] text-gray-400">Select Episode</h4>
                                    </div>
                                    <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest">
                                        Season {selectedSeason} • {movie.metadata?.seasons.find(s => s.season_number === selectedSeason)?.episode_count || 0} Episodes
                                    </div>
                                </div>

                                <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 xl:grid-cols-14 gap-2.5">
                                    {Array.from({ length: movie.metadata?.seasons.find(s => s.season_number === selectedSeason)?.episode_count || 0 }).map((_, idx) => {
                                        const episodeNum = idx + 1;
                                        const isSelected = selectedEpisode === episodeNum;

                                        return (
                                            <button
                                                key={episodeNum}
                                                onClick={() => setSelectedEpisode(episodeNum)}
                                                className={`h-10 w-10 flex items-center justify-center rounded-xl text-sm font-black transition-all duration-300 border ${isSelected
                                                    ? 'bg-primary border-primary text-white shadow-[0_0_25px_rgba(229,9,20,0.4)] z-10 scale-110'
                                                    : 'bg-white/5 border-white/10 text-gray-500 hover:bg-white/10 hover:border-white/30 hover:text-white'
                                                    }`}
                                            >
                                                {episodeNum < 10 ? `0${episodeNum}` : episodeNum}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Review Section */}
                    {movie && (
                        <div ref={reviewSectionRef}>
                            <ReviewSection
                                imdbId={movie.imdb_id}
                                reviews={movie.reviews || []}
                                onReviewAdded={loadMovie}
                            />
                        </div>
                    )}
                </div>

            </div>

            {/* Recommended for You - Full Width Carousel */}
            <div className="w-full mt-12 mb-12 bg-black/20">
                <MovieCarousel title="Recommended for You" movies={relatedMovies} />
            </div>
        </div>
    );
};
