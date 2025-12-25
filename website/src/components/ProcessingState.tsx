import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Terminal } from "lucide-react";

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
  const [showDetails, setShowDetails] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

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
      <div className="relative w-32 h-32 mx-auto">
        {/* Outer ring */}
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="hsl(var(--secondary))"
            strokeWidth="4"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={`${progress * 2.83} 283`}
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-foreground">{Math.round(progress)}%</span>
        </div>

        {/* Orbiting dots */}
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-primary rounded-full transition-opacity duration-300"
            style={{
              top: "50%",
              left: "50%",
              transform: `rotate(${(progress * 3.6) + (i * 120)}deg) translateX(52px) translateY(-50%)`,
              opacity: progress < 100 ? 0.3 + (i * 0.3) : 0,
            }}
          />
        ))}
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