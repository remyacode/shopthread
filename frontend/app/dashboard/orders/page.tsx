"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ShoppingCart, MessageSquare } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-yellow-100 text-yellow-800",
  CONFIRMED: "bg-blue-100 text-blue-800",
  SHIPPED: "bg-purple-100 text-purple-800",
  DELIVERED: "bg-green-100 text-green-800",
  CANCELLED: "bg-red-100 text-red-800",
};

const STATUSES = ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"];

interface Order {
  id: string;
  buyer_ig_handle: string;
  variant: string;
  quantity: number;
  amount: number;
  status: string;
  payment_status: string;
  created_at: string;
  products: { name: string } | null;
}

export default function OrdersPage() {
  const queryClient = useQueryClient();
  const [testDMOpen, setTestDMOpen] = useState(false);
  const [dmForm, setDmForm] = useState({ buyer_handle: "", message: "" });
  const [dmResult, setDmResult] = useState<any>(null);

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ["orders"],
    queryFn: async () => {
      const res = await api.get("/orders/");
      return res.data as Order[];
    },
  });

  const updateStatus = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const res = await api.patch(`/orders/${id}/status`, { status });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["orders"] }),
  });

  const testDM = useMutation({
    mutationFn: async (data: any) => {
      const res = await api.post("/orders/test-dm", data);
      return res.data;
    },
    onSuccess: (data) => {
      setDmResult(data);
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Orders</h2>
          <p className="text-gray-500 mt-1">{orders.length} total orders</p>
        </div>
        <Button onClick={() => { setTestDMOpen(true); setDmResult(null); }}>
          <MessageSquare className="h-4 w-4 mr-2" />
          Test OrderWeave
        </Button>
      </div>

      {/* Test DM Dialog */}
      <Dialog open={testDMOpen} onOpenChange={setTestDMOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Test OrderWeave Agent</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Buyer Instagram Handle</Label>
              <Input
                placeholder="priya_jewels"
                value={dmForm.buyer_handle}
                onChange={(e) => setDmForm({ ...dmForm, buyer_handle: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>DM Message</Label>
              <Textarea
                placeholder="Haan le leti hun, book kar do ek gold jhumka small size"
                value={dmForm.message}
                onChange={(e) => setDmForm({ ...dmForm, message: e.target.value })}
                rows={3}
              />
            </div>
            <Button
              className="w-full"
              onClick={() => testDM.mutate(dmForm)}
              disabled={testDM.isPending || !dmForm.buyer_handle || !dmForm.message}
            >
              {testDM.isPending ? "Processing..." : "Process DM"}
            </Button>
            {dmResult && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-3">
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Intent Detected</p>
                  <p className="text-sm font-medium">{dmResult.intent.message_type} — {dmResult.intent.product_name}</p>
                </div>
                {dmResult.order_id && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase">Order Created</p>
                    <p className="text-sm font-mono">{dmResult.order_id}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">AI Reply</p>
                  <p className="text-sm text-gray-700 italic">"{dmResult.reply}"</p>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading orders...</div>
      ) : orders.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <ShoppingCart className="h-12 w-12 text-gray-300 mb-4" />
            <p className="text-gray-500">No orders yet.</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order ID</TableHead>
                <TableHead>Buyer</TableHead>
                <TableHead>Product</TableHead>
                <TableHead>Variant</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Payment</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Update</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-mono text-xs">{order.id.slice(0, 8).toUpperCase()}</TableCell>
                  <TableCell>@{order.buyer_ig_handle}</TableCell>
                  <TableCell>{order.products?.name || "—"}</TableCell>
                  <TableCell>{order.variant || "—"}</TableCell>
                  <TableCell>₹{order.amount.toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge variant={order.payment_status === "PAID" ? "default" : "secondary"}>
                      {order.payment_status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[order.status]}`}>
                      {order.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Select
                      value={order.status}
                      onValueChange={(value) => updateStatus.mutate({ id: order.id, status: value })}
                    >
                      <SelectTrigger className="w-32 h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {STATUSES.map((s) => (
                          <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}

