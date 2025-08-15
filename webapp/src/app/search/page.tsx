import { PropertySearch } from "@/components/property-search";

export default function SearchPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Search Properties</h1>
        <p className="mt-2 text-gray-600">
          Find waterfront properties by location, price, features, and more
        </p>
      </div>

      <PropertySearch />
    </div>
  );
}
