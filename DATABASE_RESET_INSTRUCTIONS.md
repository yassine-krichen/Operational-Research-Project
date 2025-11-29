# Fix for Database Schema Issue

## Problem

The SQLite database (`hospital_scheduler.db`) was created with the old schema before we added the `completed_at` column to the `ScheduleRun` model.

## Solution

### Step 1: Stop the Backend Server

Press `Ctrl+C` in the terminal where uvicorn is running to stop the server.

### Step 2: Delete Old Database

Once the server is stopped, run this command:

```powershell
cd c:\Users\user\Documents\SWE\INSAT\GL3\S1\recherche_operationelle\project\hospital_scheduler
Remove-Item hospital_scheduler.db -Force
```

### Step 3: Restart Backend Server

The database will be automatically recreated with the new schema when you start the server again:

```powershell
.\.venv\Scripts\activate
uvicorn app.main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 4: Test

-   Refresh frontend and try "Seed Demo Data" again
-   Then "Generate Schedule"
-   Should work without 500 errors!

## Why This Happens

SQLAlchemy creates the database on first run based on the model definitions. When we added the `completed_at` field to the model, the existing database didn't get updated automatically. Deleting the database forces SQLAlchemy to recreate it with all current model definitions.

## Verification

After deleting the database and restarting, you should see:

-   ✅ No "table runs has no column named completed_at" error
-   ✅ Schedule creation works (POST /api/schedules returns 200)
-   ✅ Polling updates work (GET /api/schedules/{run_id} returns 200)
