export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  segments: Segment[];
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

export function getDownloadUrl(mediaId: number): string {
  return `${API_BASE_URL}/download/${mediaId}`;
}
