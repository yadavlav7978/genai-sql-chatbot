### 1. Create a virtual environment
```bash
python -m venv venv

```

### 2. Activate virtual environment and run
```bash
   venv\Scripts\Activate
```   

### 3. Set up Google API credentials:

You need to configure Google API authentication. Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

Or set the environment variable:
```bash
$env:GOOGLE_API_KEY="your_google_api_key_here"
```

### 4. Run the application:

```bash
python.exe -m src.app.main
```
