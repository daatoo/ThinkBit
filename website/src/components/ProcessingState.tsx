import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Terminal } from "lucide-react";
import RetroCenterAnimation from "./RetroCenterAnimation";

interface ProcessingStateProps {
  fileName: string;
  progress: number;
  currentActivity: string;
  logs?: string[];
}

const processingSteps = [
  { label: "Analyzing content structure", matcher: /Analyz/i },
  { label: "Detecting patterns", matcher: /Detect|Identify/i },
  { label: "Applying filters", matcher: /Filter|Censor/i },
  { label: "Rendering output", matcher: /Render|Output|Complet/i },
];

const ProcessingState = ({ fileName, progress, currentActivity, logs = [] }: ProcessingStateProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [visualProgress, setVisualProgress] = useState(0);
  const [showDetails, setShowDetails] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Smooth progress interpolation with "creep" logic
  useEffect(() => {
    let animationFrameId: number;
    let lastTime = performance.now();

    const animate = (currentTime: number) => {
      const deltaTime = currentTime - lastTime;
      lastTime = currentTime;

      setVisualProgress((prev) => {
        // If we are behind the real progress, catch up smoothly
        if (prev < progress) {
          const diff = progress - prev;
          // Catch up speed depends on distance.
          // If far behind, move faster. If close, ease in.
          // Minimum speed ensuring we don't get stuck infinitely close.
          const step = Math.max(diff * 0.1, 0.05);
          return Math.min(prev + step, progress);
        }
        // If we have reached the target, "creep" forward slowly to fake activity
        // But clamp it so we don't go too far ahead of reality (max +10%)
        // and never hit 100% until reality does.
        else if (prev >= progress && progress < 100) {
          const creepLimit = Math.min(progress + 10, 99);
          if (prev < creepLimit) {
            // Very slow creep
            return prev + (0.005 * (deltaTime / 16));
          }
        }
        return prev;
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrameId);
  }, [progress]);

  useEffect(() => {
    // Attempt to map the backend activity string to one of our visual steps
    const stepIndex = processingSteps.findIndex((step) => step.matcher.test(currentActivity));
    if (stepIndex !== -1) {
      setCurrentStep(stepIndex);
    } else {
      // Fallback logic based on progress if activity name doesn't match
      if (progress > 90) setCurrentStep(3);
      else if (progress > 50) setCurrentStep(2);
      else if (progress > 20) setCurrentStep(1);
      else setCurrentStep(0);
    }
  }, [currentActivity, progress]);

  // Auto-scroll logs
  useEffect(() => {
    if (showDetails && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, showDetails]);

  return (
    <div className="space-y-8 py-4">
      {/* Animated processor visual */}
      <div className="relative w-48 h-48 mx-auto">
        {/* Outer ring - Neon Track */}
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          {/* Base track */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="hsl(var(--secondary)/0.2)"
            strokeWidth="8"
          />
          {/* Track border inner */}
          <circle
            cx="50"
            cy="50"
            r="41"
            fill="none"
            stroke="hsl(var(--primary)/0.3)"
            strokeWidth="0.5"
            strokeDasharray="2 2"
          />
           {/* Track border outer */}
           <circle
            cx="50"
            cy="50"
            r="49"
            fill="none"
            stroke="hsl(var(--primary)/0.3)"
            strokeWidth="0.5"
            strokeDasharray="2 2"
          />

          {/* Progress fill (Road lit up) */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={`${visualProgress * 2.83} 283`}
            className="drop-shadow-[0_0_8px_rgba(var(--primary),0.8)]"
          />
        </svg>

        {/* Car on Track */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
             transform: `rotate(${visualProgress * 3.6}deg)`
          }}
        >
          {/* The car element itself, positioned at the top (start of rotation) and offset to the radius */}
          <div
             className="absolute w-8 h-8 -top-4 left-1/2 -ml-4 transition-transform"
             // No extra rotation needed if car points "up" by default.
             // But usually car drives forward.
             // Rotate 90deg to face direction of travel (clockwise)
             style={{ transform: 'rotate(90deg)' }}
          >
             <svg viewBox="0 0 24 24" className="w-full h-full text-white drop-shadow-[0_0_10px_rgba(255,255,255,1)]">
                {/* Simple 8-bit Car */}
                <path fill="currentColor" d="M3 12h2v-2h2v-2h10v2h2v2h2v6h-2v2h-2v-2h-10v2h-2v-2h-2v-6zm4 0h2v2h-2v-2zm10 0h2v2h-2v-2z" />
             </svg>
          </div>
        </div>

        {/* Center content - Retro Animation */}
        <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
          <RetroCenterAnimation currentStep={currentStep} />
          <div className="mt-2 px-2 py-1 bg-black/80 rounded border border-primary/50">
            <span className="text-xl font-bold text-primary font-mono">{Math.round(visualProgress)}%</span>
          </div>
        </div>
      </div>

      {/* File info */}
      <div className="text-center">
        <p className="text-sm text-muted-foreground mb-1">
          {currentActivity || "Processing..."}
        </p>
        <p className="font-medium text-foreground truncate max-w-[280px] mx-auto">{fileName}</p>
      </div>

      {/* Step indicators */}
      <div className="space-y-3">
        {processingSteps.map((step, index) => (
          <div
            key={step.label}
            className={cn(
              "flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-300",
              index < currentStep && "opacity-50",
              index === currentStep && "bg-primary/10",
              index > currentStep && "opacity-30"
            )}
          >
            <div
              className={cn(
                "w-2 h-2 rounded-full transition-all",
                index < currentStep && "bg-primary",
                index === currentStep && "bg-primary animate-pulse",
                index > currentStep && "bg-muted-foreground/30"
              )}
            />
            <span
              className={cn(
                "text-sm transition-colors",
                index === currentStep ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {step.label}
            </span>
            {index < currentStep && (
              <span className="ml-auto text-xs text-primary">✓</span>
            )}
          </div>
        ))}
      </div>

      {/* Details Toggle */}
      <div className="pt-2">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center gap-2 mx-auto text-xs font-medium text-muted-foreground hover:text-primary transition-colors"
        >
          {showDetails ? (
            <>
              <ChevronUp className="w-3 h-3" /> Hide Details
            </>
          ) : (
            <>
              <ChevronDown className="w-3 h-3" /> Show Details
            </>
          )}
        </button>

        {/* Logs View */}
        <div
          className={cn(
            "grid transition-all duration-300 ease-in-out overflow-hidden mt-4",
            showDetails ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
          )}
        >
          <div className="min-h-0 bg-black/80 rounded-lg border border-primary/20 p-4 font-mono text-xs text-primary/80 shadow-inner">
            <div className="flex items-center gap-2 mb-2 border-b border-primary/10 pb-2">
              <Terminal className="w-3 h-3" />
              <span className="font-semibold uppercase tracking-wider">Process Log</span>
            </div>
            <div className="max-h-[200px] overflow-y-auto space-y-1 custom-scrollbar">
              {logs.length === 0 && (
                <div className="text-muted-foreground italic">Waiting for logs...</div>
              )}
              {logs.map((log, i) => (
                <div key={i} className="break-words">
                  <span className="opacity-50 mr-2">{log.split(']')[0] + ']'}</span>
                  <span>{log.split(']').slice(1).join(']')}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessingState;