import React from 'react';

const GitNovaLogo = ({ className = "w-16 h-16", static: isStatic = true }) => {
    return (
        <div className={`relative flex items-center justify-center ${className}`}>
            {/* Background Glow Effect */}
            <div className="absolute inset-0 bg-indigo-500/20 rounded-full blur-xl" />

            <svg
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full relative z-10 drop-shadow-[0_0_8px_rgba(147,51,234,0.6)]"
            >
                <defs>
                    {/* Main Cosmic Gradient */}
                    <linearGradient id="cosmic-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#4f46e5" /> {/* Indigo-600 */}
                        <stop offset="50%" stopColor="#a855f7" /> {/* Purple-500 */}
                        <stop offset="100%" stopColor="#22d3ee" /> {/* Cyan-400 */}
                    </linearGradient>

                    {/* Star Gradient */}
                    <linearGradient id="star-gradient" x1="50%" y1="0%" x2="50%" y2="100%">
                        <stop offset="0%" stopColor="#ffffff" />
                        <stop offset="100%" stopColor="#22d3ee" /> {/* Cyan-500 */}
                    </linearGradient>
                </defs>

                {/* LAYER 1 (Bottom): The Nova Core 
            Renders first, so it sits BEHIND the rings.
        */}
                <g>
                    {/* Main 4-Point Nova Star */}
                    <path
                        d="M 50 30 L 54 46 L 70 50 L 54 54 L 50 70 L 46 54 L 30 50 L 46 46 Z"
                        fill="url(#star-gradient)"
                        className="drop-shadow-[0_0_15px_rgba(34,211,238,0.5)]"
                    />
                    {/* Center Core */}
                    <circle cx="50" cy="50" r="3" fill="#4f46e5" />
                </g>

                {/* LAYER 2 (Top): The Orbital Rings
            Renders second, so it sits ON TOP (Front).
        */}
                <g
                    className={`origin-center ${!isStatic ? 'animate-[spin_3s_linear_infinite]' : ''}`}
                    style={{ filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.5))" }}
                >
                    {/* Ring 1 - Elliptical Orbit */}
                    <ellipse
                        cx="50" cy="50" rx="40" ry="20"
                        transform="rotate(45 50 50)"
                        stroke="url(#cosmic-gradient)"
                        strokeWidth="3"
                        strokeLinecap="round"
                    />
                    {/* Ring 2 - Opposing Elliptical Orbit */}
                    <ellipse
                        cx="50" cy="50" rx="40" ry="20"
                        transform="rotate(-45 50 50)"
                        stroke="url(#cosmic-gradient)"
                        strokeWidth="3"
                        strokeLinecap="round"
                    />

                    {/* Tiny Nodes on the rings */}
                    <circle cx="50" cy="10" r="2" fill="#22d3ee" transform="rotate(45 50 50)" />
                    <circle cx="50" cy="90" r="2" fill="#a855f7" transform="rotate(-45 50 50)" />
                </g>

            </svg>
        </div>
    );
};

export default GitNovaLogo;
