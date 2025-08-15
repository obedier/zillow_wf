"use client";

import { Home, MapPin, DollarSign, TrendingUp } from "lucide-react";

const stats = [
  {
    name: "Total Properties",
    value: "1,200+",
    change: "+45",
    changeType: "increase",
    icon: Home,
  },
  {
    name: "Waterfront Properties",
    value: "580+",
    change: "+23",
    changeType: "increase",
    icon: MapPin,
  },
  {
    name: "Properties with Analysis",
    value: "634",
    change: "+12",
    changeType: "increase",
    icon: TrendingUp,
  },
  {
    name: "Properties Added",
    value: "67",
    change: "This week",
    changeType: "neutral",
    icon: TrendingUp,
  },
];

export function DashboardStats() {
  return (
    <div>
      <h2 className="text-lg font-medium text-gray-900 mb-4">Database Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4 w-full">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                <div className="flex items-center mt-1">
                  {stat.changeType === "increase" && (
                    <span className="text-green-600 text-sm font-medium">
                      {stat.change}
                    </span>
                  )}
                  {stat.changeType === "decrease" && (
                    <span className="text-red-600 text-sm font-medium">
                      {stat.change}
                    </span>
                  )}
                  {stat.changeType === "neutral" && (
                    <span className="text-gray-500 text-sm">
                      {stat.change}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Explanation */}
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> The "Properties with Analysis" count represents properties that have detailed waterfront measurements and analysis data. 
          All properties are searchable and viewable, but waterfront analysis data is only available for properties where we were able to extract 
          detailed measurements (dock info, waterfront footage, water depth, etc.).
        </p>
      </div>
    </div>
  );
}
