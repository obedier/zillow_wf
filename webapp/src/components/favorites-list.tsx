"use client";

import { useState } from "react";
import { Heart, MapPin, Bed, Bath, Square, DollarSign, Trash2, MessageSquare } from "lucide-react";

// Mock data - will be replaced with real database queries
const favoriteProperties = [
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
    addedDate: "2025-01-15",
    notes: "Perfect location with deep water access",
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
    addedDate: "2025-01-12",
    notes: "Great investment potential",
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
    addedDate: "2025-01-10",
    notes: "Luxury waterfront estate",
  },
];

export function FavoritesList() {
  const [favorites, setFavorites] = useState(favoriteProperties);
  const [editingNote, setEditingNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");

  const handleRemoveFavorite = (zpid: string) => {
    setFavorites(prev => prev.filter(prop => prop.zpid !== zpid));
  };

  const handleEditNote = (zpid: string, currentNote: string) => {
    setEditingNote(zpid);
    setNoteText(currentNote);
  };

  const handleSaveNote = (zpid: string) => {
    setFavorites(prev => prev.map(prop => 
      prop.zpid === zpid ? { ...prop, notes: noteText } : prop
    ));
    setEditingNote(null);
    setNoteText("");
  };

  const handleCancelEdit = () => {
    setEditingNote(null);
    setNoteText("");
  };

  if (favorites.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
        <Heart className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No favorites yet</h3>
        <p className="text-gray-600 mb-6">
          Start building your collection of favorite waterfront properties
        </p>
        <div className="text-sm text-gray-500">
          Click the heart icon on any property to add it to your favorites
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <Heart className="h-8 w-8 text-red-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total Favorites</p>
              <p className="text-2xl font-bold text-gray-900">{favorites.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900">
                ${(favorites.reduce((sum, prop) => sum + prop.price, 0) / 1000000).toFixed(1)}M
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <MapPin className="h-8 w-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Cities</p>
              <p className="text-2xl font-bold text-gray-900">
                {new Set(favorites.map(prop => prop.city)).size}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <Square className="h-8 w-8 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Avg Size</p>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(favorites.reduce((sum, prop) => sum + prop.homeSizeSqft, 0) / favorites.length).toLocaleString()} sqft
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Favorites List */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Your Favorites</h2>
          <p className="text-sm text-gray-600">Manage your saved properties and add personal notes</p>
        </div>
        <div className="divide-y divide-gray-200">
          {favorites.map((property) => (
            <div key={property.zpid} className="p-6">
              <div className="flex space-x-4">
                <div className="flex-shrink-0">
                  <img
                    src={property.imageUrl}
                    alt={property.address}
                    className="w-32 h-24 rounded-lg object-cover"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">
                        {property.address}
                      </h3>
                      <p className="text-sm text-gray-600 flex items-center">
                        <MapPin className="w-4 h-4 mr-1" />
                        {property.city}, {property.state}
                      </p>
                      <div className="mt-2 flex items-center space-x-6 text-sm text-gray-600">
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
                    <div className="text-right">
                      <p className="text-xl font-bold text-gray-900">
                        ${property.price.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">
                        Added {property.addedDate}
                      </p>
                    </div>
                  </div>

                  {/* Notes Section */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900 flex items-center">
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Notes
                      </h4>
                      {editingNote === property.zpid ? (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleSaveNote(property.zpid)}
                            className="text-sm text-blue-600 hover:text-blue-800"
                          >
                            Save
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="text-sm text-gray-600 hover:text-gray-800"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleEditNote(property.zpid, property.notes)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          Edit
                        </button>
                      )}
                    </div>
                    {editingNote === property.zpid ? (
                      <textarea
                        value={noteText}
                        onChange={(e) => setNoteText(e.target.value)}
                        rows={2}
                        className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Add your notes about this property..."
                      />
                    ) : (
                      <p className="mt-2 text-sm text-gray-700">
                        {property.notes || "No notes added yet. Click edit to add your thoughts."}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="mt-4 flex items-center space-x-3">
                    <button
                      onClick={() => handleRemoveFavorite(property.zpid)}
                      className="flex items-center space-x-2 px-3 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>Remove from Favorites</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
