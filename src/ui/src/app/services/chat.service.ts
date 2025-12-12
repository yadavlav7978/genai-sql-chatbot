import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  status: string;
  explanation: string;
  query_result?: string;
  sql_query?: string;
  error?: string;
  suggestions?: string;
  selected_agent?: string;
  session_id: string;
}

export interface FileInfo {
  file_id: string;
  filename: string;
  table_name: string;
  file_path: string;
  schema?: any;
  uploaded_at: string;
}

export interface UploadResponse {
  status: string;
  message?: string;
  file_id: string;
  file_path?: string;
  filename: string;
  table_name: string;
  schema?: any;
  schema_summary?: string;
  total_files: number;
  max_files: number;
}

export interface FileStatusResponse {
  status: string;
  has_files: boolean;  // Changed from has_file
  files: FileInfo[];   // List of all files
  total_files: number;
  max_files: number;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  uploadFile(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<UploadResponse>(`${this.apiUrl}/upload-file`, formData);
  }

  sendMessage(request: ChatRequest): Observable<ChatResponse> {
    const formData = new FormData();
    formData.append('message', request.message);
    if (request.session_id) {
      formData.append('session_id', request.session_id);
    }

    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, formData);
  }

  checkFileStatus(): Observable<FileStatusResponse> {
    return this.http.get<FileStatusResponse>(`${this.apiUrl}/file-status`);
  }

  // Delete a specific file by ID
  deleteFile(fileId: string): Observable<{ status: string; message: string; file_id: string; total_files: number; max_files: number }> {
    return this.http.delete<{ status: string; message: string; file_id: string; total_files: number; max_files: number }>(`${this.apiUrl}/file/${fileId}`);
  }

  // Delete all files
  deleteAllFiles(): Observable<{ status: string; message: string; deleted_count: number }> {
    return this.http.delete<{ status: string; message: string; deleted_count: number }>(`${this.apiUrl}/files/all`);
  }




  deleteSession(sessionId: string): Observable<{ status: string; message: string; session_id: string }> {
    return this.http.delete<{ status: string; message: string; session_id: string }>(`${this.apiUrl}/session/${sessionId}`);
  }
}
