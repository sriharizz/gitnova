import React from 'react';

/**
 * GitNova Logo — Dual Orbital Rings with 4-Point Nova Star Core.
 * Styled with GitNova's signature cosmic emerald, mint, and cyan gradients.
 */
const GitNovaLogo = ({ className = "w-10 h-10", static: isStatic = true }) => {
    return (
        <div className={`relative flex items-center justify-center shrink-0 ${className}`}>
            {/* Background Glow Effect */}
            <div className="absolute inset-0 bg-emerald-500/25 rounded-full blur-xl" />

            <svg
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full relative z-10 drop-shadow-[0_0_8px_rgba(52,211,153,0.65)]"
            >
                <defs>
                    {/* Main Cosmic Emerald-Mint-Cyan Gradient */}
                    <linearGradient id="cosmic-emerald-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#059669" /> {/* Emerald-600 */}
                        <stop offset="50%" stopColor="#10B981" /> {/* Emerald-500 */}
                        <stop offset="100%" stopColor="#34D399" /> {/* Mint-400 */}
                    </linearGradient>

                    {/* Star Core Gradient */}
                    <linearGradient id="star-mint-gradient" x1="50%" y1="0%" x2="50%" y2="100%">
                        <stop offset="0%" stopColor="#FFFFFF" />
                        <stop offset="100%" stopColor="#34D399" /> {/* Mint-400 */}
                    </linearGradient>
                </defs>

                {/* LAYER 1 (Bottom): The Nova Star Core */}
                <g>
                    {/* Main 4-Point Nova Star */}
                    <path
                        d="M 50 30 L 54 46 L 70 50 L 54 54 L 50 70 L 46 54 L 30 50 L 46 46 Z"
                        fill="url(#star-mint-gradient)"
                        className="drop-shadow-[0_0_15px_rgba(52,211,153,0.7)]"
                    />
                    {/* Center Core Dot */}
                    <circle cx="50" cy="50" r="3" fill="#047857" />
                </g>

                {/* LAYER 2 (Top): The Dual Orbital Rings */}
                <g
                    className={`origin-center ${!isStatic ? 'animate-[spin_6s_linear_infinite]' : ''}`}
                    style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.4))" }}
                >
                    {/* Ring 1 - Elliptical Orbit */}
                    <ellipse
                        cx="50" cy="50" rx="40" ry="20"
                        transform="rotate(45 50 50)"
                        stroke="url(#cosmic-emerald-gradient)"
                        strokeWidth="3"
                        strokeLinecap="round"
                    />
                    {/* Ring 2 - Opposing Elliptical Orbit */}
                    <ellipse
                        cx="50" cy="50" rx="40" ry="20"
                        transform="rotate(-45 50 50)"
                        stroke="url(#cosmic-emerald-gradient)"
                        strokeWidth="3"
                        strokeLinecap="round"
                    />

                    {/* Luminous Nodes on the rings */}
                    <circle cx="50" cy="10" r="2.5" fill="#34D399" transform="rotate(45 50 50)" />
                    <circle cx="50" cy="90" r="2.5" fill="#22D3EE" transform="rotate(-45 50 50)" />
                </g>
            </svg>
        </div>
    );
};

export default GitNovaLogo;
