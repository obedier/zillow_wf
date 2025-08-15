#!/usr/bin/env python3
"""
Extraction Runner Script for Zillow Waterfront Web App
This script bridges the web app with the existing Python extraction system.
"""

import os
import sys
import json
import asyncio
import psycopg
from datetime import datetime
from typing import Dict, List, Any
import subprocess
import logging

# Add the parent directory to the path to import the extraction modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'zillow_wf'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExtractionRunner:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.cur = None
    
    async def connect(self):
        """Establish database connection"""
        try:
            self.conn = await psycopg.AsyncConnection.connect(self.database_url)
            self.cur = await self.conn.cursor()
            logger.info("✅ Connected to database successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    async def disconnect(self):
        """Close database connection"""
        if self.cur:
            await self.cur.close()
        if self.conn:
            await self.conn.close()
        logger.info("🔌 Database connection closed")
    
    async def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """Get all pending extraction jobs"""
        try:
            await self.cur.execute("""
                SELECT id, urls, total_urls, status, progress, processed_urls, error_count
                FROM extraction_jobs 
                WHERE status IN ('pending', 'running')
                ORDER BY created_at ASC
            """)
            jobs = await self.cur.fetchall()
            
            return [
                {
                    'id': job[0],
                    'urls': job[1],
                    'total_urls': job[2],
                    'status': job[3],
                    'progress': job[4],
                    'processed_urls': job[5],
                    'error_count': job[6]
                }
                for job in jobs
            ]
        except Exception as e:
            logger.error(f"Error fetching pending jobs: {e}")
            return []
    
    async def update_job_status(self, job_id: int, status: str, progress: int = None, 
                               processed_urls: int = None, error_count: int = None):
        """Update job status and progress"""
        try:
            update_fields = ["status = %s", "updated_at = %s"]
            update_values = [status, datetime.now()]
            
            if progress is not None:
                update_fields.append("progress = %s")
                update_values.append(progress)
            
            if processed_urls is not None:
                update_fields.append("processed_urls = %s")
                update_values.append(processed_urls)
            
            if error_count is not None:
                update_fields.append("error_count = %s")
                update_values.append(error_count)
            
            if status == 'running' and 'started_at = %s' not in update_fields:
                update_fields.append("started_at = %s")
                update_values.append(datetime.now())
            
            if status in ['completed', 'failed'] and 'completed_at = %s' not in update_fields:
                update_fields.append("completed_at = %s")
                update_values.append(datetime.now())
            
            query = f"""
                UPDATE extraction_jobs 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            update_values.append(job_id)
            
            await self.cur.execute(query, update_values)
            await self.conn.commit()
            
            logger.info(f"Updated job {job_id}: status={status}, progress={progress}")
            
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            await self.conn.rollback()
    
    async def run_extraction_job(self, job: Dict[str, Any]):
        """Run a single extraction job using the existing extraction system"""
        job_id = job['id']
        urls = job['urls']
        total_urls = job['total_urls']
        
        try:
            logger.info(f"🚀 Starting extraction job {job_id} with {total_urls} URLs")
            
            # Update job status to running
            await self.update_job_status(job_id, 'running', 0, 0, 0)
            
            # Create a temporary URLs file for the extraction script
            urls_file = f"/tmp/extraction_job_{job_id}_urls.txt"
            with open(urls_file, 'w') as f:
                for url in urls:
                    f.write(f"{url}\n")
            
            # Run the extraction script
            extraction_script = os.path.join(
                os.path.dirname(__file__), '..', '..', 'zillow_wf', 
                'flexible_waterfront_extractor.py'
            )
            
            if not os.path.exists(extraction_script):
                logger.error(f"Extraction script not found: {extraction_script}")
                await self.update_job_status(job_id, 'failed', 0, 0, total_urls)
                return
            
            # Build the command to run the extraction
            cmd = [
                sys.executable,  # Use current Python interpreter
                extraction_script,
                '--mode', 'urls',
                '--continue', urls_file,
                '--enable-db-storage',
                '--simple',
                '--max-concurrent-properties', '5',
                '--timeout', '60'
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            # Start the extraction process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor the process and update progress
            processed_urls = 0
            error_count = 0
            
            while True:
                # Check if process is still running
                if process.returncode is not None:
                    break
                
                # Update progress every 10 seconds
                await asyncio.sleep(10)
                
                # Simulate progress updates (in real implementation, parse output)
                processed_urls = min(processed_urls + 2, total_urls)
                progress = int((processed_urls / total_urls) * 100)
                
                await self.update_job_status(
                    job_id, 'running', progress, processed_urls, error_count
                )
            
            # Get the final result
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Extraction job {job_id} completed successfully")
                await self.update_job_status(
                    job_id, 'completed', 100, total_urls, error_count
                )
            else:
                logger.error(f"❌ Extraction job {job_id} failed with return code {process.returncode}")
                logger.error(f"Stderr: {stderr.decode()}")
                await self.update_job_status(
                    job_id, 'failed', progress, processed_urls, total_urls
                )
            
            # Clean up temporary file
            if os.path.exists(urls_file):
                os.remove(urls_file)
                
        except Exception as e:
            logger.error(f"Error running extraction job {job_id}: {e}")
            await self.update_job_status(job_id, 'failed', 0, 0, total_urls)
    
    async def run_all_pending_jobs(self):
        """Run all pending extraction jobs"""
        if not await self.connect():
            return
        
        try:
            while True:
                # Get pending jobs
                pending_jobs = await self.get_pending_jobs()
                
                if not pending_jobs:
                    logger.info("No pending jobs, waiting...")
                    await asyncio.sleep(30)  # Wait 30 seconds before checking again
                    continue
                
                logger.info(f"Found {len(pending_jobs)} pending jobs")
                
                # Process jobs sequentially (can be made concurrent if needed)
                for job in pending_jobs:
                    if job['status'] == 'pending':
                        await self.run_extraction_job(job)
                    elif job['status'] == 'running':
                        # Check if job is stuck (running for too long)
                        # This is a simple implementation - can be enhanced
                        logger.info(f"Job {job['id']} is already running")
                
                await asyncio.sleep(10)  # Wait before checking for new jobs
                
        except KeyboardInterrupt:
            logger.info("Shutting down extraction runner...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.disconnect()

async def main():
    """Main function"""
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/zillow_wf')
    
    if 'username:password' in database_url:
        logger.error("Please set DATABASE_URL environment variable with your actual database credentials")
        return
    
    runner = ExtractionRunner(database_url)
    await runner.run_all_pending_jobs()

if __name__ == "__main__":
    asyncio.run(main())
