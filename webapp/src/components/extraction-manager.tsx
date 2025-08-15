"use client";

import { useState, useEffect } from "react";
import { Plus, Play, Pause, Trash2, Clock, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";

interface ExtractionJob {
  id: number;
  urls: string[];
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  totalUrls: number;
  processedUrls: number;
  errorCount: number;
  startedAt?: string;
  completedAt?: string;
  createdAt: string;
}

export function ExtractionManager() {
  const [urls, setUrls] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [jobs, setJobs] = useState<ExtractionJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch jobs on component mount
  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/extraction');
      const data = await response.json();
      
      if (data.success) {
        setJobs(data.data.jobs);
      } else {
        console.error('Failed to fetch jobs:', data);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const startExtraction = async () => {
    if (!urls.trim()) return;

    const urlList = urls.split("\n").filter(url => url.trim());
    if (urlList.length === 0) return;

    setLoading(true);
    try {
      const response = await fetch('/api/extraction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          urls: urlList,
          userId: 'default' // Will be replaced with real user ID in Phase 3
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setUrls("");
        setIsRunning(true);
        // Refresh the jobs list
        await fetchJobs();
        
        // Start polling for updates
        startJobPolling(data.data.jobId);
      } else {
        console.error('Failed to start extraction:', data);
        alert('Failed to start extraction: ' + data.error);
      }
    } catch (error) {
      console.error('Error starting extraction:', error);
      alert('Error starting extraction. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const startJobPolling = (jobId: number) => {
    // Poll for job updates every 5 seconds
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/extraction/${jobId}`);
        const data = await response.json();
        
        if (data.success) {
          const updatedJob = data.data;
          
          // Update the job in the local state
          setJobs(prev => prev.map(job => 
            job.id === jobId ? updatedJob : job
          ));
          
          // Stop polling if job is completed or failed
          if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
            clearInterval(interval);
            setIsRunning(false);
          }
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    }, 5000);
  };

  const stopJob = async (jobId: number) => {
    try {
      const response = await fetch(`/api/extraction/${jobId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status: 'failed',
          progress: 0
        }),
      });

      if (response.ok) {
        await fetchJobs();
        setIsRunning(false);
      }
    } catch (error) {
      console.error('Error stopping job:', error);
    }
  };

  const deleteJob = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      const response = await fetch(`/api/extraction/${jobId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchJobs();
      }
    } catch (error) {
      console.error('Error deleting job:', error);
    }
  };

  const refreshJobs = async () => {
    setRefreshing(true);
    await fetchJobs();
    setRefreshing(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case "running":
        return <Play className="h-5 w-5 text-blue-500" />;
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "failed":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "running":
        return "bg-blue-100 text-blue-800";
      case "completed":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* New Extraction Form */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Start New Extraction</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Zillow Search URLs
            </label>
            <textarea
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
              placeholder="Enter Zillow search URLs (one per line)&#10;Example:&#10;https://www.zillow.com/homes/for_sale/?searchQueryState=..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {urls.split("\n").filter(url => url.trim()).length} URLs ready to process
            </p>
            <button
              onClick={startExtraction}
              disabled={!urls.trim() || loading || isRunning}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus className="h-4 w-4 inline mr-2" />
              {loading ? 'Starting...' : 'Start Extraction'}
            </button>
          </div>
        </div>
      </div>

      {/* Active Jobs */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Extraction Jobs</h3>
              <p className="text-sm text-gray-600">Monitor and manage your extraction jobs</p>
            </div>
            <button
              onClick={refreshJobs}
              disabled={refreshing}
              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
        
        {jobs.length === 0 ? (
          <div className="p-8 text-center">
            <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No extraction jobs yet</h3>
            <p className="text-gray-600">
              Start your first extraction by adding URLs above
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {jobs.map((job) => (
              <div key={job.id} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        Job #{job.id}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {job.totalUrls} URLs • Created {formatDate(job.createdAt)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                      {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                    </span>
                    {job.status === "running" && (
                      <button
                        onClick={() => stopJob(job.id)}
                        className="p-1 text-red-600 hover:text-red-800"
                        title="Stop job"
                      >
                        <Pause className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteJob(job.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                      title="Delete job"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                    <span>Progress</span>
                    <span>{job.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                </div>

                {/* Job Details */}
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Processed:</span>
                    <span className="ml-2 font-medium">{job.processedUrls}/{job.totalUrls}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Errors:</span>
                    <span className="ml-2 font-medium text-red-600">{job.errorCount}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Started:</span>
                    <span className="ml-2 font-medium">
                      {job.startedAt ? formatTime(job.startedAt) : "Pending"}
                    </span>
                  </div>
                </div>

                {/* URLs Preview */}
                <div className="mt-4">
                  <details className="text-sm">
                    <summary className="cursor-pointer text-gray-600 hover:text-gray-900">
                      Show URLs ({job.urls.length})
                    </summary>
                    <div className="mt-2 p-3 bg-gray-50 rounded-lg max-h-32 overflow-y-auto">
                      {job.urls.map((url, index) => (
                        <div key={index} className="text-xs text-gray-600 break-all">
                          {url}
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-2">How to Use</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p>1. Copy a Zillow search URL from your browser</p>
          <p>2. Paste it into the URL field above</p>
          <p>3. Click "Start Extraction" to begin processing</p>
          <p>4. Monitor progress in the jobs section below</p>
          <p>5. New properties will be automatically added to your database</p>
          <p className="mt-3 font-medium">Note: The extraction system runs your existing Python scripts in the background</p>
        </div>
      </div>
    </div>
  );
}
