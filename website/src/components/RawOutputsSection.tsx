import { useState, useEffect } from "react";
import { Clock, RefreshCw, File, Trash2 } from "lucide-react";
import { listRawFiles, RawFileResponse, getRawFileUrl, deleteRawFile } from "@/lib/api";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import CustomPlayer from "@/components/CustomPlayer";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const RawOutputsSection = () => {
    const [files, setFiles] = useState<RawFileResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [fileToDelete, setFileToDelete] = useState<string | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);
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

    const handleFileClick = (filename: string) => {
        setSelectedFile(filename);
    };

    const getFileType = (filename: string): "audio" | "video" => {
        const ext = filename.split('.').pop()?.toLowerCase();
        if (['wav', 'mp3', 'flac', 'm4a'].includes(ext || '')) {
            return 'audio';
        }
        return 'video';
    };

    if (!loading && files.length === 0) {
        return null;
    }

    const handleDeleteClick = (e: React.MouseEvent, filename: string) => {
        e.stopPropagation();
        setFileToDelete(filename);
    };

    const handleConfirmDelete = async () => {
        if (!fileToDelete) return;

        setIsDeleting(true);
        try {
            await deleteRawFile(fileToDelete);
            await fetchFiles();
        } catch (error) {
            console.error("Failed to delete file:", error);
            // Optionally add toast notification here
        } finally {
            setIsDeleting(false);
            setFileToDelete(null);
        }
    };
    return (
        <section id="raw-outputs" className="py-12 px-8 relative overflow-hidden bg-black/20">
            <div className="max-w-6xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h3 className="text-xl font-bold mb-1 text-muted-foreground">
                            Raw Output Files
                        </h3>
                        <p className="text-sm text-muted-foreground/60">
                            Files physically present in the output folder. Click to play.
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
                            onClick={() => handleFileClick(file.filename)}
                            className="bg-card/50 border border-border/50 rounded-lg p-4 flex flex-col hover:border-primary/20 transition-all duration-200 cursor-pointer hover:bg-card/80 group relative"                        >
                            <div className="flex items-start gap-3">
                                <div className="p-2 rounded-md bg-secondary text-muted-foreground group-hover:text-primary transition-colors">
                                    <File className="w-5 h-5" />
                                </div>
                                <div className="min-w-0 flex-1 pr-8">
                                    <p className="font-medium text-sm truncate" title={file.filename}>
                                        {file.filename}
                                    </p>
                                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
                                        <Clock className="w-3 h-3" />
                                        <span>{format(new Date(file.modified_at), "MMM d, yyyy • HH:mm")}</span>
                                    </div>
                                </div>
                                <button
                                    onClick={(e) => handleDeleteClick(e, file.filename)}
                                    className="absolute top-4 right-4 p-1.5 rounded-md text-muted-foreground/50 hover:text-red-500 hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100"
                                    title="Delete file"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <Dialog open={!!selectedFile} onOpenChange={(open) => !open && setSelectedFile(null)}>
                <DialogContent className="sm:max-w-3xl bg-black/90 border-border/50">
                    <DialogHeader>
                        <DialogTitle className="text-left truncate pr-8">{selectedFile}</DialogTitle>
                    </DialogHeader>
                    {selectedFile && (
                        <div className="mt-4">
                            <CustomPlayer
                                src={getRawFileUrl(selectedFile)}
                                type={getFileType(selectedFile)}
                                className="w-full aspect-video"
                            />
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            <AlertDialog open={!!fileToDelete} onOpenChange={(open) => !open && setFileToDelete(null)}>
                <AlertDialogContent className="bg-black/90 border-border/50">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This will permanently delete "{fileToDelete}". If this file was generated by the app,
                            the associated database record and original upload will also be removed.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleConfirmDelete}
                            disabled={isDeleting}
                            className="bg-red-500 hover:bg-red-600 focus:ring-red-500"
                        >
                            {isDeleting ? "Deleting..." : "Delete"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

        </section>
    );
};

export default RawOutputsSection;
