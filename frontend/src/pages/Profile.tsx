// Profile page - User settings with tabs

import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

type Tab = 'account' | 'preferences' | 'playback';

export const Profile: React.FC = () => {
    const { user, isAuthenticated, logout } = useAuth();
    const navigate = useNavigate();
    const { preferences, updatePreferences } = useApp();
    const [activeTab, setActiveTab] = useState<Tab>('account');
    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const tabs: { id: Tab; label: string }[] = [
        { id: 'account', label: 'Account' },
        { id: 'preferences', label: 'Preferences' },
        { id: 'playback', label: 'Playback' },
    ];

    return (
        <div className="min-h-screen bg-dark-900 pt-24 px-6">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-6 mb-8 animate-fade-in">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-primary to-red-400 flex items-center justify-center text-white text-3xl font-black shadow-2xl">
                        {isAuthenticated ? user?.email[0].toUpperCase() : '?'}
                    </div>
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">Profile Settings</h1>
                        <p className="text-dark-400 font-medium">Manage your account and viewing preferences</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-8 mb-8 border-b border-white/5 overflow-x-auto no-scrollbar">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`pb-4 px-1 font-bold text-sm uppercase tracking-widest transition-all whitespace-nowrap ${activeTab === tab.id
                                ? 'text-white border-b-2 border-primary'
                                : 'text-dark-400 hover:text-white'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="bg-dark-800/50 backdrop-blur-xl border border-white/5 rounded-3xl p-8 shadow-2xl animate-scale-in">
                    {/* Account Tab */}
                    {activeTab === 'account' && (
                        <div className="space-y-8">
                            {!isAuthenticated ? (
                                <div className="text-center py-12">
                                    <div className="bg-white/5 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <svg className="w-8 h-8 text-dark-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                        </svg>
                                    </div>
                                    <h2 className="text-white text-xl font-bold mb-2">Sign in to manage your account</h2>
                                    <p className="text-dark-400 mb-6">Create an account to sync your watchlist and favorites across devices.</p>
                                    <button onClick={() => navigate('/login')} className="px-8 py-3 bg-primary hover:bg-red-700 text-white font-bold rounded-xl transition-all">Sign In Now</button>
                                </div>
                            ) : (
                                <>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <div>
                                            <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2">Email Address</label>
                                            <input
                                                type="email"
                                                readOnly
                                                value={user?.email || ''}
                                                className="w-full bg-white/5 border border-white/10 text-white px-5 py-3 rounded-2xl focus:outline-none opacity-70 cursor-not-allowed font-medium"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2">Account Status</label>
                                            <div className="flex items-center gap-2 px-5 py-3 bg-green-500/10 border border-green-500/20 rounded-2xl text-green-400 font-bold text-sm">
                                                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                                                Active / Verified
                                            </div>
                                        </div>
                                    </div>

                                    <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row gap-4 items-center justify-between">
                                        <div>
                                            <h3 className="text-white font-bold">Sign Out</h3>
                                            <p className="text-xs text-dark-400">Sign out of your account on this device</p>
                                        </div>
                                        <button
                                            onClick={handleLogout}
                                            className="px-6 py-2.5 border border-red-500/30 text-red-500 hover:bg-red-500/10 font-bold text-sm rounded-xl transition-all"
                                        >
                                            Sign Out of StreamFlix
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {/* Preferences Tab */}
                    {activeTab === 'preferences' && (
                        <div className="space-y-6">
                            <div>
                                <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2">Interface Language</label>
                                <select
                                    value={preferences.language}
                                    onChange={(e) => updatePreferences({ language: e.target.value })}
                                    className="w-full bg-white/5 border border-white/10 text-white px-5 py-3 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/50 font-medium cursor-pointer"
                                >
                                    <option value="en">English (US)</option>
                                    <option value="es">Español</option>
                                    <option value="fr">Français</option>
                                    <option value="de">Deutsch</option>
                                </select>
                            </div>
                            <div>
                                <label className="flex items-center gap-4 cursor-pointer group">
                                    <div className="relative">
                                        <input
                                            type="checkbox"
                                            checked={preferences.subtitles}
                                            onChange={(e) => updatePreferences({ subtitles: e.target.checked })}
                                            className="sr-only peer"
                                        />
                                        <div className="w-12 h-6 bg-dark-600 rounded-full peer peer-checked:bg-primary transition-all after:content-[''] after:absolute after:top-1 after:left-1 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-6" />
                                    </div>
                                    <span className="text-white font-bold text-sm">Enable Subtitles by Default</span>
                                </label>
                            </div>
                            <div>
                                <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2">Display Theme</label>
                                <div className="grid grid-cols-2 gap-4">
                                    <button
                                        onClick={() => updatePreferences({ theme: 'dark' })}
                                        className={`p-4 rounded-2xl border ${preferences.theme === 'dark' ? 'border-primary bg-primary/10 text-white' : 'border-white/10 text-dark-400'} font-bold transition-all`}
                                    >
                                        Dark Mode
                                    </button>
                                    <button
                                        onClick={() => updatePreferences({ theme: 'light' })}
                                        className={`p-4 rounded-2xl border ${preferences.theme === 'light' ? 'border-primary bg-primary/10 text-white' : 'border-white/10 text-dark-400'} font-bold transition-all opacity-50 cursor-not-allowed`}
                                        disabled
                                    >
                                        Light Mode (Fixed)
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Playback Tab */}
                    {activeTab === 'playback' && (
                        <div className="space-y-6">
                            <div>
                                <label className="flex items-center gap-4 cursor-pointer group">
                                    <div className="relative">
                                        <input
                                            type="checkbox"
                                            checked={preferences.autoplay}
                                            onChange={(e) => updatePreferences({ autoplay: e.target.checked })}
                                            className="sr-only peer"
                                        />
                                        <div className="w-12 h-6 bg-dark-600 rounded-full peer peer-checked:bg-primary transition-all after:content-[''] after:absolute after:top-1 after:left-1 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-6" />
                                    </div>
                                    <span className="text-white font-bold text-sm">Autoplay Next Episode</span>
                                </label>
                            </div>
                            <div>
                                <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2">Default Video Quality</label>
                                <div className="flex flex-wrap gap-2">
                                    {['auto', 'hd', 'sd'].map((q) => (
                                        <button
                                            key={q}
                                            onClick={() => updatePreferences({ quality: q as any })}
                                            className={`px-6 py-2 rounded-full border text-xs font-black uppercase tracking-widest transition-all ${preferences.quality === q
                                                ? 'bg-white text-black border-white shadow-xl scale-105'
                                                : 'border-white/10 text-dark-400 hover:border-white/30'}`}
                                        >
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Save Button */}
                    <div className="mt-12 flex gap-4">
                        <button
                            onClick={handleSave}
                            className="flex-1 md:flex-none px-10 py-4 bg-primary hover:bg-red-700 text-white font-black text-sm uppercase tracking-widest rounded-2xl shadow-2xl transition-all active:scale-95"
                        >
                            {saved ? '✓ Changes Applied' : 'Update Profile'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
