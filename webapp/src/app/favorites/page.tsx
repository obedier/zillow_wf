import { FavoritesList } from "@/components/favorites-list";

export default function FavoritesPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Favorite Properties</h1>
        <p className="mt-2 text-gray-600">
          View and manage your saved favorite waterfront properties
        </p>
      </div>

      <FavoritesList />
    </div>
  );
}
