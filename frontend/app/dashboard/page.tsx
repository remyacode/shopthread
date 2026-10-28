"use client";

import { useAuth } from "@/context/AuthContext";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ShoppingCart, MessageSquare, Package, TrendingUp, Clock } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { vendor } = useAuth();

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["metrics"],
    queryFn: async () => { const res = await api.get("/analytics/metrics"); return res.data; },
  });

  const { data: orders = [], isLoading: ordersLoading } = useQuery({
    queryKey: ["orders"],
    queryFn: async () => { const res = await api.get("/orders/"); return res.data; },
  });

  const { data: conversations = [], isLoading: convsLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => { const res = await api.get("/conversations/"); return res.data; },
  });

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  const recentOrders = orders.slice(0, 5);
  const recentConversations = conversations.slice(0, 5);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900">
          {getGreeting()}, {vendor?.full_name.split(" ")[0]}
        </h2>
        <p className="text-gray-500 mt-1">Here's what's happening with your shop today.</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metricsLoading ? (
          Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-24 rounded-lg" />)
        ) : (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Total Orders</CardTitle>
                <ShoppingCart className="h-4 w-4 text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{metrics?.total_orders ?? 0}</div>
                <p className="text-xs text-gray-500 mt-1">{metrics?.pending_orders ?? 0} pending</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Revenue</CardTitle>
                <TrendingUp className="h-4 w-4 text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">₹{(metrics?.total_revenue ?? 0).toLocaleString()}</div>
                <p className="text-xs text-gray-500 mt-1">From paid orders</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Active Products</CardTitle>
                <Package className="h-4 w-4 text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{metrics?.active_products ?? 0}</div>
                <p className="text-xs text-gray-500 mt-1">In catalogue</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">DM Conversations</CardTitle>
                <MessageSquare className="h-4 w-4 text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{metrics?.total_conversations ?? 0}</div>
                <p className="text-xs text-gray-500 mt-1">Total buyers</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Recent Orders</CardTitle>
            <Link href="/dashboard/orders" className="text-xs text-gray-500 hover:text-gray-900">View all →</Link>
          </CardHeader>
          <CardContent>
            {ordersLoading ? (
              <div className="space-y-3">{Array(3).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
            ) : recentOrders.length === 0 ? (
              <p className="text-sm text-gray-500 py-4 text-center">No orders yet. Orders from Instagram DMs will appear here.</p>
            ) : (
              <div className="space-y-3">
                {recentOrders.map((order: any) => (
                  <div key={order.id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div>
                      <p className="text-sm font-medium text-gray-900">@{order.buyer_ig_handle}</p>
                      <p className="text-xs text-gray-500">{order.products?.name || "Unknown product"} · {order.variant || "—"}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">₹{order.amount.toLocaleString()}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        order.status === "DELIVERED" ? "bg-green-100 text-green-700" :
                        order.status === "SHIPPED" ? "bg-purple-100 text-purple-700" :
                        order.status === "CONFIRMED" ? "bg-blue-100 text-blue-700" :
                        "bg-yellow-100 text-yellow-700"
                      }`}>{order.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Conversations */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Recent Conversations</CardTitle>
            <Link href="/dashboard/conversations" className="text-xs text-gray-500 hover:text-gray-900">View all →</Link>
          </CardHeader>
          <CardContent>
            {convsLoading ? (
              <div className="space-y-3">{Array(3).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
            ) : recentConversations.length === 0 ? (
              <p className="text-sm text-gray-500 py-4 text-center">No conversations yet. DMs will appear here when received.</p>
            ) : (
              <div className="space-y-3">
                {recentConversations.map((conv: any) => {
                  const lastMsg = conv.messages?.[conv.messages.length - 1];
                  return (
                    <div key={conv.id} className="flex items-start justify-between py-2 border-b last:border-0">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">@{conv.buyer_ig_handle}</p>
                        <p className="text-xs text-gray-500 truncate">{lastMsg?.content || "No messages"}</p>
                      </div>
                      <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                        <Clock className="h-3 w-3 text-gray-300" />
                        <p className="text-xs text-gray-400">{new Date(conv.last_message_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

