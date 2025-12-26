// In prod (nginx), use same-origin /api
// In dev (vite), you can still set VITE_API_URL=http://localhost:8000 if you want,
// but simplest is also /api + vite proxy.
export const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ||
  "http://localhost:8080";

// Auth token management
const TOKEN_KEY = "auth_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getAuthHeaders(): HeadersInit {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// Auth interfaces
export interface UserResponse {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

// Auth API functions
export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(error.detail || "Login failed");
  }

  const data: TokenResponse = await response.json();
  if (data.access_token) {
    setToken(data.access_token);
    console.debug("Token saved to localStorage");
  } else {
    console.error("No access_token in login response");
  }
  return data;
}

export async function register(data: RegisterRequest): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(error.detail || "Registration failed");
  }

  return response.json();
}

export async function getCurrentUser(): Promise<UserResponse> {
  const headers = getAuthHeaders();
  const token = getToken();
  
  // Debug logging (remove in production)
  if (!token) {
    console.warn("No token found in localStorage");
  }
  
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      const errorText = await response.text().catch(() => "Unauthorized");
      console.error("401 Unauthorized:", errorText);
      console.error("Token was:", token ? `${token.substring(0, 20)}...` : "missing");
      removeToken();
      throw new Error("Unauthorized");
    }
    throw new Error("Failed to fetch user");
  }

  return response.json();
}

export function logout(): void {
  removeToken();
}

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
  filterVideo: boolean = false,
  subtitleFile?: File
): Promise<MediaResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (subtitleFile) {
    formData.append("subtitle_file", subtitleFile);
  }

  // Construct query params
  const params = new URLSearchParams();
  params.append("filter_audio", filterAudio.toString());
  params.append("filter_video", filterVideo.toString());

  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/process?${params.toString()}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    const errorText = await response.text();
    throw new Error(`Upload failed: ${errorText}`);
  }

  return response.json();
}
export async function deleteRawFile(filename: string): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE_URL}/outputs/files/${encodeURIComponent(filename)}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    const errorText = await response.text();
    throw new Error(`Failed to delete raw file: ${errorText}`);
  }

  return response.json();
}
export function getRawFileUrl(filename: string): string {
  const token = getToken();
  return token
    ? `${API_BASE_URL}/outputs/files/${encodeURIComponent(filename)}?token=${token}`
    : `${API_BASE_URL}/outputs/files/${encodeURIComponent(filename)}`;
}

export async function getMedia(mediaId: number): Promise<MediaResponse> {
  const response = await fetch(`${API_BASE_URL}/media/${mediaId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
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
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    const errorText = await response.text();
    throw new Error(`Failed to delete media: ${errorText}`);
  }

  return response.json();
}

export function getDownloadUrl(mediaId: number, variant: "original" | "processed" = "processed"): string {
  // For video player, add token as query param (backend supports both header and query param)
  const token = getToken();
  return token
    ? `${API_BASE_URL}/download/${mediaId}?variant=${variant}&token=${token}`
    : `${API_BASE_URL}/download/${mediaId}?variant=${variant}`;
}

export async function getAuthenticatedVideoUrl(mediaId: number, variant: "original" | "processed" = "processed"): Promise<string> {
  // Fetch video with auth and create blob URL for player
  const response = await fetch(`${API_BASE_URL}/download/${mediaId}?variant=${variant}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    throw new Error("Failed to load video");
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export async function downloadMedia(mediaId: number, variant: "original" | "processed" = "processed", filename?: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/download/${mediaId}?variant=${variant}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    throw new Error("Download failed");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || `download_${mediaId}_${variant}.mp4`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function listMedia(status?: string): Promise<MediaResponse[]> {
  const url = status
    ? `${API_BASE_URL}/media?status=${status}`
    : `${API_BASE_URL}/media`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    const errorText = await response.text();
    throw new Error(`Failed to list media: ${errorText}`);
  }

  const data = await response.json();
  return data.items;
}

export async function listRawFiles(): Promise<RawFileResponse[]> {
  const response = await fetch(`${API_BASE_URL}/outputs/files`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    const errorText = await response.text();
    throw new Error(`Failed to list raw files: ${errorText}`);
  }

  return response.json();
}

export interface StatsResponse {
  total_media: number;
  total_segments: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

export async function getStats(): Promise<StatsResponse> {
  const response = await fetch(`${API_BASE_URL}/stats`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error("Unauthorized - please login again");
    }
    const errorText = await response.text();
    throw new Error(`Failed to fetch stats: ${errorText}`);
  }

  return response.json();
}