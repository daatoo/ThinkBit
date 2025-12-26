import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface RetroCenterAnimationProps {
  currentStep: number;
}

const RetroCenterAnimation = ({ currentStep }: RetroCenterAnimationProps) => {
  const [frame, setFrame] = useState(0);

  // Animation loop (2 frames per second for retro feel)
  useEffect(() => {
    const interval = setInterval(() => {
      setFrame((f) => (f + 1) % 4);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Simple pixel-art style SVGs
  // We use simple shapes to mimic 8-bit sprites

  const renderGhost = () => (
    <svg viewBox="0 0 24 24" className={cn("w-16 h-16 text-primary drop-shadow-[0_0_8px_rgba(var(--primary),0.8)]", frame % 2 === 0 ? "translate-y-0" : "-translate-y-1 transition-transform duration-300")}>
      {/* Ghost body */}
      <path
        fill="currentColor"
        d="M2 12a10 10 0 0 1 20 0v8a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2v-1a1 1 0 0 0-1-1 1 1 0 0 0-1 1v1a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-1a1 1 0 0 0-1-1 1 1 0 0 0-1 1v1a2 2 0 0 1-2 2H2v-8z"
      />
      {/* Eyes */}
      <rect x="6" y="8" width="4" height="4" fill="black" />
      <rect x="14" y="8" width="4" height="4" fill="black" />
      <rect x={frame % 2 === 0 ? "6" : "8"} y="9" width="2" height="2" fill="white" />
      <rect x={frame % 2 === 0 ? "14" : "16"} y="9" width="2" height="2" fill="white" />
    </svg>
  );

  const renderRunner = () => (
    <svg viewBox="0 0 24 24" className="w-16 h-16 text-secondary drop-shadow-[0_0_8px_rgba(var(--secondary),0.8)]">
      {/* 8-bit Runner */}
      {frame % 2 === 0 ? (
        // Frame 1: Stride
        <path fill="currentColor" d="M11 2h2v3h-2zM9 6h6v2H9zM8 8h2v5h-2zM14 8h2v3h-2zM10 13h4v2h-4zM8 15h2v3H8zM14 15h2v2h-2zM6 18h4v2H6zM15 17h3v2h-3z" />
      ) : (
        // Frame 2: Mid-air/Run
        <path fill="currentColor" d="M11 2h2v3h-2zM9 6h6v2H9zM10 9h4v4h-4zM9 13h2v3H9zM13 13h2v2h-2zM7 16h4v2H7zM14 15h3v2h-3z" />
      )}
    </svg>
  );

  const renderTyping = () => (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 24 24" className="w-12 h-12 text-accent drop-shadow-[0_0_8px_rgba(var(--accent),0.8)] mb-1">
        <path fill="currentColor" d="M4 4h16v12H4zM2 18h20v2H2z" />
        <rect x="6" y="6" width="12" height="8" fill="black" />
        {/* Blinking cursor or text */}
        {frame % 4 === 0 && <rect x="7" y="7" width="2" height="2" fill="lime" />}
        {frame % 4 >= 1 && <rect x="10" y="7" width="2" height="2" fill="lime" />}
        {frame % 4 >= 2 && <rect x="13" y="7" width="2" height="2" fill="lime" />}
      </svg>
      <div className="h-1 w-16 bg-accent/20 rounded-full animate-pulse" />
    </div>
  );

  const renderRocket = () => (
    <svg viewBox="0 0 24 24" className={cn("w-16 h-16 text-primary drop-shadow-[0_0_8px_rgba(var(--primary),0.8)]", "animate-bounce")}>
      <path fill="currentColor" d="M11 2h2v2h-2zM10 4h4v2h-4zM9 6h6v4H9zM8 10h8v8H8zM6 14h2v6H6zM16 14h2v6h-2z" />
      {/* Flame */}
      {frame % 2 !== 0 && (
         <path fill="#ef4444" d="M10 19h4v3h-4zM11 22h2v2h-2z" />
      )}
    </svg>
  );

  return (
    <div className="flex items-center justify-center w-full h-full">
      {/* Map currentStep to animation. 0=Analyze, 1=Detect, 2=Filter, 3=Render */}
      {currentStep === 0 && renderTyping()}
      {currentStep === 1 && renderGhost()}
      {currentStep === 2 && renderRunner()}
      {currentStep >= 3 && renderRocket()}
    </div>
  );
};

export default RetroCenterAnimation;
