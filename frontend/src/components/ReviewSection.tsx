import React, { useState } from 'react';
import { apiService } from '../services/api.service';
import type { Review } from '../types';
import { useAuth } from '../context/AuthContext';

interface ReviewSectionProps {
    imdbId: string;
    reviews: Review[];
    onReviewAdded: () => void;
}

export const ReviewSection: React.FC<ReviewSectionProps> = ({ imdbId, reviews: initialReviews, onReviewAdded }) => {
    const { user } = useAuth();
    const [rating, setRating] = useState(5);
    const [comment, setComment] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) {
            setError('Please login to leave a review');
            return;
        }

        try {
            setSubmitting(true);
            setError(null);
            await apiService.postReview({
                movie: imdbId,
                rating,
                comment
            });
            setComment('');
            onReviewAdded();
        } catch (err: any) {
            setError(err.message || 'Failed to post review');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="mt-12 bg-dark-800/50 backdrop-blur-md rounded-3xl p-8 border border-white/5">
            <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-4">
                <span className="text-yellow-400">⭐</span>
                <div className="flex flex-col">
                    <span>Community Reviews</span>
                    {initialReviews.length > 0 && (
                        <div className="flex items-center gap-2 mt-1">
                            <div className="flex text-yellow-500 text-xs">
                                {Array.from({ length: 5 }).map((_, i) => {
                                    const avg = initialReviews.reduce((acc, r) => acc + r.rating, 0) / initialReviews.length;
                                    return <span key={i} className={i < Math.round(avg) ? '' : 'text-dark-600'}>★</span>;
                                })}
                            </div>
                            <span className="text-dark-400 text-xs font-medium">
                                {(initialReviews.reduce((acc, r) => acc + r.rating, 0) / initialReviews.length).toFixed(1)} / 5.0
                            </span>
                        </div>
                    )}
                </div>
                <span className="text-sm font-normal text-dark-400 ml-auto bg-white/5 px-4 py-1 rounded-full border border-white/5">
                    {initialReviews.length} {initialReviews.length === 1 ? 'Review' : 'Reviews'}
                </span>
            </h2>

            {/* Review Form */}
            {user ? (
                <form onSubmit={handleSubmit} className="mb-12 bg-white/5 rounded-2xl p-6 border border-white/5">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="flex gap-1">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    type="button"
                                    onClick={() => setRating(star)}
                                    className={`text-2xl transition-all hover:scale-125 ${star <= rating ? 'text-yellow-400' : 'text-dark-500'
                                        }`}
                                >
                                    ★
                                </button>
                            ))}
                        </div>
                        <span className="text-sm font-bold text-yellow-400/80 uppercase tracking-widest">
                            {rating === 5 ? 'Masterpiece' : rating === 4 ? 'Great' : rating === 3 ? 'Good' : rating === 2 ? 'Meh' : 'Avoid'}
                        </span>
                    </div>

                    <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="Write your thoughts about this movie..."
                        className="w-full bg-dark-900/50 border border-white/10 rounded-xl p-4 text-white placeholder-dark-500 focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all resize-none h-24 mb-4"
                        required
                    />

                    {error && <p className="text-red-500 text-sm mb-4 bg-red-500/10 p-3 rounded-lg border border-red-500/20">{error}</p>}

                    <button
                        type="submit"
                        disabled={submitting}
                        className="bg-primary hover:bg-primary-hover text-white px-8 py-3 rounded-xl font-bold transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 flex items-center gap-2"
                    >
                        {submitting ? (
                            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                        ) : null}
                        {submitting ? 'Posting...' : 'Post Review'}
                    </button>
                </form>
            ) : (
                <div className="mb-12 bg-white/5 rounded-2xl p-8 border border-white/5 text-center">
                    <p className="text-dark-300 mb-4">You need to be logged in to share your thoughts!</p>
                    <button
                        onClick={() => window.location.href = '/login'}
                        className="bg-white/10 hover:bg-white/20 text-white px-8 py-2 rounded-full font-bold transition-all"
                    >
                        Sign In to Review
                    </button>
                </div>
            )}

            {/* Review List */}
            <div className="space-y-6 max-h-[500px] overflow-y-auto pr-6 custom-scrollbar scroll-smooth">
                {initialReviews.length > 0 ? (
                    initialReviews.map((review) => (
                        <div key={review.id} className="bg-white/5 rounded-2xl p-6 border border-white/5 animate-fade-in group hover:bg-white/[0.07] transition-all">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
                                        {(review.user_name || review.user_email || 'U')[0].toUpperCase()}
                                    </div>
                                    <div>
                                        <h4 className="text-white font-bold">
                                            {review.user_name || review.user_email.split('@')[0]}
                                        </h4>
                                        <div className="flex items-center gap-2">
                                            <div className="flex text-yellow-400 text-xs">
                                                {Array.from({ length: 5 }).map((_, i) => (
                                                    <span key={i} className={i < review.rating ? '' : 'text-dark-600'}>★</span>
                                                ))}
                                            </div>
                                            <span className="text-dark-500 text-[10px]">•</span>
                                            <span className="text-dark-500 text-xs">
                                                {new Date(review.created_at).toLocaleDateString(undefined, {
                                                    year: 'numeric',
                                                    month: 'short',
                                                    day: 'numeric'
                                                })}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <p className="text-dark-200 leading-relaxed italic border-l-2 border-primary/30 pl-4 py-1">
                                "{review.comment}"
                            </p>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-12 text-dark-500">
                        <span className="text-4xl block mb-4">🎭</span>
                        <p>No reviews yet. Be the first to share your thoughts!</p>
                    </div>
                )}
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                .custom-scrollbar::-webkit-scrollbar {
                    width: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #E50914;
                    border-radius: 10px;
                    border: 2px solid transparent;
                    background-clip: content-box;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #ff0f1a;
                    background-clip: content-box;
                }
            `}} />
        </div>
    );
};
