// Badge component - Colored badges for quality, language, rating, etc.

import React from 'react';

interface BadgeProps {
    variant: 'quality' | 'language' | 'rating' | 'source' | 'type';
    text: string;
    className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant, text, className = '' }) => {
    const getVariantClasses = () => {
        switch (variant) {
            case 'quality':
                return 'bg-green-600 text-white';
            case 'language':
                return 'bg-blue-600 text-white';
            case 'rating':
                return 'bg-yellow-600 text-black';
            case 'source':
                return 'bg-dark-700 text-white';
            case 'type':
                return 'bg-primary/80 text-white backdrop-blur-sm';
            default:
                return 'bg-dark-600 text-white';
        }
    };

    return (
        <span
            className={`inline-block px-2 py-0.5 text-xs font-semibold rounded ${getVariantClasses()} ${className}`}
        >
            {text}
        </span>
    );
};
