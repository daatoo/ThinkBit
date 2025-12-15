import { useState } from "react";
import { Download, Play, Pause, Volume2, VolumeX, RotateCcw, Check, Share2, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { getDownloadUrl } from "@/lib/api";

interface OutputPreviewProps {
  fileName: string;
  fileType: "audio" | "video";
  filterMode: string;
  onReset: () => void;
  mediaId: number;
}

const OutputPreview = ({ fileName, fileType, filterMode, onReset, mediaId }: OutputPreviewProps) => {
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
            {/* Use actual video element if mediaId is present, else placeholder */}
            <video
                src={getDownloadUrl(mediaId)}
                className="w-full h-full object-contain"
                controls
            >
                Your browser does not support the video tag.
            </video>

            {/* Fullscreen button */}
            <button className="absolute top-4 right-4 w-10 h-10 rounded-lg bg-background/50 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Maximize2 className="w-4 h-4 text-foreground" />
            </button>
          </div>
        ) : (
          <div className="p-8 flex flex-col items-center justify-center min-h-[200px]">
             <audio
                src={getDownloadUrl(mediaId)}
                controls
                className="w-full"
            >
                Your browser does not support the audio tag.
            </audio>
          </div>
        )}

        {/* Custom controls removed in favor of native controls for simplicity and robustness with actual media */}
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
        <a href={getDownloadUrl(mediaId)} download className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl gradient-button">
          <Download className="w-4 h-4" />
          <span className="text-sm">Download</span>
        </a>
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