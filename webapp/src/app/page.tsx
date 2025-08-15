import { Suspense } from "react";
import { DashboardStats } from "@/components/dashboard-stats";
import { RecentProperties } from "@/components/recent-properties";
import { QuickActions } from "@/components/quick-actions";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Waterfront Properties Dashboard
        </h1>
        <p className="mt-2 text-gray-600">
          Manage and explore your waterfront property database
        </p>
      </div>

      <Suspense fallback={<div>Loading stats...</div>}>
        <DashboardStats />
      </Suspense>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Suspense fallback={<div>Loading recent properties...</div>}>
            <RecentProperties />
          </Suspense>
        </div>
        <div>
          <QuickActions />
        </div>
      </div>
    </div>
  );
}
