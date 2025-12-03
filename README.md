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
- **Role:** Main traffic controller
- **Responsibility:** Analyzes incoming user messages and routes them to the appropriate agent
- **Routing Logic:**
  - Greetings/Help queries → `greeting_agent`
  - Data queries → `sql_agent`
- **Type:** LlmAgent (intelligent routing)

---

### 2️⃣ **Greeting Agent**
- **Role:** Welcome and onboarding
- **Responsibility:** Greets users and explains chatbot capabilities
- **Behavior:**
  - Responds to "hello", "hi", "what can you do?"
  - Provides friendly introduction
  - Does NOT process SQL queries
- **Type:** Agent (no sub-agents)
- **Restrictions:** Cannot transfer to other agents (isolated)

---

### 3️⃣ **SQL Agent** (Sequential Coordinator)
- **Role:** Orchestrates SQL query processing
- **Responsibility:** Manages a sequential pipeline of two sub-agents
- **Pipeline:**
  1. Input Validation & SQL Generation Agent
  2. SQL Validator & SQL Executor Agent
- **Type:** SequentialAgent (enforces execution order)

---

### 4️⃣ **Input Validation & SQL Generation Agent**
- **Role:** Query validation and SQL creation
- **Responsibilities:**
  1. Retrieves database schema using `get_schema()` tool
  2. Validates user input for safety
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
- **Role:** Final validation and execution
- **Responsibilities:**
  1. Validates SQL is SELECT-only (no destructive operations)
  2. Cross-checks against schema using `get_schema()`
  3. Executes SQL using `execute_sql()` tool
  4. Formats results as Markdown table
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

### **Key Communication Mechanisms:**

1. **State Sharing** - Agents pass data via `state` dictionary:
   - `state['generated_sql']` - SQL query from Agent 4
   - `state['query_result']` - Results from Agent 5

2. **Sequential Execution** - SQL Agent uses SequentialAgent to ensure:
   - Agent 4 completes BEFORE Agent 5 starts
   - No parallel execution in SQL pipeline

3. **Agent Transfers** - Orchestrator can transfer control to:
   - `greeting_agent` (isolated, no peer transfers)
   - `sql_agent` (coordinates sub-agents)

4. **Tool Calls** - Agents interact with data via tools:
   - `get_schema()` - Fetches database structure
   - `execute_sql(query)` - Runs SQL on data

---

## 🛠️ Implementation Details

### **Backend (FastAPI + Google ADK)**

#### **1. Main Entry Point** - `src/app/main_fastapi.py`
- FastAPI application server
- Routes: `/api/chat`, `/api/upload-file`, `/api/health`
- CORS enabled for Angular frontend
- Handles file uploads (Excel/CSV)

#### **2. Chat API** - `src/app/api/chat.py`
- Receives user messages
- Manages session state
- Sends messages to Orchestrator Agent
- Parses responses and returns to frontend

#### **3. Agents** - `src/app/agents/`
Each agent has:
- `agent.py` - Agent configuration
- `prompt.py` - Instructions and behavior rules

#### **4. Tools** - `src/app/tools/`

**`get_schema.py`:**
```python
# Returns database schema (tables, columns, types)
# Used by agents to validate queries
get_schema() -> JSON schema
```

**`execute_sql.py`:**
```python
# Executes SQL on uploaded Excel/CSV
# Loads data into SQLite in-memory database
# Returns query results as JSON
execute_sql(query: str) -> JSON results
```

#### **5. Services** - `src/app/services/`
- `session_service` - Manages conversation state
- `runner` - Executes agent workflows

#### **6. Response Parsing** - `src/app/utils/response_parser.py`
- Extracts explanation, SQL, results, errors from agent output
- Uses delimiters: `<<<EXPLANATION>>>`, `<<<SQL>>>`, `<<<QUERY_RESULT>>>`, `<<<END>>>`

---

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

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ using Google ADK and FastAPI**
