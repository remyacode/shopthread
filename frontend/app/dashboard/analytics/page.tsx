"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3, TrendingUp, Package, MessageSquare, ShoppingCart, Loader2, Lightbulb, AlertCircle, Zap } from "lucide-react";

export default function AnalyticsPage() {
  const [briefRequested, setBriefRequested] = useState(false);

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["metrics"],
    queryFn: async () => { const res = await api.get("/analytics/metrics"); return res.data; },
  });

  const { data: briefData, isLoading: briefLoading } = useQuery({
    queryKey: ["weekly-brief"],
    queryFn: async () => { const res = await api.get("/analytics/weekly-brief"); return res.data; },
    enabled: briefRequested,
  });

  const brief = briefData?.brief;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900">GrowthRadar</h2>
        <p className="text-gray-500 mt-1">AI-powered intelligence from your own shop data</p>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {metricsLoading ? (
          Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-24 rounded-lg" />)
        ) : (
          <>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-500">Total Orders</p>
                  <ShoppingCart className="h-4 w-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold">{metrics?.total_orders ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-500">Revenue</p>
                  <TrendingUp className="h-4 w-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold">₹{(metrics?.total_revenue ?? 0).toLocaleString()}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-500">Active Products</p>
                  <Package className="h-4 w-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold">{metrics?.active_products ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-500">DM Conversations</p>
                  <MessageSquare className="h-4 w-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold">{metrics?.total_conversations ?? 0}</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Weekly Brief */}
      <div className="space-y-6">
        {!briefRequested && !brief && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <BarChart3 className="h-12 w-12 text-gray-300 mb-4" />
              <p className="text-gray-700 font-medium mb-2">Weekly Intelligence Brief</p>
              <p className="text-gray-500 text-sm text-center mb-6 max-w-md">
                GrowthRadar analyses your orders, DMs, and inventory to generate actionable insights. Takes ~20 seconds.
              </p>
              <Button onClick={() => setBriefRequested(true)}>
                <Zap className="h-4 w-4 mr-2" />
                Generate Weekly Brief
              </Button>
            </CardContent>
          </Card>
        )}

        {briefLoading && (
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                <p className="text-sm text-gray-500">GrowthRadar is analysing your shop data...</p>
              </div>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-5/6" />
            </CardContent>
          </Card>
        )}

        {brief && !briefLoading && (
          <>
            {/* Headline */}
            <Card className="border-gray-900">
              <CardContent className="pt-6">
                <p className="text-xs font-medium text-gray-500 uppercase mb-2">This Week</p>
                <p className="text-lg font-medium text-gray-900">{brief.headline}</p>
                <div className="flex gap-6 mt-4">
                  <div>
                    <p className="text-2xl font-bold text-gray-900">₹{brief.revenue_summary?.total?.toLocaleString()}</p>
                    <p className="text-xs text-gray-500">Revenue</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{brief.revenue_summary?.orders}</p>
                    <p className="text-xs text-gray-500">Orders</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">₹{brief.revenue_summary?.avg_order_value?.toFixed(0)}</p>
                    <p className="text-xs text-gray-500">Avg Order Value</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Top Insights */}
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><Lightbulb className="h-4 w-4" />Top Insights</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {brief.top_insights?.map((insight: string, i: number) => (
                    <div key={i} className="flex gap-3">
                      <span className="text-xs font-bold text-gray-400 mt-0.5">{i + 1}</span>
                      <p className="text-sm text-gray-700">{insight}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Actions */}
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><Zap className="h-4 w-4" />Do This Week</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {brief.action_this_week?.map((action: string, i: number) => (
                    <div key={i} className="flex gap-3 p-3 bg-gray-50 rounded-lg">
                      <span className="text-xs font-bold text-gray-400 mt-0.5">{i + 1}</span>
                      <p className="text-sm text-gray-700">{action}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Best Seller */}
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><TrendingUp className="h-4 w-4" />Best Seller</CardTitle></CardHeader>
                <CardContent>
                  {brief.best_seller?.product ? (
                    <div>
                      <p className="font-medium text-gray-900">{brief.best_seller.product}</p>
                      <p className="text-sm text-gray-500 mt-1">{brief.best_seller.reason}</p>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Not enough data yet</p>
                  )}
                </CardContent>
              </Card>

              {/* Buyer Signals */}
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><MessageSquare className="h-4 w-4" />Buyer Signals</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  {brief.buyer_signals?.length > 0 ? (
                    brief.buyer_signals.map((signal: string, i: number) => (
                      <div key={i} className="flex gap-2 p-2 bg-blue-50 rounded-lg">
                        <AlertCircle className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-blue-700">{signal}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No signals detected yet</p>
                  )}
                </CardContent>
              </Card>
            </div>

            <Button variant="outline" onClick={() => setBriefRequested(false)} className="w-full">
              Regenerate Brief
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

