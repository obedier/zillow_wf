"use client";

import Link from "next/link";
import { MapPin, Bed, Bath, Square, DollarSign } from "lucide-react";

// Mock data - will be replaced with real database queries
const recentProperties = [
  {
    zpid: "103014903",
    address: "1234 Waterfront Dr",
    city: "Fort Lauderdale",
    state: "FL",
    price: 2500000,
    beds: 4,
    baths: 3,
    homeSizeSqft: 3200,
    isWaterfront: true,
    waterfrontFootage: "150 ft",
    imageUrl: "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop",
  },
  {
    zpid: "103022783",
    address: "5678 Marina Way",
    city: "Miami",
    state: "FL",
    price: 1800000,
    beds: 3,
    baths: 2,
    homeSizeSqft: 2400,
    isWaterfront: true,
    waterfrontFootage: "100 ft",
    imageUrl: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=400&h=300&fit=crop",
  },
  {
    zpid: "103028843",
    address: "9012 Ocean Blvd",
    city: "Palm Beach",
    state: "FL",
    price: 4200000,
    beds: 5,
    baths: 4,
    homeSizeSqft: 4800,
    isWaterfront: true,
    waterfrontFootage: "200 ft",
    imageUrl: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop",
  },
];

export function RecentProperties() {
  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Recent Properties</h2>
        <p className="text-sm text-gray-600">Recently added waterfront properties</p>
      </div>
      <div className="divide-y divide-gray-200">
        {recentProperties.map((property) => (
          <div key={property.zpid} className="p-6 hover:bg-gray-50 transition-colors">
            <div className="flex space-x-4">
              <div className="flex-shrink-0">
                <img
                  src={property.imageUrl}
                  alt={property.address}
                  className="w-24 h-24 rounded-lg object-cover"
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      <Link href={`/property/${property.zpid}`} className="hover:text-blue-600">
                        {property.address}
                      </Link>
                    </h3>
                    <p className="text-sm text-gray-600 flex items-center">
                      <MapPin className="w-4 h-4 mr-1" />
                      {property.city}, {property.state}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-gray-900">
                      ${property.price.toLocaleString()}
                    </p>
                    {property.isWaterfront && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Waterfront
                      </span>
                    )}
                  </div>
                </div>
                <div className="mt-3 flex items-center space-x-6 text-sm text-gray-600">
                  <div className="flex items-center">
                    <Bed className="w-4 h-4 mr-1" />
                    {property.beds} beds
                  </div>
                  <div className="flex items-center">
                    <Bath className="w-4 h-4 mr-1" />
                    {property.baths} baths
                  </div>
                  <div className="flex items-center">
                    <Square className="w-4 h-4 mr-1" />
                    {property.homeSizeSqft.toLocaleString()} sqft
                  </div>
                  {property.waterfrontFootage && (
                    <div className="flex items-center">
                      <MapPin className="w-4 h-4 mr-1" />
                      {property.waterfrontFootage}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="px-6 py-4 border-t border-gray-200">
        <Link
          href="/search"
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          View all properties →
        </Link>
      </div>
    </div>
  );
}
