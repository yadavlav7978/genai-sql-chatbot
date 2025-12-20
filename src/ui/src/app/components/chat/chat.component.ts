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
    suggestions?: string[];
    error?: string;
    selected_agent?: string;
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
    activeRequests: number = 0;
    sessionId: string | null = null;
    uploadedFiles: Array<{ file_id: string, filename: string, table_name: string, file_path: string, uploaded_at: string }> = [];
    uploadedFilesSchemas: Map<string, any> = new Map();
    showSidebar: boolean = true;
    showSchema: boolean = false;
    showUploadModal: boolean = false;
    lastSelectedAgent: string | null = null;
    conversations: Array<{ id: string; title: string; lastMessage: string }> = [];

    constructor(private chatService: ChatService, private sanitizer: DomSanitizer) { }

    private updateLoadingState(): void {
        this.isLoading = this.activeRequests > 0;
    }

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
                        console.error('Failed to load files from localStorage', e);
                    }
                } else {
                    // No files - show upload required message logic handled by template
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
            Array.from(input.files).forEach(file => this.uploadFile(file));
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

        this.activeRequests++;
        this.updateLoadingState();

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

                this.activeRequests--;
                this.updateLoadingState();

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
                this.activeRequests--;
                this.updateLoadingState();
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

        this.activeRequests++;
        this.updateLoadingState();

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

                this.activeRequests--;
                this.updateLoadingState();
            },
            error: (error) => {
                this.showError(`Delete failed: ${error.error?.detail || error.message}`);
                this.activeRequests--;
                this.updateLoadingState();
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

        this.activeRequests++;
        this.updateLoadingState();

        const request: ChatRequest = {
            message: messageText,
            session_id: this.sessionId || undefined
        };

        this.chatService.sendMessage(request).subscribe({
            next: (response: ChatResponse) => {
                this.sessionId = response.session_id;

                // DEBUG: Log the raw response from backend
                console.log('=== BACKEND RESPONSE ===' );
                console.log('Full response:', response);
                console.log('Explanation:', response.explanation);
                console.log('Query Result (raw):', response.query_result);
                console.log('SQL Query:', response.sql_query);

                // Handle structured response
                const message: Message = {
                    role: 'assistant',
                    content: '', // We'll use explanation and queryResult instead
                    explanation: response.explanation,
                    queryResult: response.query_result,
                    sql_query: response.sql_query,
                    suggestions: response.suggestions,
                    error: response.error,
                    selected_agent: response.selected_agent,
                    timestamp: new Date()
                };

                // DEBUG: Test the parsing immediately
                if (response.query_result) {
                    console.log('=== TESTING PARSING ===');
                    const isMulti = this.isMultiQuery(response.query_result);
                    console.log('Is Multi Query?', isMulti);
                    if (isMulti) {
                        const parsed = this.parseMultiQueryResult(response.query_result);
                        console.log('Parsed Results:', parsed);
                    }
                }

                this.messages.push(message);

                // Update last selected agent for sidebar display
                if (response.selected_agent) {
                    this.lastSelectedAgent = response.selected_agent;
                }

                this.activeRequests--;
                this.updateLoadingState();
            },
            error: (error) => {
                this.messages.push({
                    role: 'assistant',
                    content: '',
                    error: error.error?.detail || error.message || 'An error occurred',
                    timestamp: new Date()
                });
                this.activeRequests--;
                this.updateLoadingState();
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

    openUploadModal(): void {
        this.showUploadModal = true;
    }

    closeUploadModal(): void {
        this.showUploadModal = false;
    }

    onDragOver(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        event.dataTransfer!.dropEffect = 'copy';
    }

    onDragLeave(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
    }

    onDrop(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            // Handle multiple files if needed, for now just taking the first one or iterating
            Array.from(files).forEach(file => this.uploadFile(file));
        }
    }

    deleteAllFiles(): void {
        if (!this.uploadedFiles || this.uploadedFiles.length === 0) return;

        if (!confirm('Are you sure you want to delete ALL files? This action cannot be undone.')) {
            return;
        }

        // We'll delete them one by one for now as we don't have a bulk delete API
        const filesClone = [...this.uploadedFiles];
        let deleteCount = 0;

        filesClone.forEach(file => {
            this.chatService.deleteFile(file.file_id).subscribe({
                next: () => {
                    this.uploadedFiles = this.uploadedFiles.filter(f => f.file_id !== file.file_id);
                    this.uploadedFilesSchemas.delete(file.file_id);
                    deleteCount++;

                    // Check if all are deleted
                    if (deleteCount === filesClone.length) {
                        this.updateLocalStorageAfterDelete();
                        // Reset to fresh state: clear chat, clear agent, show welcome message
                        this.lastSelectedAgent = null;
                        this.newConversation();
                    }
                },
                error: (err) => {
                    console.error(`Failed to delete file ${file.filename}`, err);
                }
            });
        });
    }

    private updateLocalStorageAfterDelete(): void {
        localStorage.setItem('uploadedFiles', JSON.stringify(this.uploadedFiles));
        const schemasObj = Object.fromEntries(this.uploadedFilesSchemas);
        localStorage.setItem('uploadedFilesSchemas', JSON.stringify(schemasObj));
        if (this.uploadedFiles.length === 0) {
            this.showSchema = false;
        }
    }

    newConversation(): void {
        // Clear session and messages
        this.sessionId = null;
        this.messages = [];
        this.showSchema = false;
        this.lastSelectedAgent = null; // Clear selected agent

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
            // No files uploaded - visual welcome state will naturally appear
        }
    }

    toggleSchema(): void {
        this.showSchema = !this.showSchema;
    }

    // Helper method to get schema for a specific file
    getFileSchema(fileId: string): any {
        return this.uploadedFilesSchemas.get(fileId);
    }


    formatTimestamp(date: Date): string {
        return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }



    formatQueryName(queryName: string): string {
        // Convert snake_case to Title Case
        // e.g., "Age_of_Arjun" -> "Age of Arjun"
        return queryName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
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

    isMultiQuery(queryResult: string): boolean {
        console.log('=== isMultiQuery CALLED ===');
        console.log('Input queryResult type:', typeof queryResult);
        console.log('Input queryResult value:', queryResult);
        
        if (!queryResult || queryResult.trim() === '') {
            console.log('Empty query result, returning false');
            return false;
        }

        try {
            const parsed = JSON.parse(queryResult);
            console.log('Parsed JSON:', parsed);
            console.log('Is object?', typeof parsed === 'object');
            console.log('Is array?', Array.isArray(parsed));
            console.log('Has success?', 'success' in parsed);
            
            // Check if it's a multi-query result (object with multiple query keys)
            // Each key should point to an object with success, data, row_count, columns
            if (typeof parsed === 'object' && !Array.isArray(parsed) && !parsed.success) {
                const keys = Object.keys(parsed);
                console.log('Object keys:', keys);
                if (keys.length > 0) {
                    // Check if at least one key has the multi-query structure
                    const firstKey = keys[0];
                    console.log('First key:', firstKey);
                    console.log('First key value:', parsed[firstKey]);
                    if (parsed[firstKey] && typeof parsed[firstKey] === 'object' &&
                        'success' in parsed[firstKey] && 'data' in parsed[firstKey]) {
                        console.log('✓ Is multi-query format, returning true');
                        return true;
                    }
                }
            }
            console.log('Not multi-query format, returning false');
            return false;
        } catch (e) {
            console.error('Error parsing queryResult:', e);
            return false;
        }
    }

    parseMultiQueryResult(queryResult: string): any[] {
        console.log('=== parseMultiQueryResult CALLED ===');
        if (!queryResult || queryResult.trim() === '') {
            console.log('Empty queryResult, returning []');
            return [];
        }

        try {
            const parsed = JSON.parse(queryResult);
            console.log('Parsed JSON in parseMultiQueryResult:', parsed);
            const results: any[] = [];

            // Each key is a query name, value is the result object
            for (const queryName of Object.keys(parsed)) {
                console.log('Processing query:', queryName);
                const queryData = parsed[queryName];
                console.log('Query data:', queryData);
                if (queryData && typeof queryData === 'object') {
                    const resultObject = {
                        queryName: queryName,
                        success: queryData.success || false,
                        summary: queryData.summary || null,
                        data: queryData.data || [],
                        columns: queryData.columns || [],
                        row_count: queryData.row_count || 0,
                        error: queryData.error || null
                    };
                    console.log('Adding result object:', resultObject);
                    results.push(resultObject);
                }
            }

            console.log('Final parsed results array:', results);
            console.log('Results count:', results.length);
            return results;
        } catch (e) {
            console.error('Failed to parse multi-query result:', e);
            return [];
        }
    }





}

