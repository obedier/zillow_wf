import { ExtractionManager } from "@/components/extraction-manager";

export default function ExtractionPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Property Extraction</h1>
        <p className="mt-2 text-gray-600">
          Add new properties to your database by extracting from Zillow search URLs
        </p>
      </div>

      <ExtractionManager />
    </div>
  );
}
