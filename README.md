# SQL ChatBot 🤖

An intelligent SQL chatbot powered by **Google ADK (Agent Development Kit)** that allows users to interact with Excel/CSV files using natural language queries. Upload your data file, ask questions in plain English, and get instant SQL query results.

---

## 📖 Table of Contents

- [What is SQL ChatBot?](#what-is-sql-chatbot)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Available Agents](#available-agents)
- [How Agents Communicate](#how-agents-communicate)
- [Implementation Details](#implementation-details)
- [Setup & Installation](#setup--installation)
- [How to Use](#how-to-use)
- [Tech Stack](#tech-stack)

---

## 🎯 What is SQL ChatBot?

SQL ChatBot is an **AI-powered conversational interface** that enables users to query Excel and CSV files using natural language instead of writing complex SQL queries. The system automatically:

- Understands your questions in plain English
- Generates safe, valid SQL queries
- Executes queries on your uploaded data
- Returns results in an easy-to-read format

**Example:**
- **You ask:** "Show me all employees older than 30"
- **ChatBot:** Generates `SELECT * FROM Employees WHERE Age > 30`, executes it, and displays the results

---

## ✨ Key Features

- **Natural Language Processing** - Ask questions in plain English
- **Multi-Agent Architecture** - Specialized agents handle different tasks for better accuracy
- **Automatic SQL Generation** - No need to write SQL manually
- **Excel/CSV Support** - Upload and query Excel or CSV files
- **Safety First** - Only read-only SELECT queries are allowed
- **Schema Awareness** - Validates queries against actual column names
- **Conversational Memory** - Maintains context across multiple questions
- **Web Interface** - Clean Angular-based UI for easy interaction

---

## 🏗️ System Architecture

The SQL ChatBot uses a **multi-agent architecture** powered by Google ADK. The system consists of:

```
┌─────────────────────────────────────────────────┐
│           User Query (Natural Language)         │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Orchestrator Agent    │ ◄── Entry Point
         │  (Routes Requests)     │
         └────────┬───────────────┘
                  │
         ┌────────┴────────┐
         │                  │
         ▼                  ▼
  ┌─────────────┐    ┌──────────────┐
  │  Greeting   │    │  SQL Agent   │
  │   Agent     │    │ (Sequential) │
  └─────────────┘    └──────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                            │
              ▼                            ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│ Input Validation &       │  │ SQL Validator &          │
│ SQL Generation Agent     │──│ SQL Executor Agent       │
└──────────────────────────┘  └──────────────────────────┘
              │                            │
              │         Uses Tools         │
              └────────────┬───────────────┘
                           │
              ┌────────────┴────────────┐
              │                          │
              ▼                          ▼
       ┌──────────┐             ┌──────────────┐
       │get_schema│             │ execute_sql  │
       └──────────┘             └──────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │ Query Results    │
                              │ (Markdown Table) │
                              └──────────────────┘
```

---

## 👥 Available Agents

The chatbot uses **5 specialized AI agents**, each with a specific responsibility:

### 1️⃣ **Orchestrator Agent** (Entry Point)
- **Responsibility:** This is the main entry point agent that routes user queries to the appropriate sub-agent.
It analyzes the user's intent and transfers to either the greeting agent or SQL agent.

---

### 2️⃣ **Greeting Agent**
- **Responsibility:** This agent welcomes the user and provides an introduction to the SQL Chatbot system.It explains what the chatbot can do and how the user should proceed.

---

### 3️⃣ **SQL Agent** (Sequential Coordinator)
- **Responsibility:** SQL Agent handles SQL query sequentially through 2 subagents.
- **2 steps pipeline:**
  1. Input Validation & SQL Generation Agent : - Validate user input + Generate SQL
  2. SQL Validator & SQL Executor Agent : - Validate SQL + Execute SQL

---

### 4️⃣ **Input Validation & SQL Generation Agent**
- **Responsibilities:**
  1. This agent validates the user's input and generates a safe SQL query.
  2. Validates user input for safety (only read query allowed, No write operation allowed)
  3. Checks if requested columns/tables exist
  4. Generates valid SQL query
- **Tools:** `get_schema`
- **Output:** Stores generated SQL in `state['generated_sql']`
- **Validation Rules:**
  - Rejects unsafe queries
  - Warns about missing columns
  - Only uses existing schema columns

---

### 5️⃣ **SQL Validator & SQL Executor Agent**
- **Responsibilities:**
  1. This agent validates SQL, executes it, and returns a user-friendly response.
  2. Cross-checks against schema using `get_schema()`
  3. Executes SQL using `execute_sql()` tool
- **Tools:** `execute_sql`, `get_schema`
- **Input:** Reads SQL from `state['generated_sql']`
- **Output:** Stores results in `state['query_result']`

---

## 🔄 How Agents Communicate

The agents communicate in a **sequential, ordered workflow**:

```
Step 1: User sends message
   │
   ▼
Step 2: Orchestrator Agent receives message
   │   • Analyzes intent
   │   • Decides: Greeting or SQL query?
   │
   ├─► [Greeting Path]
   │   └─► Greeting Agent responds → Done ✓
   │
   └─► [SQL Path]
       │
       Step 3: SQL Agent (Sequential) activates
       │
       ├─► Sub-Agent 1: Input Validation & SQL Generation
       │   │
       │   ├─► Calls get_schema() tool
       │   ├─► Validates user input
       │   ├─► Generates SQL query
       │   └─► Stores in state['generated_sql']
       │
       └─► Sub-Agent 2: SQL Validator & Executor
           │   (Automatically runs AFTER Sub-Agent 1)
           │
           ├─► Reads state['generated_sql']
           ├─► Validates SQL is safe
           ├─► Calls execute_sql(query) tool
           ├─► Formats results as table
           └─► Stores in state['query_result']
           
Step 4: Results returned to user ✓
```


### **Frontend (Angular)**

#### **Location:** `src/ui/`

- **Component:** `chat.component.ts` - Handles user input and displays messages
- **Styling:** `chat.component.css` - Beautiful, modern UI
- **API Calls:** Sends messages to `/api/chat` endpoint

---

## 🚀 Setup & Installation

### **Prerequisites**
- Python 3.8+
- Node.js 14+ (for Angular frontend)
- Google API Key (for Google ADK)

### **Step 1: Clone Repository**
```bash
git clone <repository-url>
cd genai-sql-chatbot
```

### **Step 2: Create Virtual Environment**
```bash
python -m venv venv
```

### **Step 3: Activate Virtual Environment**
```bash
# Windows
venv\Scripts\Activate

# Linux/Mac
source venv/bin/activate
```

### **Step 4: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 5: Set Up Google API Key**

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL=gemini-2.0-flash-exp
```

Or set environment variable:
```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your_google_api_key_here"
$env:MODEL="gemini-2.0-flash-exp"

# Linux/Mac
export GOOGLE_API_KEY="your_google_api_key_here"
export MODEL="gemini-2.0-flash-exp"
```

### **Step 6: Run Backend Server**
```bash
# Using Python module
python -m src.app.main_fastapi

# Or using uvicorn directly
uvicorn src.app.main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

Backend will start at: `http://localhost:8000`

### **Step 7: Run Frontend (Optional)**
```bash
cd src/ui
npm install
npm start
```

Frontend will start at: `http://localhost:4200`

---

## 📝 How to Use

### **1. Upload a File**
- Click "Upload File" in the web interface
- Select an Excel (.xlsx, .xls) or CSV file
- The chatbot will automatically extract the schema

### **2. Ask Questions**
Use natural language to query your data:

**Examples:**
```
"Show me all records"
"How many rows are in the data?"
"What are the column names?"
"List all employees with salary > 50000"
"Get the average age by department"
"Show top 10 highest-paid employees"
"Count records where status is 'active'"
```

### **3. View Results**
- The chatbot will show:
  - An explanation of what it's doing
  - The generated SQL query
  - Results in a formatted table

---

## 🧰 Tech Stack

### **Backend**
- **FastAPI** - Modern Python web framework
- **Google ADK** - Agent Development Kit for multi-agent AI
- **Google Gemini** - LLM for natural language understanding
- **Azure OpenAI** - LLM for natural language understanding
- **SQLite** - In-memory database for query execution
- **Pandas** - Excel/CSV file processing

### **Frontend**
- **Angular** - Web application framework
- **TypeScript** - Type-safe JavaScript
- **HTML/CSS** - Modern, responsive UI

### **Development Tools**
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Python-dotenv** - Environment configuration

---

## 📂 Project Structure

```
genai-sql-chatbot/
├── src/
│   ├── app/
│   │   ├── agents/           # All AI agents
│   │   │   ├── orchestrator_agent/
│   │   │   ├── greeting_agent/
│   │   │   ├── sql_agent/
│   │   │   ├── inputValidationAndSqlGeneration_agent/
│   │   │   └── sqlValidatorAndSqlExecutor_agent/
│   │   ├── api/              # API routes
│   │   │   ├── chat.py
│   │   │   ├── file_manager.py
│   │   │   └── health.py
│   │   ├── tools/            # Agent tools
│   │   │   ├── get_schema.py
│   │   │   └── execute_sql.py
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Helper functions
│   │   ├── configs/          # Configuration
│   │   └── main_fastapi.py   # Application entry
│   └── ui/                   # Angular frontend
├── uploads/                  # Uploaded files
├── schemas/                  # Stored schemas
├── requirements.txt
└── README.md
```


