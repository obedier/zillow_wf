"use client";

import { useState } from "react";
import { Plus, Play, Pause, Trash2, Clock, CheckCircle, AlertCircle } from "lucide-react";

interface ExtractionJob {
  id: number;
  urls: string[];
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  totalUrls: number;
  processedUrls: number;
  errorCount: number;
  startedAt?: Date;
  completedAt?: Date;
  createdAt: Date;
}

export function ExtractionManager() {
  const [urls, setUrls] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [jobs, setJobs] = useState<ExtractionJob[]>([
    {
      id: 1,
      urls: ["https://www.zillow.com/homes/for_sale/?searchQueryState=..."],
      status: "completed",
      progress: 100,
      totalUrls: 45,
      processedUrls: 45,
      errorCount: 2,
      startedAt: new Date(Date.now() - 3600000),
      completedAt: new Date(Date.now() - 1800000),
      createdAt: new Date(Date.now() - 7200000),
    },
    {
      id: 2,
      urls: ["https://www.zillow.com/homes/for_sale/?searchQueryState=..."],
      status: "running",
      progress: 65,
      totalUrls: 120,
      processedUrls: 78,
      errorCount: 0,
      startedAt: new Date(Date.now() - 1800000),
      createdAt: new Date(Date.now() - 3600000),
    },
  ]);

  const handleStartExtraction = () => {
    if (!urls.trim()) return;

    const urlList = urls.split("\n").filter(url => url.trim());
    const newJob: ExtractionJob = {
      id: Date.now(),
      urls: urlList,
      status: "pending",
      progress: 0,
      totalUrls: urlList.length,
      processedUrls: 0,
      errorCount: 0,
      createdAt: new Date(),
    };

    setJobs([newJob, ...jobs]);
    setUrls("");
    setIsRunning(true);

    // Simulate job progression
    setTimeout(() => {
      setJobs(prev => prev.map(job => 
        job.id === newJob.id 
          ? { ...job, status: "running", startedAt: new Date() }
          : job
      ));
    }, 1000);
  };

  const handleStopJob = (jobId: number) => {
    setJobs(prev => prev.map(job => 
      job.id === jobId 
        ? { ...job, status: "failed", progress: job.progress }
        : job
    ));
    setIsRunning(false);
  };

  const handleDeleteJob = (jobId: number) => {
    setJobs(prev => prev.filter(job => job.id !== jobId));
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
              onClick={handleStartExtraction}
              disabled={!urls.trim() || isRunning}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus className="h-4 w-4 inline mr-2" />
              Start Extraction
            </button>
          </div>
        </div>
      </div>

      {/* Active Jobs */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Extraction Jobs</h3>
          <p className="text-sm text-gray-600">Monitor and manage your extraction jobs</p>
        </div>
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
                      {job.totalUrls} URLs • Created {job.createdAt.toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                    {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                  </span>
                  {job.status === "running" && (
                    <button
                      onClick={() => handleStopJob(job.id)}
                      className="p-1 text-red-600 hover:text-red-800"
                    >
                      <Pause className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteJob(job.id)}
                    className="p-1 text-gray-400 hover:text-red-600"
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
                    {job.startedAt ? job.startedAt.toLocaleTimeString() : "Pending"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
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
        </div>
      </div>
    </div>
  );
}
