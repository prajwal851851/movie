// Pagination component - Styled navigation buttons to match user design requirements

import React from 'react';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
    currentPage,
    totalPages,
    onPageChange,
}) => {
    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        const maxVisible = 5;

        if (totalPages <= maxVisible) {
            // Show all pages if total is small
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Always show first page
            pages.push(1);

            const start = Math.max(2, currentPage - 1);
            const end = Math.min(totalPages - 1, currentPage + 1);

            if (start > 2) {
                pages.push('...');
            }

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (end < totalPages - 1) {
                pages.push('...');
            }

            // Always show last page
            if (totalPages > 1) {
                pages.push(totalPages);
            }
        }

        return pages;
    };

    const pages = getPageNumbers();

    return (
        <div className="flex items-center justify-center gap-2 sm:gap-4 my-10 animate-fade-in">
            {/* Previous Button */}
            <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="w-10 h-10 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/5 transition-all disabled:opacity-10 disabled:cursor-not-allowed group"
                aria-label="Previous page"
            >
                <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
                </svg>
            </button>

            {/* Page Numbers */}
            <div className="flex items-center gap-1 sm:gap-2">
                {pages.map((page, index) => {
                    if (page === '...') {
                        return (
                            <span key={`ellipsis-${index}`} className="w-10 h-10 flex items-center justify-center text-white/40 tracking-widest">
                                ...
                            </span>
                        );
                    }

                    const pageNum = page as number;
                    const isActive = pageNum === currentPage;

                    return (
                        <button
                            key={pageNum}
                            onClick={() => onPageChange(pageNum)}
                            className={`w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center rounded-full text-lg font-bold transition-all duration-300 ${isActive
                                ? 'bg-primary text-white shadow-[0_0_20px_rgba(234,22,22,0.4)] scale-110 z-10'
                                : 'text-white hover:bg-white/5 hover:text-white'
                                }`}
                        >
                            {pageNum}
                        </button>
                    );
                })}
            </div>

            {/* Next Button */}
            <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="w-10 h-10 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/5 transition-all disabled:opacity-10 disabled:cursor-not-allowed group"
                aria-label="Next page"
            >
                <svg className="w-5 h-5 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                </svg>
            </button>

            {/* Last Page Button */}
            {totalPages > 5 && currentPage < totalPages - 2 && (
                <button
                    onClick={() => onPageChange(totalPages)}
                    className="w-10 h-10 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/5 transition-all font-black text-2xl"
                    aria-label="Skip to last page"
                >
                    »
                </button>
            )}
        </div>
    );
};
