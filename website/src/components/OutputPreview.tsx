import { useState } from "react";
import { Download, Play, Pause, Volume2, VolumeX, RotateCcw, Check, Share2, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

interface OutputPreviewProps {
  fileName: string;
  fileType: "audio" | "video";
  filterMode: string;
  onReset: () => void;
}

const OutputPreview = ({ fileName, fileType, filterMode, onReset }: OutputPreviewProps) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration] = useState(180); // Mock duration

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const progress = (currentTime / duration) * 100;

  return (
    <div className="space-y-6">
      {/* Success header */}
      <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
        <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
          <Check className="w-5 h-5 text-emerald-400" />
        </div>
        <div>
          <p className="font-semibold text-foreground">Processing Complete</p>
          <p className="text-sm text-muted-foreground">Your filtered content is ready</p>
        </div>
      </div>

      {/* Preview player */}
      <div className="relative rounded-2xl overflow-hidden bg-secondary/50 border border-border/50">
        {fileType === "video" ? (
          <div className="aspect-video bg-gradient-to-br from-secondary to-background flex items-center justify-center relative group">
            {/* Video placeholder with waveform visualization */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex items-end gap-1 h-16">
                {Array.from({ length: 32 }).map((_, i) => (
                  <div
                    key={i}
                    className={cn(
                      "w-1 bg-primary/40 rounded-full transition-all duration-150",
                      isPlaying && "animate-pulse"
                    )}
                    style={{
                      height: `${Math.sin(i * 0.5) * 30 + 40}%`,
                      animationDelay: `${i * 50}ms`,
                    }}
                  />
                ))}
              </div>
            </div>
            
            {/* Play overlay */}
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="relative z-10 w-20 h-20 rounded-full bg-primary/20 backdrop-blur-sm border border-primary/30 flex items-center justify-center group-hover:bg-primary/30 transition-all"
            >
              {isPlaying ? (
                <Pause className="w-8 h-8 text-primary" />
              ) : (
                <Play className="w-8 h-8 text-primary ml-1" />
              )}
            </button>

            {/* Fullscreen button */}
            <button className="absolute top-4 right-4 w-10 h-10 rounded-lg bg-background/50 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Maximize2 className="w-4 h-4 text-foreground" />
            </button>
          </div>
        ) : (
          <div className="p-8 flex flex-col items-center justify-center min-h-[200px]">
            {/* Audio waveform */}
            <div className="flex items-end gap-0.5 h-24 mb-6">
              {Array.from({ length: 64 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-1 bg-gradient-to-t from-primary/60 to-primary rounded-full transition-all duration-75",
                    isPlaying && "animate-pulse"
                  )}
                  style={{
                    height: `${Math.abs(Math.sin(i * 0.3) * Math.cos(i * 0.1)) * 80 + 20}%`,
                    animationDelay: `${i * 30}ms`,
                  }}
                />
              ))}
            </div>
            
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="w-16 h-16 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center hover:bg-primary/30 transition-all"
            >
              {isPlaying ? (
                <Pause className="w-6 h-6 text-primary" />
              ) : (
                <Play className="w-6 h-6 text-primary ml-0.5" />
              )}
            </button>
          </div>
        )}

        {/* Progress bar and controls */}
        <div className="p-4 border-t border-border/50">
          <div className="flex items-center gap-4 mb-3">
            <span className="text-xs font-mono text-muted-foreground w-12">{formatTime(currentTime)}</span>
            <div className="flex-1 relative">
              <Progress value={progress} className="h-1.5 bg-secondary" />
              <input
                type="range"
                min={0}
                max={duration}
                value={currentTime}
                onChange={(e) => setCurrentTime(Number(e.target.value))}
                className="absolute inset-0 w-full opacity-0 cursor-pointer"
              />
            </div>
            <span className="text-xs font-mono text-muted-foreground w-12 text-right">{formatTime(duration)}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsMuted(!isMuted)}
                className="w-9 h-9 rounded-lg hover:bg-secondary flex items-center justify-center transition-colors"
              >
                {isMuted ? (
                  <VolumeX className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <Volume2 className="w-4 h-4 text-foreground" />
                )}
              </button>
            </div>
            
            <div className="text-center">
              <p className="text-sm font-medium text-foreground truncate max-w-[200px]">{fileName}</p>
              <p className="text-xs text-muted-foreground">{filterMode}</p>
            </div>

            <div className="w-9" /> {/* Spacer for balance */}
          </div>
        </div>
      </div>

      {/* Comparison toggle */}
      <div className="flex items-center justify-center gap-2 p-3 rounded-xl bg-secondary/30 border border-border/30">
        <span className="text-sm text-muted-foreground">Original</span>
        <div className="w-12 h-6 rounded-full bg-primary/20 p-1 cursor-pointer">
          <div className="w-4 h-4 rounded-full bg-primary translate-x-6 transition-transform" />
        </div>
        <span className="text-sm text-foreground font-medium">Filtered</span>
      </div>

      {/* Action buttons */}
      <div className="grid grid-cols-3 gap-3">
        <button
          onClick={onReset}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-border/50 text-muted-foreground hover:text-foreground hover:border-border transition-all"
        >
          <RotateCcw className="w-4 h-4" />
          <span className="text-sm">New File</span>
        </button>
        <button className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-border/50 text-muted-foreground hover:text-foreground hover:border-border transition-all">
          <Share2 className="w-4 h-4" />
          <span className="text-sm">Share</span>
        </button>
        <button className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl gradient-button">
          <Download className="w-4 h-4" />
          <span className="text-sm">Download</span>
        </button>
      </div>

      {/* Processing stats */}
      <div className="grid grid-cols-3 gap-4 p-4 rounded-xl bg-secondary/20 border border-border/30">
        <div className="text-center">
          <p className="text-2xl font-bold text-primary">12</p>
          <p className="text-xs text-muted-foreground">Items Filtered</p>
        </div>
        <div className="text-center border-x border-border/30">
          <p className="text-2xl font-bold text-foreground">3.2s</p>
          <p className="text-xs text-muted-foreground">Process Time</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-emerald-400">99.7%</p>
          <p className="text-xs text-muted-foreground">Accuracy</p>
        </div>
      </div>
    </div>
  );
};

export default OutputPreview;