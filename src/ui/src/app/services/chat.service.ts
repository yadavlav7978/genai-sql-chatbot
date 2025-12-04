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
  selected_agent?: string;
  session_id: string;
}

export interface UploadResponse {
  status: string;
  message: string;
  file_id: string;
  file_path: string;
  filename: string;
  schema?: any;
  schema_summary?: string;
}

export interface FileStatusResponse {
  status: string;
  has_file: boolean;
  file_id?: string;
  filename?: string;
  file_path?: string;
  message?: string;
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

  deleteFile(): Observable<{ status: string; message: string }> {
    return this.http.delete<{ status: string; message: string }>(`${this.apiUrl}/file`);
  }

  getSchema(): Observable<{ status: string; schema: any; schema_summary: string }> {
    return this.http.get<{ status: string; schema: any; schema_summary: string }>(`${this.apiUrl}/schema/current`);
  }

  deleteSession(sessionId: string): Observable<{ status: string; message: string; session_id: string }> {
    return this.http.delete<{ status: string; message: string; session_id: string }>(`${this.apiUrl}/session/${sessionId}`);
  }
}

