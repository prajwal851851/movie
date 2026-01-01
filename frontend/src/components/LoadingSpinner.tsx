// Loading components - Spinners and skeleton loaders

import React from 'react';

export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
    const sizeClasses = {
        sm: 'w-6 h-6',
        md: 'w-12 h-12',
        lg: 'w-16 h-16',
    };

    return (
        <div className="flex items-center justify-center">
            <div
                className={`${sizeClasses[size]} border-4 border-dark-600 border-t-primary rounded-full animate-spin`}
            />
        </div>
    );
};

export const LoadingPage: React.FC = () => {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <LoadingSpinner size="lg" />
            <p className="mt-4 text-dark-400">Loading...</p>
        </div>
    );
};

export const SkeletonCard: React.FC = () => {
    return (
        <div className="animate-pulse">
            <div className="aspect-[2/3] bg-dark-800 rounded-card" />
            <div className="mt-2 space-y-2">
                <div className="h-4 bg-dark-800 rounded w-3/4" />
                <div className="h-3 bg-dark-800 rounded w-1/2" />
            </div>
        </div>
    );
};

export const SkeletonGrid: React.FC<{ count?: number }> = ({ count = 12 }) => {
    return (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {Array.from({ length: count }).map((_, i) => (
                <SkeletonCard key={i} />
            ))}
        </div>
    );
};
export const SkeletonHero: React.FC = () => {
    return (
        <div className="relative h-[50vh] md:h-[60vh] lg:h-[70vh] w-full bg-dark-900 animate-pulse">
            <div className="absolute inset-0 bg-dark-800" />
            <div className="absolute inset-0 bg-gradient-to-t from-dark-900 via-dark-900/60 to-transparent" />
            <div className="absolute bottom-0 left-0 w-full p-8 md:p-16 space-y-6">
                <div className="h-10 md:h-16 bg-dark-700 rounded-xl w-2/3 md:w-1/2" />
                <div className="flex gap-4">
                    <div className="h-6 bg-dark-700 rounded-lg w-20" />
                    <div className="h-6 bg-dark-700 rounded-lg w-20" />
                    <div className="h-6 bg-dark-700 rounded-lg w-20" />
                </div>
                <div className="h-4 bg-dark-700 rounded-lg w-full md:w-2/3" />
                <div className="h-4 bg-dark-700 rounded-lg w-1/2 md:w-1/3" />
                <div className="flex gap-4 pt-4">
                    <div className="h-12 bg-dark-700 rounded-xl w-32" />
                    <div className="h-12 bg-dark-700 rounded-xl w-32" />
                </div>
            </div>
        </div>
    );
};

export const SkeletonCarousel: React.FC<{ title?: boolean }> = ({ title = true }) => {
    return (
        <div className="space-y-4 mb-8">
            {title && <div className="h-8 bg-dark-800 rounded-lg w-48 ml-6 animate-pulse" />}
            <div className="flex gap-4 overflow-hidden px-6">
                {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                    <div key={i} className="flex-shrink-0 w-40 sm:w-48 animate-pulse">
                        <div className="aspect-[2/3] bg-dark-800 rounded-2xl" />
                        <div className="mt-3 space-y-2">
                            <div className="h-4 bg-dark-800 rounded-lg w-3/4" />
                            <div className="h-3 bg-dark-800 rounded-lg w-1/2" />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
