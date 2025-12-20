import { useState } from "react";
import { Download, RotateCcw, Check, Share2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { getDownloadUrl } from "@/lib/api";
import CustomPlayer from "./CustomPlayer";

interface OutputPreviewProps {
  fileName: string;
  fileType: "audio" | "video";
  filterMode: string;
  onReset: () => void;
  mediaId: number;
}

const OutputPreview = ({ fileName, fileType, filterMode, onReset, mediaId }: OutputPreviewProps) => {
  const [viewMode, setViewMode] = useState<"original" | "filtered">("filtered");

  const toggleViewMode = () => {
    setViewMode((prev) => (prev === "filtered" ? "original" : "filtered"));
  };

  const downloadUrl = viewMode === "filtered"
    ? getDownloadUrl(mediaId, "processed")
    : getDownloadUrl(mediaId, "original");

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
      <CustomPlayer
        key={viewMode} // Re-mount on mode change to reset state
        src={downloadUrl}
        type={fileType}
        className="w-full aspect-video"
      />

      {/* Comparison toggle */}
      <div className="flex items-center justify-center gap-3 p-3 rounded-xl bg-secondary/10 border border-border/30">
        <span className={cn("text-sm transition-colors", viewMode === "original" ? "text-foreground font-medium" : "text-muted-foreground")}>Original</span>

        <button
            onClick={toggleViewMode}
            className="w-12 h-6 rounded-full bg-primary/20 p-1 cursor-pointer relative transition-colors hover:bg-primary/30"
        >
          <div
            className={cn(
                "w-4 h-4 rounded-full bg-primary shadow-[0_0_10px_theme(colors.primary.DEFAULT)] transition-transform duration-300",
                viewMode === "filtered" ? "translate-x-6" : "translate-x-0"
            )}
          />
        </button>

        <span className={cn("text-sm transition-colors", viewMode === "filtered" ? "text-foreground font-medium" : "text-muted-foreground")}>Filtered</span>
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