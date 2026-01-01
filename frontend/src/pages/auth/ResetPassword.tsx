// ResetPassword page - Enter OTP and new password

import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { apiService } from '../../services/api.service';

export const ResetPassword: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const emailParam = queryParams.get('email');
        if (emailParam) {
            setEmail(emailParam);
        } else {
            navigate('/forgot-password');
        }
    }, [location, navigate]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (newPassword.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }

        setLoading(true);
        setError('');

        try {
            await apiService.resetPassword({ email, otp, new_password: newPassword });
            setSuccess(true);

            setTimeout(() => {
                navigate('/login');
            }, 3000);
        } catch (err: any) {
            setError(err.message || 'Failed to reset password. Check your code and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-dark-900 flex items-center justify-center p-6 relative overflow-hidden">
            {/* Background Glows */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full animate-pulse" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-red-900/10 blur-[120px] rounded-full" />

            <div className="w-full max-w-md animate-scale-in relative z-10">
                <div className="glass-dark border border-white/10 rounded-3xl p-10 shadow-2xl">
                    <div className="text-center mb-10">
                        <Link to="/" className="inline-block mb-6">
                            <span className="text-primary text-4xl font-black tracking-tighter">StreamFlix</span>
                        </Link>
                        <h1 className="text-3xl font-black text-white tracking-tight mb-2">New Password</h1>
                        <p className="text-dark-400 font-medium">Reset your password for {email}</p>
                    </div>

                    {success ? (
                        <div className="bg-green-500/10 border border-green-500/20 text-green-400 p-6 rounded-2xl text-center animate-fade-in">
                            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <h3 className="font-bold text-lg mb-1">Success!</h3>
                            <p className="text-sm opacity-80">Your password has been reset successfully. Redirecting you to login...</p>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-6">
                            {error && (
                                <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-xl text-sm font-medium animate-shake">
                                    {error}
                                </div>
                            )}

                            <div>
                                <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2 ml-1">Verification Code</label>
                                <input
                                    type="text"
                                    required
                                    maxLength={6}
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                                    className="w-full bg-white/5 border border-white/10 text-white px-5 py-3 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono text-center text-xl tracking-widest"
                                    placeholder="000000"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2 ml-1">New Password</label>
                                <input
                                    type="password"
                                    required
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 text-white px-5 py-3 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                                    placeholder="••••••••"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-black uppercase tracking-widest text-dark-400 mb-2 ml-1">Confirm New Password</label>
                                <input
                                    type="password"
                                    required
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 text-white px-5 py-3 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                                    placeholder="••••••••"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-4 bg-primary hover:bg-red-700 text-white font-black text-sm uppercase tracking-widest rounded-2xl shadow-2xl transition-all transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <div className="flex items-center justify-center gap-2">
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Resetting...
                                    </div>
                                ) : 'Reset Password'}
                            </button>
                        </form>
                    )}

                    <div className="mt-10 text-center">
                        <Link to="/login" className="text-dark-400 hover:text-white text-sm font-bold transition-colors inline-flex items-center gap-2">
                            Back to Login
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};
