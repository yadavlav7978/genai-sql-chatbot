import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ChatService, ChatRequest, ChatResponse, UploadResponse, FileStatusResponse } from '../../services/chat.service';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    explanation?: string;
    queryResult?: string;
    sql_query?: string;
    suggestions?: string;
    error?: string;
    selectedAgent?: string;
}

@Component({
    selector: 'app-chat',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './chat.component.html',
    styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit, AfterViewChecked {
    @ViewChild('chatContainer') private chatContainer!: ElementRef;
    @ViewChild('fileInput') private fileInput!: ElementRef;

    messages: Message[] = [];
    userMessage: string = '';
    isLoading: boolean = false;
    sessionId: string | null = null;
    uploadedFiles: Array<{ file_id: string, filename: string, table_name: string, file_path: string, uploaded_at: string }> = [];
    uploadedFilesSchemas: Map<string, any> = new Map();
    showSidebar: boolean = true;
    showSchema: boolean = false;
    lastSelectedAgent: string | null = null;
    conversations: Array<{ id: string; title: string; lastMessage: string }> = [];

    constructor(private chatService: ChatService, private sanitizer: DomSanitizer) { }

    ngOnInit(): void {
        this.checkFileStatusOnInit();
    }

    // ... (existing methods remain unchanged) ...

    formatMessage(content: string): any {
        if (!content) return '';

        // 1. Handle Code Blocks (```code```)
        // We do this first to prevent other regexes from messing up code blocks
        const codeBlockRegex = /```([\s\S]*?)```/g;
        let formatted = content.replace(codeBlockRegex, (match, code) => {
            return `<pre><code>${this.escapeHtml(code.trim())}</code></pre>`;
        });

        // 2. Handle Inline Code (`code`)
        const inlineCodeRegex = /`([^`]+)`/g;
        formatted = formatted.replace(inlineCodeRegex, (match, code) => {
            return `<code>${this.escapeHtml(code)}</code>`;
        });

        // 3. Handle Markdown Tables
        // Look for table headers and separators
        const tableRegex = /(\|.*\|\n\|[-:| ]+\|\n(?:\|.*\|\n?)*)/g;
        formatted = formatted.replace(tableRegex, (match) => {
            const rows = match.trim().split('\n');
            let html = '<div class="table-container"><table>';

            rows.forEach((row, index) => {
                // Remove leading/trailing pipes and split
                const cells = row.replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());

                if (index === 0) {
                    html += '<thead><tr>';
                    cells.forEach(cell => html += `<th>${cell}</th>`);
                    html += '</tr></thead><tbody>';
                } else if (index === 1) {
                    // Skip separator row
                    return;
                } else {
                    html += '<tr>';
                    cells.forEach(cell => html += `<td>${cell}</td>`);
                    html += '</tr>';
                }
            });

            html += '</tbody></table></div>';
            return html;
        });

        // 4. Handle Bold (**text**)
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // 5. Handle Italic (*text*)
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // 6. Handle Newlines
        formatted = formatted.replace(/\n/g, '<br>');

        return this.sanitizer.bypassSecurityTrustHtml(formatted);
    }

    private escapeHtml(text: string): string {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // ... (rest of the methods) ...


    checkFileStatusOnInit(): void {
        // Check server for all uploaded files
        this.chatService.checkFileStatus().subscribe({
            next: (response: FileStatusResponse) => {
                if (response.has_files && response.files && response.files.length > 0) {
                    // Load ALL files, not just the first one
                    this.uploadedFiles = response.files;

                    // Populate schemas from response
                    response.files.forEach(file => {
                        if (file.schema) {
                            this.uploadedFilesSchemas.set(file.file_id, file.schema);
                        }
                    });

                    // Save to localStorage
                    localStorage.setItem('uploadedFiles', JSON.stringify(this.uploadedFiles));
                    const schemasObj = Object.fromEntries(this.uploadedFilesSchemas);
                    localStorage.setItem('uploadedFilesSchemas', JSON.stringify(schemasObj));



                    const fileCount = this.uploadedFiles.length;
                    const fileNames = this.uploadedFiles.map(f => f.filename).join(', ');
                    this.messages.push({
                        role: 'assistant',
                        content: `✅ ${fileCount} file(s) found: ${fileNames}. You can directly start chatting! Ask me questions about your data.`,
                        timestamp: new Date()
                    });
                } else {
                    // No files - show upload required message
                    this.uploadedFiles = [];
                    localStorage.removeItem('uploadedFiles');
                    localStorage.removeItem('uploadedFilesSchemas');
                    this.messages.push({
                        role: 'assistant',
                        content: '📁 No data file found. Please upload an Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
                        timestamp: new Date()
                    });
                }
            },
            error: (error) => {
                // Try to load from localStorage as fallback
                const savedFiles = localStorage.getItem('uploadedFiles');
                if (savedFiles) {
                    try {
                        this.uploadedFiles = JSON.parse(savedFiles);

                        // Load schemas from localStorage
                        const savedSchemas = localStorage.getItem('uploadedFilesSchemas');
                        if (savedSchemas) {
                            const schemasObj = JSON.parse(savedSchemas);
                            this.uploadedFilesSchemas = new Map(Object.entries(schemasObj));
                        }

                        const fileCount = this.uploadedFiles.length;
                        const fileNames = this.uploadedFiles.map(f => f.filename).join(', ');
                        this.messages.push({
                            role: 'assistant',
                            content: `✅ ${fileCount} file(s) available: ${fileNames}. You can start chatting!`,
                            timestamp: new Date()
                        });
                    } catch (e) {
                        console.error('Failed to load files from localStorage', e);
                        this.messages.push({
                            role: 'assistant',
                            content: '📁 No data file found. Please upload an Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
                            timestamp: new Date()
                        });
                    }
                } else {
                    this.messages.push({
                        role: 'assistant',
                        content: '📁 No data file found. Please upload an Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
                        timestamp: new Date()
                    });
                }
            }
        });
    }

    ngAfterViewChecked(): void {
        this.scrollToBottom();
    }

    scrollToBottom(): void {
        try {
            if (this.chatContainer) {
                this.chatContainer.nativeElement.scrollTop =
                    this.chatContainer.nativeElement.scrollHeight;
            }
        } catch (err) { }
    }

    addWelcomeMessage(): void {
        this.messages.push({
            role: 'assistant',
            content: 'Hello! I\'m your SQL ChatBot. Please upload an Excel file (.xlsx, .xls, or .csv) to get started, or ask me a question!',
            timestamp: new Date()
        });
    }

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            const file = input.files[0];
            this.uploadFile(file);
        }
    }

    uploadFile(file: File): void {
        // Validate file type
        const allowedTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv'
        ];
        const allowedExtensions = ['.xlsx', '.xls', '.csv'];
        const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();

        if (!allowedExtensions.includes(fileExt)) {
            this.showError('Invalid file type. Please upload .xlsx, .xls, or .csv files.');
            return;
        }

        this.isLoading = true;
        this.chatService.uploadFile(file).subscribe({
            next: (response: UploadResponse) => {
                // Add to files array
                const newFile = {
                    file_id: response.file_id,
                    filename: response.filename,
                    table_name: response.table_name || '',
                    file_path: '',
                    uploaded_at: new Date().toISOString()
                };
                this.uploadedFiles.push(newFile);

                // Store schema if available
                if (response.schema) {
                    this.uploadedFilesSchemas.set(response.file_id, response.schema);
                }

                this.messages.push({
                    role: 'assistant',
                    content: `✅ File "${response.filename}" uploaded successfully! Total files: ${this.uploadedFiles.length}. You can now ask questions about your data.`,
                    timestamp: new Date()
                });
                this.isLoading = false;

                // Reset file input
                if (this.fileInput) {
                    this.fileInput.nativeElement.value = '';
                }

                // Store in localStorage for persistence
                localStorage.setItem('uploadedFiles', JSON.stringify(this.uploadedFiles));
                const schemasObj = Object.fromEntries(this.uploadedFilesSchemas);
                localStorage.setItem('uploadedFilesSchemas', JSON.stringify(schemasObj));
            },
            error: (error) => {
                this.showError(`Upload failed: ${error.error?.detail || error.message}`);
                this.isLoading = false;
            }
        });
    }

    deleteFile(fileId: string): void {
        const fileToDelete = this.uploadedFiles.find(f => f.file_id === fileId);
        if (!fileToDelete) {
            return;
        }

        if (!confirm(`Are you sure you want to delete "${fileToDelete.filename}"?`)) {
            return;
        }

        this.isLoading = true;
        this.chatService.deleteFile(fileId).subscribe({
            next: () => {
                // Remove from array
                this.uploadedFiles = this.uploadedFiles.filter(f => f.file_id !== fileId);
                this.uploadedFilesSchemas.delete(fileId);

                // Update localStorage
                localStorage.setItem('uploadedFiles', JSON.stringify(this.uploadedFiles));
                const schemasObj = Object.fromEntries(this.uploadedFilesSchemas);
                localStorage.setItem('uploadedFilesSchemas', JSON.stringify(schemasObj));

                if (this.uploadedFiles.length === 0) {
                    this.showSchema = false;
                }

                this.messages.push({
                    role: 'assistant',
                    content: `🗑️ File "${fileToDelete.filename}" deleted. ${this.uploadedFiles.length} file(s) remaining.`,
                    timestamp: new Date()
                });
                this.isLoading = false;
            },
            error: (error) => {
                this.showError(`Delete failed: ${error.error?.detail || error.message}`);
                this.isLoading = false;
            }
        });
    }

    sendMessage(): void {
        if (!this.userMessage.trim() || this.isLoading) {
            return;
        }

        const messageText = this.userMessage.trim();
        this.userMessage = '';

        // Add user message
        this.messages.push({
            role: 'user',
            content: messageText,
            timestamp: new Date()
        });

        this.isLoading = true;

        const request: ChatRequest = {
            message: messageText,
            session_id: this.sessionId || undefined
        };

        this.chatService.sendMessage(request).subscribe({
            next: (response: ChatResponse) => {
                this.sessionId = response.session_id;

                // Handle structured response
                const message: Message = {
                    role: 'assistant',
                    content: '', // We'll use explanation and queryResult instead
                    explanation: response.explanation,
                    queryResult: response.query_result,
                    sql_query: response.sql_query,
                    suggestions: response.suggestions,
                    error: response.error,
                    selectedAgent: response.selected_agent,
                    timestamp: new Date()
                };

                this.messages.push(message);

                // Update last selected agent for sidebar display
                if (response.selected_agent) {
                    this.lastSelectedAgent = response.selected_agent;
                }

                this.isLoading = false;
            },
            error: (error) => {
                this.messages.push({
                    role: 'assistant',
                    content: '',
                    error: error.error?.detail || error.message || 'An error occurred',
                    timestamp: new Date()
                });
                this.isLoading = false;
            }
        });
    }

    showError(message: string): void {
        this.messages.push({
            role: 'assistant',
            content: '',
            error: message,
            timestamp: new Date()
        });
    }

    toggleSidebar(): void {
        this.showSidebar = !this.showSidebar;
    }

    newConversation(): void {
        // Clear session and messages
        this.sessionId = null;
        this.messages = [];
        this.showSchema = false;

        // Preserve all uploaded files - just clear the chat history
        if (this.uploadedFiles.length > 0) {
            const fileCount = this.uploadedFiles.length;
            const fileNames = this.uploadedFiles.map(f => f.filename).join(', ');
            this.messages.push({
                role: 'assistant',
                content: `🔄 New chat started! ${fileCount} file(s) remain loaded: ${fileNames}. You can start asking questions right away!`,
                timestamp: new Date()
            });
        } else {
            // No files uploaded
            this.messages.push({
                role: 'assistant',
                content: '📁 New chat started! Please upload an Excel file (.xlsx, .xls, or .csv) to begin chatting about your data.',
                timestamp: new Date()
            });
        }
    }

    toggleSchema(): void {
        this.showSchema = !this.showSchema;
    }

    // Helper method to get schema for a specific file
    getFileSchema(fileId: string): any {
        return this.uploadedFilesSchemas.get(fileId);
    }

    // Get all schemas with their tables grouped
    getAllSchemas(): any[] {
        const schemas: any[] = [];
        this.uploadedFiles.forEach(file => {
            const schema = this.uploadedFilesSchemas.get(file.file_id);
            if (schema) {
                schemas.push({
                    file_id: file.file_id,
                    filename: file.filename,
                    table_name: file.table_name,
                    schema: schema
                });
            }
        });
        return schemas;
    }

    getSchemaTables(): any[] {
        // Get all tables from all files
        const allTables: any[] = [];
        this.uploadedFiles.forEach(file => {
            const schema = this.uploadedFilesSchemas.get(file.file_id);
            if (schema && schema.tables) {
                allTables.push(...schema.tables);
            }
        });
        return allTables;
    }

    getSchemaSummary(): any {
        // Combine summaries from all files
        const combinedSummary: any = {
            total_tables: 0,
            total_columns: 0,
            total_rows: 0
        };
        this.uploadedFiles.forEach(file => {
            const schema = this.uploadedFilesSchemas.get(file.file_id);
            if (schema && schema.summary) {
                combinedSummary.total_tables += schema.summary.total_tables || 0;
                combinedSummary.total_columns += schema.summary.total_columns || 0;
                combinedSummary.total_rows += schema.summary.total_rows || 0;
            }
        });
        return combinedSummary;
    }

    formatTimestamp(date: Date): string {
        return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    getTableKeys(obj: any): string[] {
        return obj ? Object.keys(obj) : [];
    }

    getFormattedAgentName(): string {
        if (!this.lastSelectedAgent) return 'No agent selected';

        // Convert agent names to readable format
        const agentNameMap: { [key: string]: string } = {
            'greeting_agent': 'Greeting Agent',
            'sql_agent': 'SQL Agent',
            'inputValidationAndSqlGeneration_agent': 'Input Validation & SQL Generation',
            'sqlValidatorAndSqlExecutor_agent': 'SQL Validator & Executor'
        };

        return agentNameMap[this.lastSelectedAgent] || this.lastSelectedAgent;
    }

    parseQueryResult(queryResult: string): any {
        if (!queryResult || queryResult.trim() === '') {
            return null;
        }

        try {
            const parsed = JSON.parse(queryResult);
            if (parsed.success && parsed.data && Array.isArray(parsed.data)) {
                return {
                    success: true,
                    data: parsed.data,
                    columns: parsed.columns || [],
                    row_count: parsed.row_count || 0
                };
            }
            return null;
        } catch (e) {
            console.error('Failed to parse query result:', e);
            return null;
        }
    }
}

