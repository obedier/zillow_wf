# Extraction System Integration

This directory contains the integration between the Next.js web app and your existing Python extraction system.

## Overview

The extraction system allows users to:
1. Submit Zillow search URLs through the web interface
2. Monitor extraction job progress in real-time
3. View completed extractions and results
4. Manage and delete extraction jobs

## Files

### `extraction_runner.py`
The main Python script that:
- Connects to the PostgreSQL database
- Monitors for new extraction jobs
- Executes your existing `flexible_waterfront_extractor.py` script
- Updates job status and progress in real-time
- Handles job lifecycle management

### `start_extraction_runner.sh`
A bash script to start the extraction runner with proper environment setup.

## How It Works

### 1. Job Creation
1. User submits URLs through the web interface (`/api/extraction` POST endpoint)
2. Job is created in the `extraction_jobs` table with status "pending"
3. Extraction runner detects the new job

### 2. Job Execution
1. Extraction runner updates job status to "running"
2. Creates a temporary URLs file
3. Executes your existing extraction script with appropriate parameters
4. Monitors progress and updates the database

### 3. Job Completion
1. Job status is updated to "completed" or "failed"
2. Results are stored in your existing database tables
3. Web interface shows updated job status

## Setup Instructions

### 1. Environment Variables
Set your database connection string:
```bash
export DATABASE_URL="postgresql://youruser:yourpass@localhost:5432/zillow_wf"
```

### 2. Install Dependencies
The extraction runner requires:
```bash
pip install psycopg
```

### 3. Start the Runner
```bash
# From the webapp directory
./scripts/start_extraction_runner.sh

# Or manually
python3 scripts/extraction_runner.py
```

## Integration with Your Existing System

### Script Location
The extraction runner expects to find your `flexible_waterfront_extractor.py` script at:
```
webapp/../zillow_wf/flexible_waterfront_extractor.py
```

### Command Parameters
The runner executes your script with these parameters:
```bash
python3 flexible_waterfront_extractor.py \
  --mode urls \
  --continue /tmp/extraction_job_{ID}_urls.txt \
  --enable-db-storage \
  --simple \
  --max-concurrent-properties 5 \
  --timeout 60
```

### Database Integration
- Uses your existing database schema
- New properties are stored in `listings_summary`, `listings_detail`, etc.
- Waterfront analysis data goes to `wf_data` table
- Job tracking uses the new `extraction_jobs` table

## Monitoring and Logging

### Log Files
- `extraction_runner.log` - Main runner logs
- Your existing extraction script logs

### Real-time Updates
- Web interface polls job status every 5 seconds
- Progress bars show real-time completion
- Job history is preserved in the database

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL environment variable
   - Verify PostgreSQL is running
   - Check database credentials

2. **Extraction Script Not Found**
   - Ensure `flexible_waterfront_extractor.py` exists in the expected location
   - Check file permissions

3. **Jobs Not Starting**
   - Check extraction runner logs
   - Verify the runner is connected to the database
   - Check for Python errors

### Debug Mode
To enable debug logging, modify the logging level in `extraction_runner.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Performance Considerations

### Concurrent Jobs
- Currently processes one job at a time
- Can be modified to handle multiple concurrent jobs
- Consider your server's resources and database connection limits

### Timeout Settings
- Default timeout: 60 seconds per property
- Adjust based on your extraction script's performance
- Consider network latency and Zillow's response times

### Database Connections
- Uses connection pooling for efficiency
- Properly closes connections to prevent leaks
- Monitors connection health

## Security Notes

### URL Validation
- URLs are stored as-is from user input
- Consider adding URL validation if needed
- Sanitize URLs before passing to extraction script

### Database Access
- Runner needs full database access
- Consider creating a dedicated database user
- Limit permissions to necessary tables only

## Future Enhancements

### Planned Features
1. **Job Scheduling** - Run extractions at specific times
2. **Batch Processing** - Group multiple jobs together
3. **Error Recovery** - Automatic retry for failed extractions
4. **Resource Monitoring** - Track CPU/memory usage
5. **Email Notifications** - Alert when jobs complete/fail

### Integration Points
1. **User Authentication** - Link jobs to specific users
2. **Rate Limiting** - Prevent abuse of the system
3. **API Keys** - Secure access to extraction endpoints
4. **Audit Logging** - Track all extraction activities

## Support

For issues with the extraction system:
1. Check the logs in `extraction_runner.log`
2. Verify database connectivity
3. Test your extraction script manually
4. Check the web interface for error messages

The extraction system is designed to be robust and self-healing, but manual intervention may be needed for complex issues.
