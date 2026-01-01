import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { InstantSearch } from './InstantSearch';
import { apiService } from '../services/api.service';

export const Navigation: React.FC = () => {
    const { user, isAuthenticated, logout } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [scrolled, setScrolled] = useState(false);
    const [searchOpen, setSearchOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [profileMenuOpen, setProfileMenuOpen] = useState(false);
    const [genreMenuOpen, setGenreMenuOpen] = useState(false);
    const [creditsOpen, setCreditsOpen] = useState(false);
    const [genres, setGenres] = useState<string[]>([]);
    const genreMenuRef = useRef<HTMLDivElement>(null);

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

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll);

        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            if (!target.closest('.profile-menu-container')) {
                setProfileMenuOpen(false);
            }
            if (genreMenuRef.current && !genreMenuRef.current.contains(event.target as Node)) {
                setGenreMenuOpen(false);
            }
        };
        window.addEventListener('mousedown', handleClickOutside);


        return () => {
            window.removeEventListener('scroll', handleScroll);
            window.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);



    const handleLogout = () => {
        logout();
        navigate('/');
        setProfileMenuOpen(false);
    };


    const navLinks = [
        { path: '/', label: 'Home' },
        { path: '/movies', label: 'Movies' },
        { path: '/tv-shows', label: 'TV Shows' },
        { path: '/kids', label: 'Kids' },
        { path: '/upcoming', label: 'Upcoming' },
        { path: '/shuffle', label: 'Shuffle' },
        { path: '/trending', label: 'Trending' },
        { path: '/my-list', label: 'My List' },
        { path: '/favorites', label: 'Favorites' },
    ];

    return (
        <nav
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-dark-900 shadow-xl' : 'bg-gradient-to-b from-black/80 to-transparent'
                }`}
        >
            <div className="max-w-[1440px] mx-auto pl-8 pr-4 py-4">
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-2 group">
                        <span className="text-primary text-2xl md:text-3xl font-black group-hover:scale-105 transition-transform">StreamFlix</span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center gap-6">
                        {navLinks.map((link) => (
                            <React.Fragment key={link.path}>
                                <Link
                                    to={link.path}
                                    className={`text-sm font-semibold transition-all duration-200 hover:scale-105 ${location.pathname === link.path
                                        ? 'text-white'
                                        : 'text-dark-300 hover:text-white'
                                        }`}
                                >
                                    {link.label}
                                </Link>

                                {link.path === '/kids' && (
                                    <div className="relative" ref={genreMenuRef}>
                                        <button
                                            onClick={() => setGenreMenuOpen(!genreMenuOpen)}
                                            className={`text-sm font-semibold transition-all duration-200 hover:scale-105 flex items-center gap-1 ${genreMenuOpen || location.search.includes('genre')
                                                ? 'text-white'
                                                : 'text-dark-300 hover:text-white'
                                                }`}
                                        >
                                            Genres
                                            <svg
                                                className={`w-3 h-3 transition-transform duration-300 ${genreMenuOpen ? 'rotate-180' : ''}`}
                                                fill="none"
                                                stroke="currentColor"
                                                viewBox="0 0 24 24"
                                            >
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </button>

                                        {genreMenuOpen && (
                                            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-4 w-64 bg-dark-900/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 animate-fade-in py-2">
                                                <div className="max-h-[350px] overflow-y-auto custom-scrollbar px-2">
                                                    {genres.map((genre) => (
                                                        <button
                                                            key={genre}
                                                            onClick={() => {
                                                                navigate(`/movies?genre=${encodeURIComponent(genre)}`);
                                                                setGenreMenuOpen(false);
                                                            }}
                                                            className="w-full text-left px-4 py-2.5 text-sm font-semibold text-dark-200 hover:text-white hover:bg-white/5 rounded-xl transition-all"
                                                        >
                                                            {genre}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </React.Fragment>
                        ))}
                    </div>

                    {/* Right Side Actions */}
                    <div className="flex items-center gap-8 translate-x-1">
                        {/* Search */}
                        <div className="relative">
                            {searchOpen ? (
                                <div className="flex items-center">
                                    <div className="relative animate-slide-in-right">
                                        <InstantSearch
                                            value={searchQuery}
                                            onChange={(val) => {
                                                setSearchQuery(val);
                                            }}
                                            placeholder="Search titles..."
                                            className="w-64"
                                            autoFocus
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setSearchOpen(false);
                                            setSearchQuery('');
                                        }}
                                        className="ml-3 text-dark-400 hover:text-white transition-all transform hover:rotate-90"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setSearchOpen(true)}
                                    className="p-2 text-white hover:text-primary transition-all hover:scale-110"
                                    aria-label="Search"
                                >
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                </button>
                            )}
                        </div>

                        {/* Profile / Login */}
                        <div className="flex items-center gap-4">
                            {isAuthenticated ? (
                                <div className="relative profile-menu-container">
                                    <button
                                        onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                                        className="flex items-center gap-2 group p-1"
                                    >
                                        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-primary to-red-400 flex items-center justify-center text-white font-black text-sm shadow-lg group-hover:scale-105 transition-all">
                                            {user?.email[0].toUpperCase()}
                                        </div>
                                    </button>


                                    {profileMenuOpen && (
                                        <div className="absolute top-full right-0 mt-2 w-56 glass-dark border border-white/10 rounded-2xl shadow-2xl py-3 px-2 z-50 animate-fade-in text-left">
                                            <div className="px-4 py-3 border-b border-white/5 mb-2">
                                                <p className="text-xs text-gray-400 font-medium">Account</p>
                                                <p className="text-sm text-white font-bold truncate">{user?.email}</p>
                                            </div>
                                            <Link to="/profile" className="flex items-center gap-3 px-4 py-2 text-sm text-dark-200 hover:bg-white/5 hover:text-white rounded-xl transition-all">
                                                My Profile
                                            </Link>
                                            <button
                                                onClick={handleLogout}
                                                className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-500 hover:bg-red-500/10 rounded-xl transition-all font-semibold"
                                            >
                                                Sign Out
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <Link
                                    to="/login"
                                    className="px-6 py-2 bg-primary hover:bg-red-700 text-white font-bold text-sm rounded-full shadow-lg shadow-primary/20 transition-all transform hover:scale-105 active:scale-95"
                                >
                                    Sign In
                                </Link>
                            )}

                            {/* Credit Button */}
                            <button
                                onClick={() => setCreditsOpen(true)}
                                className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center text-white/60 hover:text-primary hover:border-primary transition-all font-black text-xs hover:scale-110"
                                title="Developer Credits"
                            >
                                C
                            </button>
                        </div>
                    </div>
                </div>

                {/* Credits Modal */}
                {creditsOpen && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 animate-fade-in">
                        <div
                            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                            onClick={() => setCreditsOpen(false)}
                        />
                        <div className="relative bg-dark-900 border border-white/10 rounded-3xl p-8 max-w-md w-full shadow-2xl animate-scale-in text-center overflow-hidden">
                            {/* Decorative background circle */}
                            <div className="absolute -top-20 -right-20 w-40 h-40 bg-primary/20 rounded-full blur-3xl" />
                            <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl" />

                            <div className="relative">
                                <div className="w-20 h-20 bg-gradient-to-tr from-primary to-red-400 rounded-2xl mx-auto mb-6 flex items-center justify-center text-white text-3xl font-black shadow-xl rotate-3">
                                    PD
                                </div>
                                <h3 className="text-2xl font-black text-white mb-2">Prajwal Dhital</h3>
                                <p className="text-primary font-bold uppercase tracking-widest text-xs mb-6">Computer Engineering Student</p>

                                <div className="space-y-4 text-left">
                                    <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
                                        <h4 className="text-sm font-bold text-gray-400 uppercase tracking-tighter mb-2">Tech Stack</h4>
                                        <div className="flex flex-wrap gap-2">
                                            {['Python', 'Django', 'Django Rest Framework', 'React', 'PostgreSQL', 'Tailwind CSS'].map(tech => (
                                                <span key={tech} className="px-3 py-1 bg-dark-800 rounded-full text-xs font-semibold text-white/80 border border-white/5 whitespace-nowrap">
                                                    {tech}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <p className="text-dark-300 text-sm leading-relaxed px-2 italic">
                                        "This website was crafted for learning the full potential of backend and frontend development. Focused on high-performance movie scraping and seamless user experiences."
                                    </p>
                                </div>

                                <button
                                    onClick={() => setCreditsOpen(false)}
                                    className="mt-8 w-full py-3 bg-white/5 hover:bg-white/10 text-white font-bold rounded-2xl transition-all border border-white/5"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Mobile Navigation */}
                <div className="md:hidden mt-4 flex gap-4 overflow-x-auto no-scrollbar pb-2 mask-linear-right">
                    {navLinks.map((link) => (
                        <Link
                            key={link.path}
                            to={link.path}
                            className={`text-[13px] font-bold whitespace-nowrap transition-all duration-200 px-1 py-1 ${location.pathname === link.path
                                ? 'text-white border-b-2 border-primary'
                                : 'text-dark-300 border-b-2 border-transparent hover:text-white'
                                }`}
                        >
                            {link.label}
                        </Link>
                    ))}
                </div>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                .mask-linear-right {
                    -webkit-mask-image: linear-gradient(to right, black 85%, transparent 100%);
                    mask-image: linear-gradient(to right, black 85%, transparent 100%);
                }
                .no-scrollbar::-webkit-scrollbar {
                    display: none;
                }
                .no-scrollbar {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }
            `}} />
        </nav>
    );
};
