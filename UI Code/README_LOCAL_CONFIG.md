# UI Code - Local Report Generation Configuration

This directory contains the web interface for the Smart Pharma Copilot system, now configured to use the local report generation API at `http://localhost:8001`.

## Recent Changes

### ✅ Updated Report Generation Endpoint
- **Before**: Used external endpoint `http://165.22.211.17:8001`
- **After**: Now uses local endpoint `http://localhost:8001`

### Modified Files:
1. `server.js` - Main server configuration updated
2. `server_fixed.js` - Alternative server configuration updated
3. `package.json` - Added test script for local API

### New Files:
1. `test_local_report_api.js` - Script to test local report API
2. `start_local_report_api.bat` - Windows batch file to start report API
3. `start_local_report_api.ps1` - PowerShell script to start report API

## Quick Start

### 1. Start the Local Report Generation API
Before starting the UI, make sure the report generation API is running locally:

**Option A: Using PowerShell**
```powershell
.\start_local_report_api.ps1
```

**Option B: Using Command Prompt**
```batch
start_local_report_api.bat
```

**Option C: Manual Start**
```batch
cd "..\Report Generation"
python run_report_system.py
```

### 2. Test the Local Report API
```bash
npm run test-local-report-api
```

### 3. Start the UI Server
```bash
npm start
```

### 4. Start Development Environment
```bash
npm run dev
```

## API Endpoints

The UI now connects to these local endpoints:

### Report Generation API (localhost:8001)
- **Health**: `GET /api/reports/health`
- **Types**: `GET /api/reports/types`
- **Generate**: `POST /api/reports/generate`
- **Download PDF**: `POST /api/reports/download-pdf`

### Prediction API (unchanged)
- Still uses configured prediction API endpoints

## Troubleshooting

### Report Generation Not Working?

1. **Check if local API is running:**
   ```bash
   npm run test-local-report-api
   ```

2. **Verify the Report Generation service is started:**
   ```bash
   cd "..\Report Generation"
   python run_report_system.py
   ```

3. **Check for port conflicts:**
   - Make sure nothing else is using port 8001
   - Use `netstat -an | findstr :8001` to check

4. **Verify Python dependencies:**
   ```bash
   cd "..\Report Generation"
   pip install -r requirements.txt
   ```

### Common Error Messages

- **"Connection refused"**: Report API is not running on port 8001
- **"Timeout"**: Report API is slow to respond or overloaded
- **"404 Not Found"**: Incorrect API endpoint configuration

## Configuration

### Environment Variables (Optional)
You can override the default localhost configuration:

```bash
# Set custom report API URL
set REPORT_API_URL=http://localhost:8001

# Set custom report API port
set REPORT_API_PORT=8001
```

### Server Configuration
The main configuration is in:
- `server.js` (lines 10-11)
- `server_fixed.js` (lines 10-11)

Current setting:
```javascript
const REPORT_API_URL = process.env.REPORT_API_URL || `http://localhost:8001`;
```

## Development Workflow

1. **Start Report API**: `.\start_local_report_api.ps1`
2. **Test API**: `npm run test-local-report-api`
3. **Start UI**: `npm run dev`
4. **Access Dashboard**: `http://localhost:3000`

## Production Deployment

For production deployment, ensure:
1. Report Generation API is accessible at the configured URL
2. All required Python dependencies are installed
3. Firewall allows connections to port 8001
4. Environment variables are properly set

## Support

If you encounter issues:
1. Check the console logs in both the UI server and Report Generation API
2. Verify all dependencies are installed
3. Ensure port 8001 is available and not blocked
4. Test the API endpoints directly using the test script

## File Structure

```
UI Code/
├── server.js                    # Main UI server (updated)
├── server_fixed.js             # Alternative server config (updated)
├── package.json                # Added test script
├── test_local_report_api.js    # API testing script (new)
├── start_local_report_api.bat  # Windows start script (new)
├── start_local_report_api.ps1  # PowerShell start script (new)
├── README_LOCAL_CONFIG.md      # This file (new)
└── client/                     # React application (unchanged)
    └── src/
        └── components/
            └── ReportsView.js  # Uses relative API paths (no changes needed)
```

---

**Status**: ✅ UI Code successfully configured to use local report generation API at `http://localhost:8001`
