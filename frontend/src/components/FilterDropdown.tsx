import React, { useState, useRef, useEffect } from 'react';

interface FilterDropdownProps {
    label: string;
    value: string;
    options: string[];
    onChange: (value: string) => void;
}

export const FilterDropdown: React.FC<FilterDropdownProps> = ({
    label,
    value,
    options,
    onChange,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const selectedLabel = value || label;

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg border transition-all duration-300 min-w-[140px] justify-between
                    ${isOpen
                        ? 'bg-white/10 border-white/40 shadow-[0_0_20px_rgba(255,255,255,0.05)]'
                        : 'bg-black/40 border-white/10 hover:border-white/30'
                    }`}
            >
                <span className={`text-sm font-medium transition-colors ${value ? 'text-white' : 'text-gray-400'}`}>
                    {selectedLabel}
                </span>
                <svg
                    className={`w-4 h-4 text-gray-400 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {/* Dropdown Menu */}
            <div className={`absolute top-full left-0 mt-2 w-64 bg-dark-800/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl z-[100] transition-all duration-300 origin-top overflow-hidden
                ${isOpen
                    ? 'opacity-100 scale-100'
                    : 'opacity-0 scale-95 pointer-events-none'
                }`}
            >
                <div className="max-h-[300px] overflow-y-auto custom-scrollbar p-2">
                    <button
                        onClick={() => {
                            onChange('');
                            setIsOpen(false);
                        }}
                        className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-colors mb-1
                            ${!value ? 'bg-primary/20 text-primary font-bold' : 'text-gray-400 hover:bg-white/5 hover:text-white'}
                        `}
                    >
                        {label}
                    </button>
                    <div className="h-[1px] bg-white/5 my-1 mx-2" />
                    {options.map((option) => (
                        <button
                            key={option}
                            onClick={() => {
                                onChange(option);
                                setIsOpen(false);
                            }}
                            className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-colors mb-1
                                ${value === option ? 'bg-primary/20 text-primary font-bold' : 'text-gray-400 hover:bg-white/5 hover:text-white'}
                            `}
                        >
                            {option}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};
