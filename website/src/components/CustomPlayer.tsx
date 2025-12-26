import { useRef, useState, useEffect } from "react";
import { Play, Pause, Volume2, VolumeX, Maximize2, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import AudioVisualizer from "@/components/ui/AudioVisualizer";
import { Segment } from "@/lib/api";

interface CustomPlayerProps {
    src: string;
    type: "audio" | "video";
    poster?: string;
    className?: string;
    initialTime?: number;
    initialIsPlaying?: boolean;
    onTimeUpdate?: (time: number) => void;
    onPlayStateChange?: (isPlaying: boolean) => void;
    segments?: Segment[];
}

const CustomPlayer = ({
    src,
    type,
    poster,
    className,
    initialTime = 0,
    initialIsPlaying = false,
    onTimeUpdate,
    onPlayStateChange,
    segments = []
}: CustomPlayerProps) => {
    const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement>(null);
    const progressBarRef = useRef<HTMLDivElement>(null);
    const prevSrcRef = useRef<string | null>(null);

    const [isPlaying, setIsPlaying] = useState(initialIsPlaying);
    const [progress, setProgress] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [currentTime, setCurrentTime] = useState(initialTime);
    const [duration, setDuration] = useState(0);
    const [isHovering, setIsHovering] = useState(false);
    const [visualizerMode, setVisualizerMode] = useState<'bars' | 'wave' | 'oscilloscope'>('bars');
    const [isDragging, setIsDragging] = useState(false);

    useEffect(() => {
        const media = mediaRef.current;
        if (!media) return;

        const updateTime = () => {
            if (!isDragging) {
                setCurrentTime(media.currentTime);
                setDuration(media.duration || 0);
                setProgress((media.currentTime / media.duration) * 100);
                if (onTimeUpdate) onTimeUpdate(media.currentTime);
            }
        };

        const handleEnded = () => {
            setIsPlaying(false);
            if (onPlayStateChange) onPlayStateChange(false);
        };

        media.addEventListener("timeupdate", updateTime);
        media.addEventListener("loadedmetadata", updateTime);
        media.addEventListener("ended", handleEnded);

        return () => {
            media.removeEventListener("timeupdate", updateTime);
            media.removeEventListener("loadedmetadata", updateTime);
            media.removeEventListener("ended", handleEnded);
        };
    }, [src, isDragging, onTimeUpdate, onPlayStateChange]);

    // Handle src changes and initialization
    useEffect(() => {
        if (mediaRef.current) {
            // Check if src has changed or if it's the first mount
            const srcChanged = src !== prevSrcRef.current;

            if (srcChanged) {
                // If initialTime is provided and > 0, we set it.
                mediaRef.current.currentTime = initialTime;
                setCurrentTime(initialTime);

                // Recalculate progress if duration is known (might not be yet)
                if (mediaRef.current.duration) {
                    setProgress((initialTime / mediaRef.current.duration) * 100);
                } else {
                    setProgress(0);
                }

                if (initialIsPlaying) {
                    mediaRef.current.play().catch(e => console.error("Auto-play failed:", e));
                    setIsPlaying(true);
                } else {
                    setIsPlaying(false);
                    mediaRef.current.pause();
                }

                prevSrcRef.current = src;
            }
        }
    }, [src, initialTime, initialIsPlaying]);

    const togglePlay = () => {
        if (!mediaRef.current) return;
        const newIsPlaying = !isPlaying;
        if (isPlaying) {
            mediaRef.current.pause();
        } else {
            mediaRef.current.play();
        }
        setIsPlaying(newIsPlaying);
        if (onPlayStateChange) onPlayStateChange(newIsPlaying);
    };

    const toggleVisualizerMode = () => {
        const modes: ('bars' | 'wave' | 'oscilloscope')[] = ['bars', 'wave', 'oscilloscope'];
        const currentIndex = modes.indexOf(visualizerMode);
        setVisualizerMode(modes[(currentIndex + 1) % modes.length]);
    };

    const updateSeek = (clientX: number) => {
        if (!mediaRef.current || !progressBarRef.current) return;
        // Guard against invalid duration
        if (!mediaRef.current.duration || isNaN(mediaRef.current.duration)) return;

        const rect = progressBarRef.current.getBoundingClientRect();
        const pos = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));

        const newTime = pos * mediaRef.current.duration;
        setCurrentTime(newTime);
        setProgress(pos * 100);

        // Real-time scrubbing: update media current time
        if (Math.abs(mediaRef.current.currentTime - newTime) > 0.1) {
            mediaRef.current.currentTime = newTime;
        }
    };

    const handleDragStart = (e: React.MouseEvent<HTMLDivElement>) => {
        e.stopPropagation(); // Stop bubbling to prevent togglePlay
        setIsDragging(true);
        updateSeek(e.clientX);
    };

    useEffect(() => {
        const handleDragMove = (e: MouseEvent) => {
            if (isDragging) {
                updateSeek(e.clientX);
            }
        };

        const handleDragEnd = () => {
            if (isDragging) {
                setIsDragging(false);
            }
        };

        if (isDragging) {
            window.addEventListener('mousemove', handleDragMove);
            window.addEventListener('mouseup', handleDragEnd);
        }

        return () => {
            window.removeEventListener('mousemove', handleDragMove);
            window.removeEventListener('mouseup', handleDragEnd);
        };
    }, [isDragging]);

    const toggleMute = () => {
        if (!mediaRef.current) return;
        const newMuteState = !isMuted;
        mediaRef.current.muted = newMuteState;
        setIsMuted(newMuteState);
    };

    const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!mediaRef.current) return;
        const val = parseFloat(e.target.value);
        mediaRef.current.volume = val;
        setVolume(val);
        setIsMuted(val === 0);
    };

    const formatTime = (seconds: number) => {
        if (isNaN(seconds)) return "0:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, "0")}`;
    };

    const toggleFullscreen = () => {
        if (!mediaRef.current) return;
        const container = mediaRef.current.parentElement;

        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else if (container && container.requestFullscreen) {
            container.requestFullscreen();
        }
    };

    return (
        <div
            className={cn("relative group overflow-hidden rounded-xl bg-black border border-border/50 shadow-[0_0_20px_rgba(0,0,0,0.5)]", className)}
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
        >
            {/* Media Element */}
            {type === "video" ? (
                <video
                    ref={mediaRef as React.RefObject<HTMLVideoElement>}
                    src={src}
                    className="w-full h-full object-contain bg-black"
                    onClick={togglePlay}
                    crossOrigin="anonymous"
                />
            ) : (
                <div
                    className="flex items-center justify-center w-full h-full bg-gradient-to-br from-secondary/10 to-primary/5 relative overflow-hidden cursor-pointer"
                    onClick={togglePlay}
                >
                    {/* Visualizer Background */}
                    <div className="absolute inset-0 z-0 flex items-center justify-center opacity-80 pointer-events-none">
                        <AudioVisualizer
                            mediaRef={mediaRef}
                            mode={visualizerMode}
                            className="w-full h-full object-cover"
                        />
                    </div>

                    <div className="w-full px-8 z-10 relative">
                        <audio ref={mediaRef as React.RefObject<HTMLAudioElement>} src={src} crossOrigin="anonymous" />
                    </div>
                </div>
            )}

            {/* Overlay Controls */}
            <div
                className={cn(
                    "absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent transition-opacity duration-300 flex flex-col gap-2",
                    isHovering || !isPlaying ? "opacity-100" : "opacity-0"
                )}
            >
                {/* Progress Bar */}
                <div
                    ref={progressBarRef}
                    className="relative w-full h-1.5 bg-white/20 rounded-full cursor-pointer hover:h-2.5 transition-all group/progress"
                    onMouseDown={handleDragStart}
                >
                    {/* Buffered/Loaded - skipped for simplicity */}

                    {/* Played */}
                    <div
                        className="absolute top-0 left-0 h-full bg-primary rounded-full relative z-20"
                        style={{ width: `${progress}%` }}
                    >
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_10px_theme(colors.primary.DEFAULT)] opacity-0 group-hover/progress:opacity-100 transition-opacity" />
                    </div>

                    {/* Filtered Segments */}
                    {segments.map((segment, idx) => {
                        // In audio mode, ignore non-mute segments
                        if (type === 'audio' && segment.action_type !== 'mute') return null;

                        const startPercent = (segment.start_ms / 1000 / (duration || 1)) * 100;
                        const widthPercent = ((segment.end_ms - segment.start_ms) / 1000 / (duration || 1)) * 100;

                        // Neon Blue (#00FFFF) for mute, Neon Orange (#FF5F1F) for blur
                        const color = segment.action_type === 'mute' ? '#00FFFF' : '#FF5F1F';

                        return (
                            <div
                                key={`${segment.id}-${idx}`}
                                className="absolute top-0 h-full z-10 opacity-70 pointer-events-none"
                                style={{
                                    left: `${startPercent}%`,
                                    width: `${widthPercent}%`,
                                    backgroundColor: color,
                                    boxShadow: `0 0 5px ${color}`
                                }}
                                title={`${segment.action_type}: ${formatTime(segment.start_ms/1000)} - ${formatTime(segment.end_ms/1000)}`}
                            />
                        );
                    })}
                </div>

                {/* Buttons & Info */}
                <div className="flex items-center justify-between mt-1">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={togglePlay}
                            className="text-white hover:text-primary transition-colors focus:outline-none"
                        >
                            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 fill-current" />}
                        </button>

                        <div className="flex items-center gap-2 group/volume">
                            <button onClick={toggleMute} className="text-white/80 hover:text-white">
                                {isMuted || volume === 0 ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                            </button>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.05"
                                value={isMuted ? 0 : volume}
                                onChange={handleVolumeChange}
                                style={{
                                    background: `linear-gradient(to right, #6366f1, #a855f7, #ec4899) 0/${isMuted ? 0 : volume * 100}% 100% no-repeat, rgba(255, 255, 255, 0.1)`
                                }}
                                className="w-0 overflow-hidden group-hover/volume:w-20 h-3 rounded-lg appearance-none cursor-pointer shadow-[0_0_10px_theme(colors.primary.DEFAULT)] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-[0_0_5px_rgba(255,255,255,0.8)]"
                            />
                        </div>

                        <div className="text-xs font-mono text-white/80">
                            <span className="text-white">{formatTime(currentTime)}</span>
                            <span className="mx-1">/</span>
                            <span>{formatTime(duration)}</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {type === "audio" && (
                            <button
                                onClick={toggleVisualizerMode}
                                className="text-white/80 hover:text-white transition-colors"
                                title={`Visualizer Mode: ${visualizerMode}`}
                            >
                                <Activity className="w-4 h-4" />
                            </button>
                        )}

                        {type === "video" && (
                            <button
                                onClick={toggleFullscreen}
                                className="text-white/80 hover:text-white transition-colors"
                            >
                                <Maximize2 className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Big Play Button Overlay (when paused) */}
            {!isPlaying && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-16 h-16 rounded-full bg-black/50 backdrop-blur-sm border border-white/10 flex items-center justify-center shadow-[0_0_30px_theme(colors.primary.DEFAULT)]">
                        <Play className="w-8 h-8 text-primary ml-1 fill-current" />
                    </div>
                </div>
            )}
        </div>
    );
};

export default CustomPlayer;
