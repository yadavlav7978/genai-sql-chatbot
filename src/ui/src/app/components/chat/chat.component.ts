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
  uploadedFileId: string | null = null;
  uploadedFileName: string | null = null;
  uploadedFileSchema: any = null;
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
    // First check localStorage for persisted file
    const savedFileId = localStorage.getItem('uploadedFileId');
    const savedFileName = localStorage.getItem('uploadedFileName');

    if (savedFileId && savedFileName) {
      // Verify file still exists on server
      this.chatService.checkFileStatus().subscribe({
        next: (response: FileStatusResponse) => {
          if (response.has_file && response.file_id && response.filename) {
            // File exists - show ready to chat message
            this.uploadedFileId = response.file_id;
            this.uploadedFileName = response.filename;
            // Try to load schema from localStorage
            const savedSchema = localStorage.getItem('uploadedFileSchema');
            if (savedSchema) {
              try {
                this.uploadedFileSchema = JSON.parse(savedSchema);
              } catch (e) {
                console.error('Failed to parse saved schema', e);
              }
            }
            this.messages.push({
              role: 'assistant',
              content: `✅ File "${response.filename}" is already uploaded. You can directly start chatting! Ask me questions about your data.`,
              timestamp: new Date()
            });
          } else {
            // File was deleted, clear localStorage
            localStorage.removeItem('uploadedFileId');
            localStorage.removeItem('uploadedFileName');
            this.messages.push({
              role: 'assistant',
              content: '📁 No data file found. Please upload an Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
              timestamp: new Date()
            });
          }
        },
        error: (error) => {
          // On error, check if we have saved file info
          if (savedFileId && savedFileName) {
            this.uploadedFileId = savedFileId;
            this.uploadedFileName = savedFileName;
            // Load schema from localStorage
            const savedSchema = localStorage.getItem('uploadedFileSchema');
            if (savedSchema) {
              try {
                this.uploadedFileSchema = JSON.parse(savedSchema);
              } catch (e) {
                console.error('Failed to parse saved schema', e);
              }
            }
            this.messages.push({
              role: 'assistant',
              content: `✅ File "${savedFileName}" is available. You can start chatting!`,
              timestamp: new Date()
            });
          } else {
            this.messages.push({
              role: 'assistant',
              content: '📁 No data file found. Please upload an Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
              timestamp: new Date()
            });
          }
        }
      });
    } else {
      // No saved file, check server
      this.chatService.checkFileStatus().subscribe({
        next: (response: FileStatusResponse) => {
          if (response.has_file && response.file_id && response.filename) {
            // File exists - show ready to chat message
            this.uploadedFileId = response.file_id;
            this.uploadedFileName = response.filename;
            localStorage.setItem('uploadedFileId', response.file_id);
            localStorage.setItem('uploadedFileName', response.filename);

            // Try to load schema from localStorage first
            const savedSchema = localStorage.getItem('uploadedFileSchema');
            if (savedSchema) {
              try {
                this.uploadedFileSchema = JSON.parse(savedSchema);
              } catch (e) {
                // If parsing fails, fetch from server
                this.loadSchemaFromServer();
              }
            } else {
              // Fetch schema from server
              this.loadSchemaFromServer();
            }

            this.messages.push({
              role: 'assistant',
              content: `✅ File "${response.filename}" is already uploaded. You can directly start chatting! Ask me questions about your data.`,
              timestamp: new Date()
            });
          } else {
            // No file - show upload required message
            this.messages.push({
              role: 'assistant',
              content: '📁 No data file found. Please upload an Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
              timestamp: new Date()
            });
          }
        },
        error: (error) => {
          // On error, show default message
          this.messages.push({
            role: 'assistant',
            content: '📁 No data file found. Please upload an Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
            timestamp: new Date()
          });
        }
      });
    }
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
        this.uploadedFileId = response.file_id;
        this.uploadedFileName = response.filename;
        // Schema will be loaded on-demand when user clicks "Show Schema"
        this.uploadedFileSchema = response.schema || null;
        this.messages.push({
          role: 'assistant',
          content: `✅ File "${response.filename}" uploaded successfully! You can now ask questions about your data.`,
          timestamp: new Date()
        });
        this.isLoading = false;
        // Reset file input
        if (this.fileInput) {
          this.fileInput.nativeElement.value = '';
        }
        // Store in localStorage for persistence
        if (this.uploadedFileId) {
          localStorage.setItem('uploadedFileId', this.uploadedFileId);
          localStorage.setItem('uploadedFileName', this.uploadedFileName || '');
          // Don't store schema if it's null (will be generated on-demand)
          if (this.uploadedFileSchema) {
            localStorage.setItem('uploadedFileSchema', JSON.stringify(this.uploadedFileSchema));
          }
        }
      },
      error: (error) => {
        this.showError(`Upload failed: ${error.error?.detail || error.message}`);
        this.isLoading = false;
      }
    });
  }

  deleteCurrentFile(): void {
    if (!this.uploadedFileName) {
      return;
    }

    if (!confirm(`Are you sure you want to delete "${this.uploadedFileName}"? You'll need to upload a new file to continue chatting.`)) {
      return;
    }

    this.isLoading = true;
    this.chatService.deleteFile().subscribe({
      next: () => {
        this.uploadedFileId = null;
        this.uploadedFileName = null;
        this.uploadedFileSchema = null;
        this.showSchema = false;
        localStorage.removeItem('uploadedFileId');
        localStorage.removeItem('uploadedFileName');
        localStorage.removeItem('uploadedFileSchema');
        this.messages.push({
          role: 'assistant',
          content: '🗑️ File deleted. Please upload a new Excel file (.xlsx, .xls, or .csv) to start chatting about your data.',
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

    // Check if there's an existing file on the server
    this.chatService.checkFileStatus().subscribe({
      next: (response: FileStatusResponse) => {
        if (response.has_file && response.file_id && response.filename) {
          // File exists on server - preserve it
          this.uploadedFileId = response.file_id;
          this.uploadedFileName = response.filename;

          // Update localStorage
          localStorage.setItem('uploadedFileId', response.file_id);
          localStorage.setItem('uploadedFileName', response.filename);

          // Try to load schema from localStorage or fetch from server
          const savedSchema = localStorage.getItem('uploadedFileSchema');
          if (savedSchema) {
            try {
              this.uploadedFileSchema = JSON.parse(savedSchema);
            } catch (e) {
              console.error('Failed to parse saved schema', e);
              this.loadSchemaFromServer();
            }
          } else {
            this.loadSchemaFromServer();
          }

          // Show message that file is ready for new chat
          this.messages.push({
            role: 'assistant',
            content: `🔄 New chat started! File "${response.filename}" is already loaded. You can start asking questions right away!`,
            timestamp: new Date()
          });
        } else {
          // No file exists - clear everything and prompt upload
          this.uploadedFileId = null;
          this.uploadedFileName = null;
          this.uploadedFileSchema = null;
          localStorage.removeItem('uploadedFileId');
          localStorage.removeItem('uploadedFileName');
          localStorage.removeItem('uploadedFileSchema');

          this.messages.push({
            role: 'assistant',
            content: '📁 New chat started! Please upload an Excel file (.xlsx, .xls, or .csv) to begin chatting about your data.',
            timestamp: new Date()
          });
        }
      },
      error: (error) => {
        // On error, check localStorage as fallback
        const savedFileId = localStorage.getItem('uploadedFileId');
        const savedFileName = localStorage.getItem('uploadedFileName');

        if (savedFileId && savedFileName) {
          // Use saved file info
          this.uploadedFileId = savedFileId;
          this.uploadedFileName = savedFileName;

          // Try to load schema
          const savedSchema = localStorage.getItem('uploadedFileSchema');
          if (savedSchema) {
            try {
              this.uploadedFileSchema = JSON.parse(savedSchema);
            } catch (e) {
              console.error('Failed to parse saved schema', e);
            }
          }

          this.messages.push({
            role: 'assistant',
            content: `🔄 New chat started! File "${savedFileName}" is available. You can start asking questions!`,
            timestamp: new Date()
          });
        } else {
          // No file available anywhere
          this.uploadedFileId = null;
          this.uploadedFileName = null;
          this.uploadedFileSchema = null;
          localStorage.removeItem('uploadedFileId');
          localStorage.removeItem('uploadedFileName');
          localStorage.removeItem('uploadedFileSchema');

          this.messages.push({
            role: 'assistant',
            content: '📁 New chat started! Please upload an Excel file (.xlsx, .xls, or .csv) to begin chatting about your data.',
            timestamp: new Date()
          });
        }
      }
    });
  }

  toggleSchema(): void {
    this.showSchema = !this.showSchema;
    // Load schema from localStorage or fetch from server if not already loaded
    if (this.showSchema && !this.uploadedFileSchema && this.uploadedFileName) {
      const savedSchema = localStorage.getItem('uploadedFileSchema');
      if (savedSchema) {
        try {
          this.uploadedFileSchema = JSON.parse(savedSchema);
        } catch (e) {
          console.error('Failed to parse saved schema', e);
          // If parsing fails, fetch from server
          this.loadSchemaFromServer();
        }
      } else {
        // No saved schema, fetch from server
        this.loadSchemaFromServer();
      }
    }
  }

  getSchemaTables(): any[] {
    return this.uploadedFileSchema?.tables || [];
  }

  getSchemaSummary(): any {
    return this.uploadedFileSchema?.summary || {};
  }

  formatTimestamp(date: Date): string {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  getTableKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }

  loadSchemaFromServer(): void {
    this.chatService.getSchema().subscribe({
      next: (response) => {
        if (response.schema) {
          this.uploadedFileSchema = response.schema;
          localStorage.setItem('uploadedFileSchema', JSON.stringify(response.schema));
        }
      },
      error: (error) => {
        console.error('Failed to load schema:', error);
      }
    });
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
}

