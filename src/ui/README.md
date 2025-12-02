# SQL ChatBot - Angular Frontend

Modern, responsive Angular frontend for the SQL ChatBot application.

## Features

- ✅ ChatGPT-like interface with sidebar and chat window
- ✅ Excel file upload (.xlsx, .xls, .csv)
- ✅ Real-time chat with SQL chatbot
- ✅ Message bubbles for user and bot
- ✅ SQL query display
- ✅ Query results table
- ✅ Loading animations
- ✅ Error handling
- ✅ Responsive design

## Setup

### Install Dependencies

```bash
cd src/ui
npm install
```

### Development Server

```bash
npm start
```

The application will be available at `http://localhost:4200`

### Build for Production

```bash
npm run build
```

## Project Structure

```
src/ui/
├── src/
│   ├── app/
│   │   ├── components/
│   │   │   └── chat/
│   │   │       ├── chat.component.ts
│   │   │       ├── chat.component.html
│   │   │       └── chat.component.css
│   │   ├── services/
│   │   │   └── chat.service.ts
│   │   ├── app.component.ts
│   │   └── app.routes.ts
│   ├── index.html
│   ├── main.ts
│   └── styles.css
├── package.json
├── angular.json
└── tsconfig.json
```

## API Endpoints

The frontend connects to the FastAPI backend at `http://localhost:8000`:

- `POST /api/upload-file` - Upload Excel/CSV file
- `POST /api/chat` - Send chat message
- `GET /api/health` - Health check

## Usage

1. Start the FastAPI backend:
   ```bash
   python -m uvicorn src.app.main_fastapi:app --reload --port 8000
   ```

2. Start the Angular frontend:
   ```bash
   cd src/ui
   npm start
   ```

3. Open `http://localhost:4200` in your browser

4. Upload an Excel file using the upload button

5. Start chatting with the SQL chatbot!

