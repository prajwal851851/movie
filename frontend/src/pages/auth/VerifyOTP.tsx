import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { apiService } from '../../services/api.service';
import { useAuth } from '../../context/AuthContext';

export const VerifyOTP: React.FC = () => {
    const [otp, setOtp] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [resending, setResending] = useState(false);
    const [timer, setTimer] = useState(60);
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const email = location.state?.email || '';

    useEffect(() => {
        if (!email) {
            navigate('/signup');
            return;
        }

        const interval = setInterval(() => {
            setTimer((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);

        return () => clearInterval(interval);
    }, [email, navigate]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await apiService.verifyOTP(email, otp);
            login(data.access, data.refresh, data.user);
            navigate('/');
        } catch (err: any) {
            setError(err.message || 'Verification failed. Incorrect code.');
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        if (timer > 0) return;
        setResending(true);
        setError('');
        try {
            await apiService.resendOTP(email);
            setTimer(60);
        } catch (err: any) {
            setError(err.message || 'Failed to resend code.');
        } finally {
            setResending(false);
        }
    };

    return (
        <div className="min-h-screen pt-20 flex items-center justify-center p-4 bg-dark-900 relative overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

            <div className="w-full max-w-md glass-dark p-8 rounded-3xl border border-white/5 shadow-2xl animate-scale-in relative z-10">
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/20 rounded-2xl mb-6 text-primary">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04M12 21.355l2.263-5.23L12 13.844l-2.263 2.28L12 21.355z" />
                        </svg>

                    </div>
                    <h1 className="text-4xl font-black text-white mb-2 tracking-tight">Verify Email</h1>
                    <p className="text-gray-400">Enter the 6-digit code sent to <span className="text-white font-semibold">{email}</span></p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-8">
                    <input
                        type="text"
                        maxLength={6}
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                        className="w-full bg-dark-800 border-2 border-white/5 rounded-2xl px-5 py-6 text-center text-4xl font-bold tracking-[0.5em] text-white focus:border-primary outline-none transition-all placeholder:text-gray-700"
                        placeholder="000000"
                        required
                    />

                    <button
                        type="submit"
                        disabled={loading || otp.length < 6}
                        className={`w-full py-4 bg-primary hover:bg-red-700 text-white font-bold rounded-xl shadow-lg shadow-primary/20 transition-all transform active:scale-[0.98] ${loading || otp.length < 6 ? 'opacity-70 cursor-not-allowed' : ''}`}
                    >
                        {loading ? 'Verifying...' : 'Complete Registration'}
                    </button>
                </form>

                <div className="mt-8 text-center space-y-4">
                    <p className="text-gray-400 text-sm">
                        Didn't receive the code?
                        <button
                            onClick={handleResend}
                            disabled={timer > 0 || resending}
                            className={`ml-1 font-bold ${timer > 0 || resending ? 'text-gray-600 cursor-not-allowed' : 'text-primary hover:underline'}`}
                        >
                            {resending ? 'Resending...' : timer > 0 ? `Resend in ${timer}s` : 'Resend Now'}
                        </button>
                    </p>
                    <Link to="/signup" className="block text-gray-500 hover:text-white transition-colors text-sm">Use a different email</Link>
                </div>
            </div>
        </div>
    );
};
