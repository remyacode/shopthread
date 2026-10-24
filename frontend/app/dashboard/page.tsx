"use client";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShoppingCart, MessageSquare, Package, TrendingUp } from "lucide-react";

const stats = [
  { label: "Total Orders", value: "0", icon: ShoppingCart, change: "Today" },
  { label: "Unread DMs", value: "0", icon: MessageSquare, change: "Live" },
  { label: "Active Products", value: "0", icon: Package, change: "In catalogue" },
  { label: "Revenue", value: "₹0", icon: TrendingUp, change: "This week" },
];

export default function DashboardPage() {
  const { vendor } = useAuth();

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900">
          Good morning, {vendor?.full_name.split(" ")[0]}
        </h2>
        <p className="text-gray-500 mt-1">Here's what's happening with your shop today.</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.label}
                </CardTitle>
                <Icon className="h-4 w-4 text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                <p className="text-xs text-gray-500 mt-1">{stat.change}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Placeholder sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 py-8 text-center">
              No orders yet. Orders from Instagram DMs will appear here.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 py-8 text-center">
              No conversations yet. DMs will appear here when received.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
