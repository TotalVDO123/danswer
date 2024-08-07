import React, { useState, useEffect, useRef } from "react";

export default function GeneratingImage({ isCompleted = false }) {
  const [progress, setProgress] = useState(0);
  const progressRef = useRef(0);
  const animationRef = useRef<number>();
  const startTimeRef = useRef<number>(Date.now());

  useEffect(() => {
    let lastUpdateTime = 0;
    const updateInterval = 500; // Update at most every 500ms
    const animationDuration = 30000; // Animation will take 30 seconds to reach ~99%

    const animate = (timestamp: number) => {
      const elapsedTime = timestamp - startTimeRef.current;

      // Slower logarithmic curve
      const maxProgress = 99.9;
      const progress =
        maxProgress * (1 - Math.exp(-elapsedTime / animationDuration));

      // Only update if enough time has passed since the last update
      if (timestamp - lastUpdateTime > updateInterval) {
        progressRef.current = progress;
        setProgress(Math.round(progress * 10) / 10); // Round to 1 decimal place
        lastUpdateTime = timestamp;
      }

      if (!isCompleted && elapsedTime < animationDuration) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    startTimeRef.current = performance.now();
    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isCompleted]);

  useEffect(() => {
    if (isCompleted) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      setProgress(100);
    }
  }, [isCompleted]);

  return (
    <div className="object-cover object-center border border-neutral-200 bg-neutral-100 items-center justify-center overflow-hidden flex rounded-lg w-96 h-96 transition-opacity duration-300 opacity-100">
      <div className="m-auto relative flex">
        <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 100 100">
          <circle
            className="text-gray-200"
            strokeWidth="8"
            stroke="currentColor"
            fill="transparent"
            r="44"
            cx="50"
            cy="50"
          />
          <circle
            className="text-gray-800 transition-all duration-300"
            strokeWidth="8"
            strokeDasharray={276.46}
            strokeDashoffset={276.46 * (1 - progress / 100)}
            strokeLinecap="round"
            stroke="currentColor"
            fill="transparent"
            r="44"
            cx="50"
            cy="50"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <svg
            className="w-6 h-6 text-neutral-500 animate-pulse-strong"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
