"use client";

import { useState } from "react";
import { Send, Bot, User, Lightbulb, TrendingUp, MapPin, DollarSign } from "lucide-react";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const suggestedQuestions = [
  "What are the most expensive properties in the database?",
  "How many properties are in Fort Lauderdale?",
  "What's the average price per square foot?",
  "Show me properties with boat docks",
  "Which areas have the most properties?",
  "What's the price trend across all properties?",
];

export function AIAgent() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content: "Hello! I'm your AI property agent. I can help you analyze your complete property database - including waterfront and non-waterfront properties. Ask me anything about properties, prices, locations, or trends!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = generateAIResponse(input);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: aiResponse,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const generateAIResponse = (question: string): string => {
    const lowerQuestion = question.toLowerCase();
    
    if (lowerQuestion.includes("expensive") || lowerQuestion.includes("price")) {
      return "Based on your database of 1,200+ properties, the most expensive properties are:\n\n" +
             "• 9012 Ocean Blvd, Palm Beach - $4.2M (5 beds, 4 baths, 200ft waterfront)\n" +
             "• 1234 Waterfront Dr, Fort Lauderdale - $2.5M (4 beds, 3 baths, 150ft waterfront)\n" +
             "• 5678 Marina Way, Miami - $1.8M (3 beds, 2 baths, 100ft waterfront)\n\n" +
             "The average price across all properties is $1.8M, with waterfront properties averaging $2.1M.";
    }
    
    if (lowerQuestion.includes("fort lauderdale") || lowerQuestion.includes("location")) {
      return "Fort Lauderdale has 156 properties in your database:\n\n" +
             "• Total properties: 156\n" +
             "• Waterfront properties: 89\n" +
             "• Average price: $1.8M\n" +
             "• Price range: $850K - $4.2M\n" +
             "• Properties with waterfront analysis: 67\n\n" +
             "The most popular areas are Las Olas Isles, Coral Ridge, and Rio Vista.";
    }
    
    if (lowerQuestion.includes("square foot") || lowerQuestion.includes("sqft")) {
      return "Price per square foot analysis across all 1,200+ properties:\n\n" +
             "• Overall average: $875/sqft\n" +
             "• Waterfront premium: +45% over non-waterfront\n" +
             "• By location:\n" +
             "  - Miami Beach: $1,200/sqft\n" +
             "  - Fort Lauderdale: $950/sqft\n" +
             "  - Palm Beach: $1,450/sqft\n\n" +
             "Properties with deep water access command the highest per-sqft prices.";
    }
    
    if (lowerQuestion.includes("boat dock") || lowerQuestion.includes("dock")) {
      return "Properties with boat docks (from waterfront analysis data):\n\n" +
             "• Total count: 234 properties\n" +
             "• Average price: $2.8M\n" +
             "• Most common in: Fort Lauderdale (89), Miami (67), Palm Beach (78)\n\n" +
             "Note: This data is available for 634 properties that have detailed waterfront analysis. " +
             "The remaining properties may have docks but we don't have detailed measurements.";
    }
    
    if (lowerQuestion.includes("trend") || lowerQuestion.includes("market")) {
      return "Market trends across your complete property database:\n\n" +
             "• Total properties: 1,200+\n" +
             "• Properties with waterfront analysis: 634\n" +
             "• Price appreciation: +8.2% year-over-year\n" +
             "• Days on market: Average 45 days (down from 67 days)\n" +
             "• Inventory levels: +12% increase in new listings\n" +
             "• Waterfront premium: Stable at 35-40% over inland properties\n\n" +
             "The market shows strong demand across all property types.";
    }
    
    return "I can help you analyze your complete property database of 1,200+ properties! Try asking about:\n\n" +
           "• Property prices and trends across all properties\n" +
           "• Location-specific insights for any area\n" +
           "• Waterfront analysis data (available for 634 properties)\n" +
           "• Market statistics and comparisons\n" +
           "• Property recommendations based on criteria\n\n" +
           "Note: Waterfront analysis data (dock info, measurements) is available for properties where we could extract detailed measurements.";
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Chat Interface */}
      <div className="lg:col-span-2">
        <div className="bg-white border border-gray-200 rounded-lg h-[600px] flex flex-col">
          {/* Chat Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">AI Property Agent</h3>
                <p className="text-sm text-gray-600">Ask me about your complete property database</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.type === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.type === "assistant" && (
                      <Bot className="h-4 w-4 text-blue-600 mt-1 flex-shrink-0" />
                    )}
                    {message.type === "user" && (
                      <User className="h-4 w-4 text-blue-200 mt-1 flex-shrink-0" />
                    )}
                    <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                  </div>
                  <div
                    className={`text-xs mt-2 ${
                      message.type === "user" ? "text-blue-200" : "text-gray-500"
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Bot className="h-4 w-4 text-blue-600" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex space-x-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Ask about your complete property database..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={handleSendMessage}
                disabled={!input.trim() || isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Suggested Questions & Insights */}
      <div className="space-y-6">
        {/* Suggested Questions */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Lightbulb className="h-5 w-5 text-yellow-500 mr-2" />
            Suggested Questions
          </h3>
          <div className="space-y-3">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                className="w-full text-left p-3 text-sm text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Insights */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <TrendingUp className="h-5 w-5 text-green-500 mr-2" />
            Database Overview
          </h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <MapPin className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">Total Properties</p>
                <p className="text-xs text-gray-600">1,200+ properties</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <DollarSign className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">Waterfront Analysis</p>
                <p className="text-xs text-gray-600">634 properties with detailed data</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <TrendingUp className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">Coverage</p>
                <p className="text-xs text-gray-600">All properties searchable</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
