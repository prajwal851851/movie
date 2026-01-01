// Home page - Hero section + multiple carousels

import React, { useState, useEffect } from 'react';
import { FeaturedMovieHero } from '../components/FeaturedMovieHero';
import { MovieCarousel } from '../components/MovieCarousel';
import { ContinueWatchingSidebar } from '../components/ContinueWatchingSidebar';
import { SkeletonHero, SkeletonCarousel } from '../components/LoadingSpinner';
import { apiService } from '../services/api.service';
import { useApp } from '../context/AppContext';
import type { Movie } from '../types';

export const Home: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [heroMovie, setHeroMovie] = useState<Movie | null>(null);
    const [trendingMovies, setTrendingMovies] = useState<Movie[]>([]);
    const [newReleases, setNewReleases] = useState<Movie[]>([]);
    const [popularMovies, setPopularMovies] = useState<Movie[]>([]);
    const [popularSeries, setPopularSeries] = useState<Movie[]>([]);
    const [kidsMovies, setKidsMovies] = useState<Movie[]>([]);
    const [animationContent, setAnimationContent] = useState<Movie[]>([]);

    useApp();

    useEffect(() => {
        loadContent();
    }, []);

    const loadContent = async () => {
        try {
            setLoading(true);

            // STAGE 1: Top priority content (Hero + First 3 Carousels)
            const [
                heroData,
                trendingData,
                newReleasesData,
                seriesData
            ] = await Promise.all([
                apiService.getMovies({ content_type: 'movie', year: 2025, limit: 30, ordering: 'random' }),
                apiService.getMovies({ content_type: 'movie', year_min: 2023, year_max: 2025, limit: 20, ordering: 'random' }),
                apiService.getMovies({ content_type: 'movie', year: 2025, limit: 20, ordering: 'random' }),
                apiService.getMovies({ content_type: 'series', year_min: 2017, year_max: 2025, limit: 20, ordering: 'random' })
            ]);

            // Set Stage 1 State
            setTrendingMovies(trendingData.results);
            setNewReleases(newReleasesData.results);
            setPopularSeries(seriesData.results);

            // Set Hero Slider
            const validHeroMovies = [
                ...heroData.results.filter(m => m.poster_url).slice(0, 10),
                ...seriesData.results.filter(m => m.poster_url).slice(0, 5)
            ].sort(() => Math.random() - 0.5);

            if (validHeroMovies.length > 0) {
                setHeroMovie(validHeroMovies[0]);
            } else if (heroData.results.length > 0) {
                setHeroMovie(heroData.results[0]);
            }

            // Immediately show first stage
            setLoading(false);

            // STAGE 2: Secondary content (Lower carousels)
            // We run this separately so the user can see the top content instantly
            const [
                popularData,
                kidsData,
                animationContentData
            ] = await Promise.all([
                apiService.getMovies({ content_type: 'movie', year_min: 2017, year_max: 2025, limit: 20, ordering: 'random' }),
                apiService.getMovies({ is_kids: true, year_min: 2017, year_max: 2025, limit: 20, ordering: 'random' }),
                apiService.getMovies({ genre: 'Animation', year_min: 2017, year_max: 2025, limit: 20, ordering: 'random' })
            ]);

            setPopularMovies(popularData.results);
            setKidsMovies(kidsData.results);
            setAnimationContent(animationContentData.results);

        } catch (error) {
            console.error('Error loading home content:', error);
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-dark-900 pb-20">
                <SkeletonHero />
                <div className="relative z-20 -mt-20 px-6 md:px-12">
                    <div className="flex flex-col md:flex-row gap-8">
                        <div className="flex-1 space-y-12 min-w-0">
                            <SkeletonCarousel title={true} />
                            <SkeletonCarousel title={true} />
                            <SkeletonCarousel title={true} />
                        </div>
                        <aside className="md:w-72 lg:w-80 shrink-0 hidden md:block">
                            <div className="bg-dark-800/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 h-96 animate-pulse" />
                        </aside>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 pb-20">
            {/* Hero Slider */}
            {heroMovie && <FeaturedMovieHero movie={heroMovie} />}

            {/* Content Sections */}
            <div className="relative z-20 -mt-20 px-6 md:px-12">
                <div className="flex flex-col md:flex-row gap-8">
                    {/* Main Content (Carousels) */}
                    <div className="flex-1 space-y-12 min-w-0">
                        {/* New Releases */}
                        <MovieCarousel
                            title="New Releases"
                            movies={newReleases}
                            viewAllLink="/movies"
                        />

                        {/* Trending Now */}
                        <MovieCarousel
                            title="Trending Now"
                            movies={trendingMovies}
                            viewAllLink="/trending"
                        />

                        {/* Popular TV Shows */}
                        <MovieCarousel
                            title="Popular TV Shows"
                            movies={popularSeries}
                            viewAllLink="/tv-shows"
                        />
                    </div>

                    {/* Sidebar */}
                    <aside className="md:w-72 lg:w-80 shrink-0">
                        <ContinueWatchingSidebar />
                    </aside>
                </div>

                {/* Full Width Sections - Filling vacant space below sidebar */}
                <div className="mt-12 space-y-12">
                    {/* Popular Movies */}
                    <MovieCarousel
                        title="Popular Movies"
                        movies={popularMovies}
                        viewAllLink="/movies"
                    />

                    {/* Kids Choice Section */}
                    {kidsMovies.length > 0 && (
                        <MovieCarousel
                            title="🧸 Kids Choice"
                            movies={kidsMovies}
                            viewAllLink="/kids"
                        />
                    )}

                    {/* Animation Section */}
                    {animationContent.length > 0 && (
                        <MovieCarousel
                            title="🎨 Animation"
                            movies={animationContent}
                            viewAllLink="/movies?genre=Animation"
                        />
                    )}
                </div>
            </div>
        </div>
    );
};
