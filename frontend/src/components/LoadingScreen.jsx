import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Search, Github, Sparkles } from 'lucide-react';
import GitNovaLogo from './GitNovaLogo';

const loadingSteps = [
    { text: "Scanning GitHub Universe...", icon: Github },
    { text: "Analyzing Repository Difficulty...", icon: Search },
    { text: "Filtering Out Master Level Issues...", icon: Zap },
    { text: "Curating Your Personal Feed...", icon: Sparkles },
];

const LoadingScreen = () => {
    const [currentStep, setCurrentStep] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentStep((prev) => (prev < loadingSteps.length - 1 ? prev + 1 : prev));
        }, 800); // Change text every 800ms

        return () => clearInterval(timer);
    }, []);

    const CurrentIcon = loadingSteps[currentStep].icon;

    return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#0f172a] text-white">
            {/* Background Gradient Orbs */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-[100px] animate-pulse"></div>
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[100px] animate-pulse delay-700"></div>

            {/* Main Loader - GitNova Logo (Animated) */}
            <div className="relative mb-12">
                <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                    <GitNovaLogo className="w-32 h-32" static={false} />
                </motion.div>
            </div>

            {/* Dynamic Text with AnimatePresence */}
            <div className="h-16 flex flex-col items-center">
                <AnimatePresence mode='wait'>
                    <motion.div
                        key={currentStep}
                        initial={{ y: 10, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: -10, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="flex items-center gap-3"
                    >
                        <CurrentIcon className="w-5 h-5 text-indigo-400" />
                        <span className="text-xl font-medium tracking-wide bg-gradient-to-r from-indigo-200 to-purple-200 bg-clip-text text-transparent">
                            {loadingSteps[currentStep].text}
                        </span>
                    </motion.div>
                </AnimatePresence>
            </div>

            {/* Progress Bar */}
            <div className="w-64 h-1 bg-slate-800 rounded-full mt-8 overflow-hidden">
                <motion.div
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                    initial={{ width: "0%" }}
                    animate={{ width: "100%" }}
                    transition={{ duration: 3.5, ease: "easeInOut" }}
                />
            </div>
        </div>
    );
};

export default LoadingScreen;
