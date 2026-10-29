"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Truck, Plus, MessageSquare } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-gray-100 text-gray-700",
  PACKED: "bg-blue-100 text-blue-700",
  SHIPPED: "bg-purple-100 text-purple-700",
  OUT_FOR_DELIVERY: "bg-yellow-100 text-yellow-700",
  DELIVERED: "bg-green-100 text-green-700",
  FAILED: "bg-red-100 text-red-700",
};

const STATUSES = ["PENDING", "PACKED", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "FAILED"];

export default function ShipmentsPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [currentNotification, setCurrentNotification] = useState("");
  const [createForm, setCreateForm] = useState({ order_id: "", tracking_id: "", carrier: "" });

  const { data: shipments = [], isLoading } = useQuery({
    queryKey: ["shipments"],
    queryFn: async () => { const res = await api.get("/shipments/"); return res.data; },
  });

  const { data: orders = [] } = useQuery({
    queryKey: ["orders-pending"],
    queryFn: async () => {
      const res = await api.get("/orders/");
      return res.data.filter((o: any) => o.status === "PENDING" || o.status === "CONFIRMED");
    },
  });

  const createShipment = useMutation({
    mutationFn: async (data: any) => { const res = await api.post("/shipments/", data); return res.data; },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["shipments"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      setCreateOpen(false);
      setCurrentNotification(data.buyer_notification);
      setNotificationOpen(true);
      setCreateForm({ order_id: "", tracking_id: "", carrier: "" });
    },
  });

  const updateShipment = useMutation({
    mutationFn: async ({ id, status, tracking_id }: any) => {
      const res = await api.patch(`/shipments/${id}`, { status, tracking_id });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["shipments"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      if (data.buyer_notification) {
        setCurrentNotification(data.buyer_notification);
        setNotificationOpen(true);
      }
    },
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Shipments</h2>
          <p className="text-gray-500 mt-1">Track orders and send automated buyer updates</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Shipment
        </Button>
      </div>

      {/* Create Shipment Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Shipment</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Order</Label>
              <Select value={createForm.order_id} onValueChange={(v) => setCreateForm({ ...createForm, order_id: v ?? "" })}>
                <SelectTrigger><SelectValue placeholder="Select an order..." /></SelectTrigger>
                <SelectContent>
                  {orders.map((o: any) => (
                    <SelectItem key={o.id} value={o.id}>
                      {o.id.slice(0, 8).toUpperCase()} — @{o.buyer_ig_handle}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Tracking ID (optional)</Label>
              <Input placeholder="IN123456789" value={createForm.tracking_id} onChange={(e) => setCreateForm({ ...createForm, tracking_id: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Carrier (optional)</Label>
              <Input placeholder="Delhivery, BlueDart, India Post..." value={createForm.carrier} onChange={(e) => setCreateForm({ ...createForm, carrier: e.target.value })} />
            </div>
            <Button className="w-full" onClick={() => createShipment.mutate(createForm)} disabled={!createForm.order_id || createShipment.isPending}>
              {createShipment.isPending ? "Creating..." : "Create & Notify Buyer"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Buyer Notification Preview */}
      <Dialog open={notificationOpen} onOpenChange={setNotificationOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle className="flex items-center gap-2"><MessageSquare className="h-4 w-4" />Buyer Notification Generated</DialogTitle></DialogHeader>
          <div className="mt-4">
            <p className="text-xs font-medium text-gray-500 uppercase mb-2">Auto-generated DM for buyer</p>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">{currentNotification}</p>
            </div>
            <p className="text-xs text-gray-400 mt-2">This message would be sent automatically via Instagram DM when webhook is live.</p>
          </div>
        </DialogContent>
      </Dialog>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading shipments...</div>
      ) : shipments.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Truck className="h-12 w-12 text-gray-300 mb-4" />
            <p className="text-gray-500">No shipments yet. Create one from a confirmed order.</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order</TableHead>
                <TableHead>Buyer</TableHead>
                <TableHead>Product</TableHead>
                <TableHead>Tracking</TableHead>
                <TableHead>Carrier</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Update</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {shipments.map((s: any) => (
                <TableRow key={s.id}>
                  <TableCell className="font-mono text-xs">{s.order_id?.slice(0, 8).toUpperCase()}</TableCell>
                  <TableCell>@{s.orders?.buyer_ig_handle}</TableCell>
                  <TableCell>{s.orders?.products?.name || "—"}</TableCell>
                  <TableCell className="font-mono text-xs">{s.tracking_id || "—"}</TableCell>
                  <TableCell>{s.carrier || "—"}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[s.status] || "bg-gray-100 text-gray-700"}`}>
                      {s.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Select value={s.status ?? ""} onValueChange={(value) => value && updateShipment.mutate({ id: s.id, status: value })}>
                      <SelectTrigger className="w-36 h-8 text-xs"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {STATUSES.map((status) => (
                          <SelectItem key={status} value={status} className="text-xs">{status}</SelectItem>
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

