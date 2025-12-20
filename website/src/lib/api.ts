// export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";
export const API_BASE_URL = "http://localhost:8080";

export interface RawFileResponse {
  filename: string;
  modified_at: string;
}

export interface Segment {
  id: number;
  start_ms: number;
  end_ms: number;
  action_type: string;
  reason?: string;
}

export interface MediaResponse {
  id: number;
  input_path: string;
  output_path?: string;
  input_type: string;
  filter_audio: boolean;
  filter_video: boolean;
  status: "created" | "processing" | "done" | "failed";
  progress: number;
  current_activity: string;
  logs: string[];
  error_message?: string;
  created_at: string;
  updated_at: string;
  segments: Segment[];
}

export interface MessageResponse {
  message: string;
}

export async function uploadFile(
  file: File,
  filterAudio: boolean = true,
  filterVideo: boolean = false
): Promise<MediaResponse> {
  const formData = new FormData();
  formData.append("file", file);

  // Construct query params
  const params = new URLSearchParams();
  params.append("filter_audio", filterAudio.toString());
  params.append("filter_video", filterVideo.toString());

  const response = await fetch(`${API_BASE_URL}/process?${params.toString()}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Upload failed: ${errorText}`);
  }

  return response.json();
}

export async function getMedia(mediaId: number): Promise<MediaResponse> {
  const response = await fetch(`${API_BASE_URL}/media/${mediaId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Media not found");
    }
    const errorText = await response.text();
    throw new Error(`Failed to fetch media: ${errorText}`);
  }

  return response.json();
}

export async function deleteMedia(mediaId: number): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE_URL}/media/${mediaId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete media: ${errorText}`);
  }

  return response.json();
}

export function getDownloadUrl(mediaId: number, variant: "original" | "processed" = "processed"): string {
  return `${API_BASE_URL}/download/${mediaId}?variant=${variant}`;
}

export async function listMedia(status?: string): Promise<MediaResponse[]> {
  const url = status
    ? `${API_BASE_URL}/media?status=${status}`
    : `${API_BASE_URL}/media`;

  const response = await fetch(url);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to list media: ${errorText}`);
  }

  const data = await response.json();
  return data.items;
}

export async function listRawFiles(): Promise<RawFileResponse[]> {
  const response = await fetch(`${API_BASE_URL}/outputs/files`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to list raw files: ${errorText}`);
  }

  return response.json();
}
