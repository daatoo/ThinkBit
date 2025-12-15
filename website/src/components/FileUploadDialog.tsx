import { useState, useRef, useCallback } from "react";
import { Upload, X, FileAudio, FileVideo, Zap, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import ProcessingState from "./ProcessingState";
import OutputPreview from "./OutputPreview";
import { uploadFile, MediaResponse } from "@/lib/api";
import { toast } from "sonner";

interface FileUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  filterMode: {
    label: string;
    description: string;
    type: "audio" | "video" | "stream";
  } | null;
}

type DialogState = "upload" | "processing" | "preview";

const FileUploadDialog = ({ open, onOpenChange, filterMode }: FileUploadDialogProps) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dialogState, setDialogState] = useState<DialogState>("upload");
  const [streamUrl, setStreamUrl] = useState("");
  const [outputUrl, setOutputUrl] = useState("");
  const [processedMedia, setProcessedMedia] = useState<MediaResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isStream = filterMode?.type === "stream";
  const isAudio = filterMode?.type === "audio";
  const acceptTypes = isAudio ? "audio/*" : "video/*";

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  }, []);

  const handleClose = useCallback(() => {
    setSelectedFile(null);
    setDialogState("upload");
    setStreamUrl("");
    setOutputUrl("");
    onOpenChange(false);
  }, [onOpenChange]);

  const handleProcess = useCallback(async () => {
    if (isStream) {
       // Stream logic placeholder
       toast.error("Streaming not implemented yet");
       return;
    }
    if (!selectedFile) return;

    setDialogState("processing");

    // Determine filter flags based on filterMode.label or description
    // Default logic:
    // Audio type: filterAudio=true, filterVideo=false
    // Video type:
    //   "Clean Audio Only": filterAudio=true, filterVideo=false
    //   "Clean Video Only": filterAudio=false, filterVideo=true
    //   "Full Filter" (or anything else): filterAudio=true, filterVideo=true

    let filterAudio = true;
    let filterVideo = false;

    if (filterMode?.type === "video") {
        if (filterMode.label.includes("Clean Audio Only")) {
            filterAudio = true;
            filterVideo = false;
        } else if (filterMode.label.includes("Clean Video Only")) {
            filterAudio = false;
            filterVideo = true;
        } else {
            // Full Filter or default
            filterAudio = true;
            filterVideo = true;
        }
    } else if (filterMode?.type === "audio") {
        filterAudio = true;
        filterVideo = false;
    }

    try {
      const result = await uploadFile(selectedFile, filterAudio, filterVideo);
      setProcessedMedia(result);
      setDialogState("preview");
      toast.success("Processing complete!");
    } catch (error) {
      console.error(error);
      setDialogState("upload");
      toast.error("Processing failed. Please try again.");
    }
  }, [selectedFile, isStream]);

  // Removed handleProcessingComplete as it's no longer used by ProcessingState
  // ProcessingState is now just a visual indicator controlled by dialogState

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setProcessedMedia(null);
    setDialogState("upload");
  }, []);

  const getDialogSize = () => {
    if (dialogState === "preview") return "sm:max-w-2xl";
    return "sm:max-w-lg";
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className={cn("bg-card border-primary/20 overflow-hidden transition-all duration-300", getDialogSize())}>
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 pointer-events-none" />
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
        
        {dialogState === "upload" && (
          <>
            <DialogHeader className="relative">
              <DialogTitle className="text-xl font-bold text-foreground flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/10 flex items-center justify-center border border-primary/10">
                  {isStream ? (
                    <Zap className="w-5 h-5 text-primary" />
                  ) : isAudio ? (
                    <FileAudio className="w-5 h-5 text-primary" />
                  ) : (
                    <FileVideo className="w-5 h-5 text-primary" />
                  )}
                </div>
                <div>
                  <span>{isStream ? "Connect Stream" : "Upload Content"}</span>
                  {filterMode && (
                    <p className="text-sm font-normal text-muted-foreground mt-0.5">
                      {filterMode.label}
                    </p>
                  )}
                </div>
              </DialogTitle>
            </DialogHeader>

            <div className="relative mt-6">
              {isStream ? (
                <div className="space-y-5">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Input Stream URL</label>
                    <input
                      type="url"
                      value={streamUrl}
                      onChange={(e) => setStreamUrl(e.target.value)}
                      placeholder="rtmp://your-stream-url.com/live"
                      className="w-full px-4 py-3.5 rounded-xl bg-secondary/50 border border-border/50 text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Output Destination</label>
                    <input
                      type="url"
                      value={outputUrl}
                      onChange={(e) => setOutputUrl(e.target.value)}
                      placeholder="rtmp://output-destination.com/filtered"
                      className="w-full px-4 py-3.5 rounded-xl bg-secondary/50 border border-border/50 text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm"
                    />
                  </div>
                  <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-amber-200/80">
                      Ensure your stream supports RTMP or HLS protocols. Latency varies based on network conditions.
                    </p>
                  </div>
                </div>
              ) : (
                <div
                  className={cn(
                    "relative border-2 border-dashed rounded-2xl p-10 transition-all duration-300 cursor-pointer group",
                    dragActive
                      ? "border-primary bg-primary/10 scale-[1.02]"
                      : "border-border/50 hover:border-primary/50 hover:bg-secondary/30",
                    selectedFile && "border-primary/50 bg-primary/5"
                  )}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => inputRef.current?.click()}
                >
                  <input
                    ref={inputRef}
                    type="file"
                    accept={acceptTypes}
                    onChange={handleChange}
                    className="hidden"
                  />

                  <div className="flex flex-col items-center gap-5">
                    <div className={cn(
                      "w-20 h-20 rounded-2xl flex items-center justify-center transition-all duration-300",
                      selectedFile
                        ? "bg-gradient-to-br from-primary/20 to-accent/10"
                        : "bg-secondary/50 group-hover:bg-primary/10"
                    )}>
                      {selectedFile ? (
                        isAudio ? (
                          <FileAudio className="w-10 h-10 text-primary" />
                        ) : (
                          <FileVideo className="w-10 h-10 text-primary" />
                        )
                      ) : (
                        <Upload className={cn(
                          "w-10 h-10 transition-colors",
                          dragActive ? "text-primary" : "text-muted-foreground group-hover:text-primary"
                        )} />
                      )}
                    </div>

                    {selectedFile ? (
                      <div className="text-center">
                        <p className="font-semibold text-foreground text-lg">{selectedFile.name}</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedFile(null);
                          }}
                          className="mt-3 text-sm text-destructive hover:text-destructive/80 flex items-center gap-1.5 mx-auto px-3 py-1.5 rounded-lg hover:bg-destructive/10 transition-colors"
                        >
                          <X className="w-4 h-4" /> Remove file
                        </button>
                      </div>
                    ) : (
                      <div className="text-center">
                        <p className="font-semibold text-foreground text-lg">
                          {dragActive ? "Drop your file here" : "Drag & drop to upload"}
                        </p>
                        <p className="text-sm text-muted-foreground mt-2">
                          or <span className="text-primary">browse files</span>
                        </p>
                        <p className="text-xs text-muted-foreground/60 mt-3">
                          {isAudio ? "MP3, WAV, AAC • Max 500MB" : "MP4, MOV, AVI • Max 2GB"}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-3.5 rounded-xl border border-border/50 text-muted-foreground hover:text-foreground hover:border-border hover:bg-secondary/30 transition-all font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleProcess}
                  disabled={!isStream && !selectedFile}
                  className={cn(
                    "flex-1 px-4 py-3.5 rounded-xl font-semibold transition-all duration-300",
                    (!isStream && !selectedFile)
                      ? "bg-secondary text-muted-foreground cursor-not-allowed"
                      : "gradient-button"
                  )}
                >
                  {isStream ? "Connect & Filter" : "Start Processing"}
                </button>
              </div>
            </div>
          </>
        )}

        {dialogState === "processing" && (
          <ProcessingState
            fileName={selectedFile?.name || "Stream"}
            onComplete={() => {}} // No-op, controlled by async/await
          />
        )}

        {dialogState === "preview" && selectedFile && processedMedia && (
          <OutputPreview
            fileName={selectedFile.name}
            fileType={isAudio ? "audio" : "video"}
            filterMode={filterMode?.label || ""}
            onReset={handleReset}
            mediaId={processedMedia.id}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};

export default FileUploadDialog;