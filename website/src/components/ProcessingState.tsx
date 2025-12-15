import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ProcessingStateProps {
  fileName: string;
  onComplete: () => void;
}

const processingSteps = [
  { label: "Analyzing content structure", duration: 800 },
  { label: "Detecting audio patterns", duration: 1200 },
  { label: "Identifying flagged content", duration: 1000 },
  { label: "Applying neural filters", duration: 1500 },
  { label: "Rendering output", duration: 800 },
];

const ProcessingState = ({ fileName, onComplete }: ProcessingStateProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let stepProgress = 0;
    const totalDuration = processingSteps.reduce((sum, step) => sum + step.duration, 0);
    let elapsed = 0;

    const interval = setInterval(() => {
      elapsed += 50;
      const newProgress = (elapsed / totalDuration) * 100;
      setProgress(Math.min(newProgress, 100));

      // Calculate current step
      let accumulatedTime = 0;
      for (let i = 0; i < processingSteps.length; i++) {
        accumulatedTime += processingSteps[i].duration;
        if (elapsed < accumulatedTime) {
          setCurrentStep(i);
          break;
        }
      }

      if (elapsed >= totalDuration) {
        // Reset to loop the animation while waiting for actual completion
        elapsed = 0;
        stepProgress = 0;
        // Keep the last step or loop? Let's loop visually but keep text static or cycle
        // For now, let's just let it loop the progress bar but keep the text "Processing..."
      }
    }, 50);

    return () => clearInterval(interval);
  }, []);

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
            className="transition-all duration-100"
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
            className="absolute w-2 h-2 bg-primary rounded-full"
            style={{
              top: "50%",
              left: "50%",
              transform: `rotate(${(progress * 3.6) + (i * 120)}deg) translateX(52px) translateY(-50%)`,
              opacity: 0.3 + (i * 0.3),
            }}
          />
        ))}
      </div>

      {/* File info */}
      <div className="text-center">
        <p className="text-sm text-muted-foreground mb-1">Processing</p>
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
    </div>
  );
};

export default ProcessingState;