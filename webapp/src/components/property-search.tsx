"use client";

import { useState, useEffect } from "react";
import { Search, Filter, MapPin, Bed, Bath, Square, DollarSign, Heart, MessageSquare } from "lucide-react";

interface Property {
  zpid: string;
  address: string;
  city: string;
  state: string;
  price: number;
  beds: number;
  baths: number;
  homeSizeSqft: number;
  isWaterfront: boolean;
  waterfrontFootage?: string;
  mainPhoto?: {
    mainUrl: string;
    caption?: string;
  };
  hasWaterfrontAnalysis: boolean;
  waterfrontLength?: number;
  hasBoatDock?: boolean;
  hasBoatLift?: boolean;
  hasBoatRamp?: boolean;
  hasMarinaAccess?: boolean;
  photoCount: number;
  commentCount: number;
  favoriteCount: number;
}

interface SearchResponse {
  success: boolean;
  data: {
    properties: Property[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      totalPages: number;
      hasNext: boolean;
      hasPrev: boolean;
    };
    summary: {
      totalProperties: number;
      propertiesWithAnalysis: number;
      waterfrontProperties: number;
    };
  };
}

export function PropertySearch() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    minPrice: "",
    maxPrice: "",
    minBeds: "",
    minBaths: "",
    waterfront: "all",
    city: "",
    state: "",
  });

  const [showFilters, setShowFilters] = useState(false);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false,
  });

  const performSearch = async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        ...(searchTerm && { search: searchTerm }),
        ...(filters.minPrice && { minPrice: filters.minPrice }),
        ...(filters.maxPrice && { maxPrice: filters.maxPrice }),
        ...(filters.minBeds && { minBeds: filters.minBeds }),
        ...(filters.minBaths && { minBaths: filters.minBaths }),
        ...(filters.waterfront !== 'all' && { waterfront: filters.waterfront }),
        ...(filters.city && { city: filters.city }),
        ...(filters.state && { state: filters.state }),
      });

      const response = await fetch(`/api/properties?${params}`);
      const data: SearchResponse = await response.json();

      if (data.success) {
        setProperties(data.data.properties);
        setPagination(data.data.pagination);
        setSearchPerformed(true);
      } else {
        console.error('Search failed:', data);
        setProperties([]);
      }
    } catch (error) {
      console.error('Error performing search:', error);
      setProperties([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 }));
    performSearch(1);
  };

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
    performSearch(newPage);
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      minPrice: "",
      maxPrice: "",
      minBeds: "",
      minBaths: "",
      waterfront: "all",
      city: "",
      state: "",
    });
  };

  const applyFilters = () => {
    setShowFilters(false);
    handleSearch();
  };

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Search by address, city, or ZPID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSearch()}
          className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Filters Toggle */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Filter className="h-4 w-4" />
          <span>Filters</span>
        </button>

        {searchPerformed && (
          <div className="text-sm text-gray-600">
            Showing <span className="font-medium">{properties.length}</span> of <span className="font-medium">{pagination.total}</span> properties
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Search Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Price Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Price Range
              </label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.minPrice}
                  onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.maxPrice}
                  onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Beds & Baths */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bedrooms
              </label>
              <select
                value={filters.minBeds}
                onChange={(e) => handleFilterChange('minBeds', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Any</option>
                <option value="1">1+</option>
                <option value="2">2+</option>
                <option value="3">3+</option>
                <option value="4">4+</option>
                <option value="5">5+</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bathrooms
              </label>
              <select
                value={filters.minBaths}
                onChange={(e) => handleFilterChange('minBaths', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Any</option>
                <option value="1">1+</option>
                <option value="2">2+</option>
                <option value="3">3+</option>
                <option value="4">4+</option>
              </select>
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                City
              </label>
              <input
                type="text"
                placeholder="Enter city"
                value={filters.city}
                onChange={(e) => handleFilterChange('city', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Waterfront Filter */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Waterfront Status
            </label>
            <select
              value={filters.waterfront}
              onChange={(e) => handleFilterChange('waterfront', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Properties</option>
              <option value="waterfront">Waterfront Only</option>
              <option value="non-waterfront">Non-Waterfront Only</option>
              <option value="with-analysis">With Waterfront Analysis</option>
            </select>
            <p className="mt-1 text-xs text-gray-600">
              "With Waterfront Analysis" shows properties that have detailed measurements like dock info, waterfront footage, etc.
            </p>
          </div>

          {/* Filter Actions */}
          <div className="mt-6 flex space-x-3">
            <button
              onClick={clearFilters}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Clear Filters
            </button>
            <button
              onClick={applyFilters}
              className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchPerformed && (
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Searching properties...</p>
            </div>
          ) : properties.length > 0 ? (
            <>
              {/* Properties List */}
              <div className="space-y-4">
                {properties.map((property) => (
                  <div key={property.zpid} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                    <div className="flex space-x-4">
                      <div className="flex-shrink-0">
                        {property.mainPhoto ? (
                          <img
                            src={property.mainPhoto.mainUrl}
                            alt={property.mainPhoto.caption || property.address}
                            className="w-32 h-24 rounded-lg object-cover"
                          />
                        ) : (
                          <div className="w-32 h-24 bg-gray-200 rounded-lg flex items-center justify-center">
                            <span className="text-gray-500 text-sm">No Photo</span>
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-lg font-medium text-gray-900">
                              <a href={`/property/${property.zpid}`} className="hover:text-blue-600">
                                {property.address}
                              </a>
                            </h3>
                            <p className="text-sm text-gray-600 flex items-center">
                              <MapPin className="w-4 h-4 mr-1" />
                              {property.city}, {property.state}
                            </p>
                            <div className="mt-2 flex items-center space-x-6 text-sm text-gray-600">
                              <div className="flex items-center">
                                <Bed className="w-4 h-4 mr-1" />
                                {property.beds || 'N/A'} beds
                              </div>
                              <div className="flex items-center">
                                <Bath className="w-4 h-4 mr-1" />
                                {property.baths || 'N/A'} baths
                              </div>
                              <div className="flex items-center">
                                <Square className="w-4 h-4 mr-1" />
                                {property.homeSizeSqft ? `${property.homeSizeSqft.toLocaleString()} sqft` : 'N/A'}
                              </div>
                              {property.waterfrontFootage && (
                                <div className="flex items-center">
                                  <MapPin className="w-4 h-4 mr-1" />
                                  {property.waterfrontFootage}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-xl font-bold text-gray-900">
                              {property.price ? `$${property.price.toLocaleString()}` : 'Price on request'}
                            </p>
                            <div className="flex flex-col space-y-1 mt-2">
                              {property.isWaterfront && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  Waterfront
                                </span>
                              )}
                              {property.hasWaterfrontAnalysis && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Has Analysis
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Waterfront Analysis Info */}
                        {property.hasWaterfrontAnalysis && (
                          <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                            <h4 className="text-sm font-medium text-blue-900 mb-2">Waterfront Analysis Available</h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                              {property.waterfrontLength && (
                                <div className="text-blue-700">
                                  <span className="font-medium">Length:</span> {property.waterfrontLength} ft
                                </div>
                              )}
                              {property.hasBoatDock && (
                                <div className="text-blue-700">
                                  <span className="font-medium">Boat Dock:</span> Yes
                                </div>
                              )}
                              {property.hasBoatLift && (
                                <div className="text-blue-700">
                                  <span className="font-medium">Boat Lift:</span> Yes
                                </div>
                              )}
                              {property.hasMarinaAccess && (
                                <div className="text-blue-700">
                                  <span className="font-medium">Marina Access:</span> Yes
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Property Stats */}
                        <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                          <div className="flex items-center">
                            <span className="mr-1">📸</span>
                            {property.photoCount} photos
                          </div>
                          <div className="flex items-center">
                            <MessageSquare className="w-4 h-4 mr-1" />
                            {property.commentCount} comments
                          </div>
                          <div className="flex items-center">
                            <Heart className="w-4 h-4 mr-1" />
                            {property.favoriteCount} favorites
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {pagination.totalPages > 1 && (
                <div className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-6 py-4">
                  <div className="text-sm text-gray-700">
                    Page {pagination.page} of {pagination.totalPages}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handlePageChange(pagination.page - 1)}
                      disabled={!pagination.hasPrev}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => handlePageChange(pagination.page + 1)}
                      disabled={!pagination.hasNext}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
              <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No properties found</h3>
              <p className="text-gray-600 mb-4">
                Try adjusting your search criteria or filters
              </p>
              <button
                onClick={() => {
                  setSearchTerm("");
                  clearFilters();
                  setSearchPerformed(false);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
              >
                Clear Search
              </button>
            </div>
          )}
        </div>
      )}

      {/* Initial State */}
      {!searchPerformed && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Search All Properties</h3>
          <p className="text-gray-600 mb-4">
            Search through your complete property database - including waterfront and non-waterfront properties
          </p>
          <div className="text-sm text-gray-500 space-y-1">
            <p>• Search by address, city, or ZPID</p>
            <p>• Filter by price, beds, baths, and waterfront status</p>
            <p>• View all properties, not just those with waterfront analysis</p>
          </div>
        </div>
      )}
    </div>
  );
}
