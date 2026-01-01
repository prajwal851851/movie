import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiService } from '../../services/api.service';

export const Signup: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await apiService.register({ email, password });
            navigate('/verify-otp', { state: { email } });
        } catch (err: any) {
            setError(err.message || 'Registration failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen pt-20 flex items-center justify-center p-4 bg-dark-900 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

            <div className="w-full max-w-md glass-dark p-8 rounded-3xl border border-white/5 shadow-2xl animate-scale-in relative z-10">
                <div className="text-center mb-10">
                    <h1 className="text-4xl font-black text-white mb-2 tracking-tight">Join <span className="text-primary">StreamFlix</span></h1>
                    <p className="text-gray-400">Create an account to save your favorite movies.</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Email Address</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-dark-800 border border-white/5 rounded-xl px-5 py-4 text-white focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all"
                            placeholder="name@example.com"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-dark-800 border border-white/5 rounded-xl px-5 py-4 text-white focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all"
                            placeholder="Min. 8 characters"
                            minLength={8}
                            required
                        />
                    </div>

                    <p className="text-xs text-gray-500 leading-relaxed">
                        By signing up, you agree to our <span className="text-gray-300 underline cursor-pointer">Terms of Service</span> and <span className="text-gray-300 underline cursor-pointer">Privacy Policy</span>.
                    </p>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full py-4 bg-primary hover:bg-red-700 text-white font-bold rounded-xl shadow-lg shadow-primary/20 transition-all transform active:scale-[0.98] ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                    >
                        {loading ? 'Creating Account...' : 'Get Started'}
                    </button>
                </form>

                <p className="mt-8 text-center text-gray-400">
                    Already have an account? <Link to="/login" className="text-white font-bold hover:text-primary transition-colors ml-1">Sign in</Link>
                </p>
            </div>
        </div>
    );
};
