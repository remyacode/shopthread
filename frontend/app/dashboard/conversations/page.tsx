"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, ShoppingCart } from "lucide-react";

interface Message {
  role: "buyer" | "seller";
  content: string;
  intent?: {
    message_type: string;
    product_name: string | null;
    extracted_language: string;
  };
}

interface Conversation {
  id: string;
  buyer_ig_handle: string;
  messages: Message[];
  last_message_at: string;
  created_at: string;
}

const INTENT_COLORS: Record<string, string> = {
  ORDER: "bg-green-100 text-green-700",
  INQUIRY: "bg-blue-100 text-blue-700",
  PAYMENT: "bg-purple-100 text-purple-700",
  RETURN: "bg-red-100 text-red-700",
  OTHER: "bg-gray-100 text-gray-700",
};

export default function ConversationsPage() {
  const [selected, setSelected] = useState<Conversation | null>(null);

  const { data: conversations = [], isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => {
      const res = await api.get("/conversations/");
      return res.data as Conversation[];
    },
  });

  return (
    <div className="flex h-full">
      {/* Left: conversation list */}
      <div className="w-80 border-r bg-white flex flex-col">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <p className="text-sm text-gray-500 mt-1">{conversations.length} total</p>
        </div>
        <div className="flex-1 overflow-auto">
          {isLoading ? (
            <div className="p-4 text-sm text-gray-500">Loading...</div>
          ) : conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4">
              <MessageSquare className="h-8 w-8 text-gray-300 mb-2" />
              <p className="text-sm text-gray-500 text-center">No conversations yet</p>
            </div>
          ) : (
            conversations.map((conv) => {
              const lastMsg = conv.messages?.[conv.messages.length - 1];
              const isSelected = selected?.id === conv.id;
              return (
                <div
                  key={conv.id}
                  onClick={() => setSelected(conv)}
                  className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors ${isSelected ? "bg-gray-50 border-l-2 border-l-gray-900" : ""}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900">@{conv.buyer_ig_handle}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(conv.last_message_at).toLocaleDateString()}
                    </p>
                  </div>
                  {lastMsg && (
                    <p className="text-xs text-gray-500 truncate">{lastMsg.content}</p>
                  )}
                  {lastMsg?.intent?.message_type && (
                    <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${INTENT_COLORS[lastMsg.intent.message_type] || "bg-gray-100 text-gray-700"}`}>
                      {lastMsg.intent.message_type}
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right: message thread */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {!selected ? (
          <div className="flex flex-col items-center justify-center h-full">
            <MessageSquare className="h-12 w-12 text-gray-300 mb-4" />
            <p className="text-gray-500">Select a conversation to view</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="p-6 bg-white border-b">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">@{selected.buyer_ig_handle}</h3>
                  <p className="text-sm text-gray-500">{selected.messages?.length || 0} messages</p>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-auto p-6 space-y-4">
              {(selected.messages || []).map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "buyer" ? "justify-start" : "justify-end"}`}>
                  <div className={`max-w-sm ${msg.role === "buyer" ? "items-start" : "items-end"} flex flex-col gap-1`}>
                    <div className={`px-4 py-2 rounded-2xl text-sm ${
                      msg.role === "buyer"
                        ? "bg-white text-gray-800 border border-gray-100"
                        : "bg-gray-900 text-white"
                    }`}>
                      {msg.content}
                    </div>
                    {msg.intent && (
                      <div className="flex gap-2 flex-wrap px-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${INTENT_COLORS[msg.intent.message_type] || "bg-gray-100"}`}>
                          {msg.intent.message_type}
                        </span>
                        {msg.intent.product_name && (
                          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                            <ShoppingCart className="h-3 w-3" />
                            {msg.intent.product_name}
                          </span>
                        )}
                        <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-500">
                          {msg.intent.extracted_language}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
