"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { CheckCircle, Package, Link2, Zap } from "lucide-react";

const STEPS = [
  { id: "product", label: "Add your first product", icon: Package, description: "Add at least one product so OrderWeave can create orders when buyers DM you." },
  { id: "instagram", label: "Connect Instagram", icon: Link2, description: "Connect your Instagram Business account to receive DMs and automate order processing." },
  { id: "ready", label: "You're ready!", icon: Zap, description: "ShopThread is live. Every DM you receive will be processed automatically." },
];

export default function OnboardingPage() {
  const { vendor } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [productForm, setProductForm] = useState({ name: "", price: "", inventory_count: "", variants: "" });
  const [productAdded, setProductAdded] = useState(false);

  const addProduct = useMutation({
    mutationFn: async () => {
      const res = await api.post("/products/", {
        name: productForm.name,
        price: parseFloat(productForm.price),
        inventory_count: parseInt(productForm.inventory_count) || 0,
        variants: productForm.variants ? productForm.variants.split(",").map(v => v.trim()) : [],
      });
      return res.data;
    },
    onSuccess: () => {
      setProductAdded(true);
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });

  const isStepDone = (stepId: string) => {
    if (stepId === "product") return productAdded;
    return false;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to ShopThread</h1>
          <p className="text-gray-500 mt-2">Let's get your shop set up in 2 minutes</p>
        </div>

        <div className="space-y-4">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            const done = isStepDone(step.id);
            const isActive = currentStep === index;
            const isLast = step.id === "ready";

            return (
              <Card key={step.id} className={`transition-all ${isActive ? "ring-2 ring-gray-900" : ""}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    {done ? (
                      <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
                    ) : (
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${isActive ? "border-gray-900" : "border-gray-300"}`}>
                        <span className="text-xs font-bold text-gray-500">{index + 1}</span>
                      </div>
                    )}
                    <div>
                      <CardTitle className="text-base">{step.label}</CardTitle>
                      <CardDescription>{step.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>

                {isActive && !done && !isLast && (
                  <CardContent>
                    {step.id === "product" && (
                      <div className="space-y-4 mt-2">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Product Name</Label>
                            <Input placeholder="Gold Jhumka" value={productForm.name} onChange={e => setProductForm({...productForm, name: e.target.value})} />
                          </div>
                          <div className="space-y-2">
                            <Label>Price (₹)</Label>
                            <Input type="number" placeholder="1299" value={productForm.price} onChange={e => setProductForm({...productForm, price: e.target.value})} />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Stock</Label>
                            <Input type="number" placeholder="10" value={productForm.inventory_count} onChange={e => setProductForm({...productForm, inventory_count: e.target.value})} />
                          </div>
                          <div className="space-y-2">
                            <Label>Variants (comma separated)</Label>
                            <Input placeholder="small, medium, large" value={productForm.variants} onChange={e => setProductForm({...productForm, variants: e.target.value})} />
                          </div>
                        </div>
                        <Button className="w-full" onClick={() => addProduct.mutate()} disabled={!productForm.name || !productForm.price || addProduct.isPending}>
                          {addProduct.isPending ? "Adding..." : "Add Product"}
                        </Button>
                      </div>
                    )}

                    {step.id === "instagram" && (
                      <div className="mt-2 space-y-4">
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                          <p className="text-sm text-blue-800">
                            <strong>Note for judges:</strong> This is a demo build. Instagram Business account connection will be available after Meta app review is approved for production. To test the full DM-to-order flow, use the{" "}
                            <a href="/simulator" className="underline font-semibold">DM Simulator →</a>
                          </p>
                        </div>
                        <Button className="w-full" variant="outline" onClick={() => router.push("/dashboard")}>
                          Continue to Dashboard →
                        </Button>
                      </div>
                    )}
                  </CardContent>
                )}

                {done && !isLast && (
                  <CardContent>
                    <p className="text-sm text-green-600">✓ Done</p>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>

        <div className="flex gap-3 mt-6">
          {currentStep > 0 && (
            <Button variant="outline" className="flex-1" onClick={() => setCurrentStep(currentStep - 1)}>Back</Button>
          )}
          {currentStep < STEPS.length - 1 && (
            <Button className="flex-1" onClick={() => setCurrentStep(currentStep + 1)} disabled={currentStep === 0 && !productAdded}>
              {isStepDone(STEPS[currentStep].id) ? "Next" : "Skip for now"}
            </Button>
          )}
          {currentStep === STEPS.length - 1 && (
            <Button className="flex-1" onClick={() => router.push("/dashboard")}>
              Go to Dashboard →
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
