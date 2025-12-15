# SQL ChatBot 🤖

SQL ChatBot is an intelligent, **multi-agent GenAI application** built using **Google ADK (Agent Development Kit)**.  
It enables users to interact with Excel and CSV files using **natural language**, automatically translating questions into **safe, schema-aware SQL queries** and returning clear, structured results through a modern web interface.
The system automatically:
- Understands your questions in plain English
- Generates safe, valid SQL queries
- Executes queries on your uploaded data
- Returns results in an easy-to-read format

---

## ❓ Why SQL ChatBot?

Traditional data analysis requires users to write complex SQL queries and understand database schemas and table relationships. This can be time-consuming and challenging, especially for users who are not familiar with SQL.

SQL ChatBot removes this barrier by allowing users to ask questions in plain English.
The chatbot understands natural language queries, generates safe and accurate SQL in the background, executes it on the data, and returns results in a clear, readable format.

---


## 🏗️ System Architecture

The SQL ChatBot uses a **multi-agent architecture** powered by Google ADK. The system consists of:

![Data Flow Diagram](doc/Sql-chatbot-architecture.png)

---

## 👥 Available Agents

The chatbot uses **5 specialized AI agents**, each with a specific responsibility:

### 1️⃣ **Orchestrator Agent** (Entry Point)
- **Responsibility:** This is the main entry point agent that routes user queries to the appropriate sub-agent.
It analyzes the user's intent and transfers to either the greeting agent or SQL agent.


### 2️⃣ **Greeting Agent**
- **Responsibility:** This agent welcomes the user and provides an introduction to the SQL Chatbot system. It explains what the chatbot can do and how the user should proceed.
- **Capabilities:**
  - Fetches schema using `get_schema`
  - Generates 4 sample questions relevant to the user's data


### 3️⃣ **SQL Agent** (Sequential Coordinator)
- **Responsibility:** SQL Agent handles SQL query sequentially through 2 subagents.
- **2 steps pipeline:**
  1. Input Validation & SQL Generation Agent : - Validate user input + Generate SQL
  2. SQL Validator & SQL Executor Agent : - Validate SQL + Execute SQL


### 4️⃣ **Input Validation & SQL Generation Agent**
- **Responsibilities:**
  1. This agent validates the user's input and generates a safe SQL query.
  2. Validates user input for safety (only read query allowed, No write operation allowed)
  3. Checks if requested columns/tables exist
  4. Generates valid SQL query
- **Tools:** `get_schema`
- **Output:** 
  - Stores generated SQL in `state['generated_sql']`
  - **Crucial:** Passes the full retrieved `schema` to the next agent
- **Validation Rules:**
  - Rejects unsafe queries
  - Warns about missing columns
  - Only uses existing schema columns


### 5️⃣ **SQL Validator & SQL Executor Agent**
- **Responsibilities:**
  1. This agent validates SQL, executes it, and returns a user-friendly response.
  2. Cross-checks against schema (received from previous agent, does **not** call `get_schema` again)
  3. Executes SQL using `execute_sql()` tool
  4. Generates post-query **Suggestions** (follow-up questions)
- **Tools:** `execute_sql`
- **Input:** Reads SQL and Schema from `state['generated_sql']`
- **Output:** Stores results in `state['query_result']`

---

## 🔌 Model Context Protocol (MCP)

This application uses the **Model Context Protocol (MCP)** to standardize how AI agents interact with external tools and data.

### **Architecture**
- **MCP Server**: A standalone process (running on port `8001`) that exposes the `get_schema` and `execute_sql` tools. It has direct access to the database and file system.
- **MCP Client**: The AI Agents act as clients, connecting to the server using **SSE (Server-Sent Events)**.

### **Why MCP?**
- **Decoupling**: Tools are separated from the agent logic.
- **Standardization**: Provides a unified interface for tool discovery and execution.
- **Scalability**: The server can be deployed independently or scaled separately.


---

## 📂 File Upload & Data Flow

Understanding how your data moves from upload to query execution:

### **1. File Upload**
🟢 **Step 1: Uploading the File**
- You upload an Excel or CSV file using the web interface.
- The system accepts only valid file types: `.csv`, `.xlsx`, `.xls`.
- Duplicate files are automatically detected and avoided.

👉 **Goal:** Safely accept your data.

### **2. Storage**
🟢 **Step 2: Saving the File**
- The uploaded file is stored securely in the `uploads/` folder.
- Each file is renamed using a unique ID (UUID) to avoid conflicts.
- File details like:
  - Original file name
  - Upload time
  - File hash
  are saved separately in the `metadata/` folder.

👉 **Goal:** Keep files organized and traceable.

### **3. Schema Extraction**
🟢 **Step 3: Creating the Schema**
- The system reads the uploaded file to understand:
  - Column names
  - Data types (text, number, date, etc.)
- A schema (structure of the data) is generated in JSON format.
- This schema is saved in the `schemas/` folder.

👉 **Goal:** Help the AI understand your data correctly.

### **4. Database Ingestion**
🟢 **Step 4: Storing Data in the Database**
- The file’s data is loaded using Pandas.
- All rows are inserted into a persistent SQLite database (`database/chatbot.db`).
- This database is optimized for fast and reliable SQL queries.

👉 **Goal:** Make your data easy and fast to query.

### **5. Query Execution**
🟢 **Step 5: Asking Questions**
- When you ask a question in natural language:
  - The AI uses the stored schema to understand your data.
  - A safe SQL query is generated.
  - The query is executed on the SQLite database.
  - Results are returned to you in a clear and user-friendly format.

👉 **Goal:** Get instant answers from your uploaded data.

---

## 🚀 Setup & Installation
Follow the steps below to set up and run the SQL ChatBot locally.

### **Prerequisites**
Make sure the following are installed on your system:
- Python 3.8+
- Node.js 14+ (for Angular frontend)
- One of the following API providers:
- Google Gemini API Key (via Google ADK), or
- Azure OpenAI API Key

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

### **Step 5: Set Up API Key**

Create a `.env` file in the project root:
✅ Option 1: Google Gemini (Google ADK)
```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL=gemini-2.0-flash-exp
```
✅ Option 2: Azure OpenAI
```env
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here
AZURE_OPENAI_API_VERSION=your_api_version_here
MODEL=your_azure_openai_model_name

```


### **Step 6: Run MCP Server**
The MCP server must be running to allow AI agents to access tools such as schema retrieval and SQL execution.
```bash
python -m src.app.mcp.server.mcp_server
```
MCP Server will start at: `http://localhost:8001`

### **Step 7: Start the Backend (FastAPI) Server**
Open a new terminal, activate the virtual environment again, and run:
```bash
# Using Python module
python -m src.app.main_fastapi

# Or using uvicorn directly
uvicorn src.app.main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

Backend will start at: `http://localhost:8000`

### **Step 8: Run Frontend **
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
- **Model Context Protocol (MCP)** - Standardized tool interface
- **FastMCP** - Framework for building MCP servers
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
│   │   ├── mcp/              # MCP Implementation
│   │   │   ├── server/       # MCP Server & Toolset
│   │   │   │   ├── mcp_server.py
│   │   │   │   └── mcp_toolset.py
│   │   │   └── tools/        # Actual Tool Implementations
│   │   │       ├── get_schema.py
│   │   │       └── execute_sql.py
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


