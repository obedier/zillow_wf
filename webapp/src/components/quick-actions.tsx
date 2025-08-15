"use client";

import Link from "next/link";
import { Search, Plus, Heart, Bot, Database } from "lucide-react";

const actions = [
  {
    name: "Search Properties",
    description: "Find properties by location, price, or features",
    href: "/search",
    icon: Search,
    color: "bg-blue-500 hover:bg-blue-600",
  },
  {
    name: "Add New URLs",
    description: "Extract properties from Zillow search URLs",
    href: "/extraction",
    icon: Plus,
    color: "bg-green-500 hover:bg-green-600",
  },
  {
    name: "View Favorites",
    description: "See your saved favorite properties",
    href: "/favorites",
    icon: Heart,
    color: "bg-red-500 hover:bg-red-600",
  },
  {
    name: "AI Agent",
    description: "Ask questions about your property database",
    href: "/ai-agent",
    icon: Bot,
    color: "bg-purple-500 hover:bg-purple-600",
  },
  {
    name: "Database Stats",
    description: "View detailed database analytics",
    href: "/stats",
    icon: Database,
    color: "bg-indigo-500 hover:bg-indigo-600",
  },
];

export function QuickActions() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
      <div className="space-y-3">
        {actions.map((action) => (
          <Link
            key={action.name}
            href={action.href}
            className="block p-4 rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all"
          >
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${action.color} text-white`}>
                <action.icon className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{action.name}</h3>
                <p className="text-sm text-gray-600">{action.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
