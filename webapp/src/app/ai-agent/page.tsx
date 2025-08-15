import { AIAgent } from "@/components/ai-agent";

export default function AIAgentPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Property Agent</h1>
        <p className="mt-2 text-gray-600">
          Ask questions about your waterfront property database and get intelligent insights
        </p>
      </div>

      <AIAgent />
    </div>
  );
}
