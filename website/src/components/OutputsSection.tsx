import { useState, useEffect } from "react";
import { Download, Trash2, FileVideo, Clock, RefreshCw } from "lucide-react";
import { listMedia, deleteMedia, downloadMedia, MediaResponse } from "@/lib/api";
import { format } from "date-fns";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";
import { SignInModal } from "./AuthModals";

const OutputsSection = () => {
    const [outputs, setOutputs] = useState<MediaResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const { isAuthenticated, loading: authLoading } = useAuth();

    const fetchOutputs = async () => {
        if (!isAuthenticated) {
            setLoading(false);
            return;
        }
        
        try {
            const data = await listMedia("DONE");
            // Sort by newest first
            const sorted = data.sort((a, b) =>
                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            );
            setOutputs(sorted);
        } catch (error) {
            console.error("Failed to fetch outputs:", error);
            // Don't show toast on initial load to avoid annoyance if empty
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        if (!authLoading) {
            fetchOutputs();
            // Poll for updates every 10 seconds
            const interval = setInterval(fetchOutputs, 10000);
            return () => clearInterval(interval);
        }
    }, [isAuthenticated, authLoading]);

    const handleRefresh = () => {
        setRefreshing(true);
        fetchOutputs();
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteMedia(id);
            setOutputs(prev => prev.filter(item => item.id !== id));
            toast.success("File deleted successfully");
        } catch (error) {
            console.error("Failed to delete:", error);
            toast.error(error instanceof Error ? error.message : "Failed to delete file");
        }
    };

    const handleDownload = async (item: MediaResponse) => {
        try {
            const filename = item.output_path?.split(/[/\\]/).pop() || `video_${item.id}.mp4`;
            await downloadMedia(item.id, "processed", filename);
            toast.success("Download started");
        } catch (error) {
            console.error("Failed to download:", error);
            toast.error(error instanceof Error ? error.message : "Failed to download file");
        }
    };

    if (authLoading || (loading && outputs.length === 0)) {
        return null;
    }

    if (!isAuthenticated) {
        return (
            <section id="outputs" className="py-20 px-8 relative overflow-hidden">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center py-12">
                        <h2 className="text-3xl font-bold mb-4">
                            <span className="gradient-text">Processed Outputs</span>
                        </h2>
                        <p className="text-muted-foreground mb-6">
                            Please sign in to view your processed files.
                        </p>
                        <SignInModal>
                            <button className="gradient-button px-6 py-3">
                                Sign In
                            </button>
                        </SignInModal>
                    </div>
                </div>
            </section>
        );
    }

    if (!loading && outputs.length === 0) {
        return null; // Return null if perfectly empty so we don't take up space? Or maybe show a placeholder.
        // Let's show nothing if empty to keep it clean, as per "hidden" class in original file.
    }

    return (
        <section id="outputs" className="py-20 px-8 relative overflow-hidden">
            {/* Background accents */}
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px] -z-10 translate-x-1/2 -translate-y-1/2" />

            <div className="max-w-6xl mx-auto">
                <div className="flex items-center justify-between mb-12">
                    <div>
                        <h2 className="text-3xl font-bold mb-2">
                            <span className="gradient-text">Processed Outputs</span>
                        </h2>
                        <p className="text-muted-foreground">
                            Download your filtered videos securely.
                        </p>
                    </div>

                    <button
                        onClick={handleRefresh}
                        className={cn(
                            "p-2 rounded-full hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground",
                            refreshing && "animate-spin"
                        )}
                        title="Refresh list"
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {outputs.map((item) => (
                        <div
                            key={item.id}
                            className="glass-card p-6 flex flex-col group hover:border-primary/30 transition-all duration-300"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-300">
                                    <FileVideo className="w-6 h-6" />
                                </div>
                                <div className="flex gap-2">
                                    <span className="text-xs font-mono py-1 px-2 rounded-lg bg-secondary text-muted-foreground">
                                        {((item.segments?.length || 0) > 0 ? 'FILTERED' : 'CLEAN')}
                                    </span>
                                </div>
                            </div>

                            <h3 className="font-semibold text-lg mb-1 truncate" title={item.input_path}>
                                {item.input_path.split(/[/\\]/).pop()}
                            </h3>

                            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
                                <Clock className="w-3.5 h-3.5" />
                                <span>{format(new Date(item.created_at), "MMM d, yyyy • HH:mm")}</span>
                            </div>

                            <div className="mt-auto flex gap-3 pt-4 border-t border-border/50">
                                <button
                                    onClick={() => handleDownload(item)}
                                    className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary font-medium transition-colors text-sm"
                                >
                                    <Download className="w-4 h-4" />
                                    Download
                                </button>

                                <button
                                    onClick={() => handleDelete(item.id)}
                                    className="p-2.5 rounded-xl hover:bg-destructive/10 hover:text-destructive text-muted-foreground transition-colors"
                                    title="Delete file"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default OutputsSection;
