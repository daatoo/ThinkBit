import { useState, useEffect } from "react";
import { Clock, RefreshCw, File } from "lucide-react";
import { listRawFiles, RawFileResponse } from "@/lib/api";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

const RawOutputsSection = () => {
    const [files, setFiles] = useState<RawFileResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchFiles = async () => {
        try {
            const data = await listRawFiles();
            // Sort by newest first
            const sorted = data.sort((a, b) =>
                new Date(b.modified_at).getTime() - new Date(a.modified_at).getTime()
            );
            setFiles(sorted);
        } catch (error) {
            console.error("Failed to fetch raw files:", error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchFiles();
        // Poll for updates every 10 seconds
        const interval = setInterval(fetchFiles, 10000);
        return () => clearInterval(interval);
    }, []);

    const handleRefresh = () => {
        setRefreshing(true);
        fetchFiles();
    };

    if (!loading && files.length === 0) {
        return null;
    }

    return (
        <section id="raw-outputs" className="py-12 px-8 relative overflow-hidden bg-black/20">
            <div className="max-w-6xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h3 className="text-xl font-bold mb-1 text-muted-foreground">
                            Raw Output Files
                        </h3>
                        <p className="text-sm text-muted-foreground/60">
                            Files physically present in the output folder.
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
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {files.map((file) => (
                        <div
                            key={file.filename}
                            className="bg-card/50 border border-border/50 rounded-lg p-4 flex flex-col hover:border-primary/20 transition-all duration-200"
                        >
                            <div className="flex items-start gap-3">
                                <div className="p-2 rounded-md bg-secondary text-muted-foreground">
                                    <File className="w-5 h-5" />
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className="font-medium text-sm truncate" title={file.filename}>
                                        {file.filename}
                                    </p>
                                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
                                        <Clock className="w-3 h-3" />
                                        <span>{format(new Date(file.modified_at), "MMM d, yyyy • HH:mm")}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default RawOutputsSection;
