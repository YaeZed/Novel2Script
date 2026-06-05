import axios from "axios";

export type ConversionStatus = "pending" | "processing" | "completed" | "failed";

export interface ConvertResponse {
  task_id: string;
}

export interface StatusResponse {
  id: string;
  status: ConversionStatus;
  progress: number;
  chapters_done: number;
  total_chapters: number;
  error_message: string;
  llm_provider: string;
}

export interface ResultResponse {
  id: string;
  script_yaml: string;
  characters: Array<Record<string, string>>;
  chapters: Array<{
    index: number;
    title: string;
    text: string;
    excerpt: string;
  }>;
  status: ConversionStatus;
  error_message: string;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});

export async function createConversion(payload: { text?: string; file?: File }): Promise<ConvertResponse> {
  const formData = new FormData();
  if (payload.text) {
    formData.append("text", payload.text);
  }
  if (payload.file) {
    formData.append("file", payload.file);
  }

  const response = await api.post<ConvertResponse>("/api/convert", formData);
  return response.data;
}

export async function getStatus(taskId: string): Promise<StatusResponse> {
  const response = await api.get<StatusResponse>(`/api/status/${taskId}`);
  return response.data;
}

export async function getResult(taskId: string): Promise<ResultResponse> {
  const response = await api.get<ResultResponse>(`/api/result/${taskId}`);
  return response.data;
}
