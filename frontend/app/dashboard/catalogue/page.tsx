"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ImagePlus, Copy, CheckCheck, Loader2, Upload, Link } from "lucide-react";

interface Product { id: string; name: string; }

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={copy} className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0">
      {copied ? <CheckCheck className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
    </button>
  );
}

export default function CataloguePage() {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [selectedProduct, setSelectedProduct] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [inputMode, setInputMode] = useState<"upload" | "url">("upload");
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const { data: products = [] } = useQuery({
    queryKey: ["products"],
    queryFn: async () => { const res = await api.get("/products/"); return res.data as Product[]; },
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreviewUrl(URL.createObjectURL(file));
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await api.post("/upload/product-image", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setImageUrl(res.data.url);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setUploading(false);
    }
  };

  const generate = useMutation({
    mutationFn: async () => {
      const res = await api.post("/catalogue/generate", {
        product_id: selectedProduct,
        image_url: imageUrl,
      });
      return res.data;
    },
    onMutate: () => { setGenerating(true); setResult(null); },
    onSuccess: (data) => { setResult(data); setGenerating(false); queryClient.invalidateQueries({ queryKey: ["content-packs"] }); },
    onError: () => setGenerating(false),
  });

  const steps = [
    { label: "Muse Wonder identifies jewellery type" },
    { label: "SAM 3.1 segments from background" },
    { label: "Muse Image generates 3 lifestyle shots" },
    { label: "Muse Spark writes copy in EN + HI" },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900">CatalogueForge</h2>
        <p className="text-gray-500 mt-1">Turn a raw photo into a complete content pack in under 90 seconds</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle className="text-base">Generate Content Pack</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Select Product</label>
                <Select value={selectedProduct ?? ""} onValueChange={(v) => setSelectedProduct(v ?? "")}>                  <SelectTrigger><SelectValue placeholder="Choose a product..." /></SelectTrigger>
                  <SelectContent>
                    {products.map((p) => (<SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setInputMode("upload")} className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium border transition-colors ${inputMode === "upload" ? "bg-gray-900 text-white border-gray-900" : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"}`}>
                  <Upload className="h-4 w-4" /> Upload Photo
                </button>
                <button onClick={() => setInputMode("url")} className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium border transition-colors ${inputMode === "url" ? "bg-gray-900 text-white border-gray-900" : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"}`}>
                  <Link className="h-4 w-4" /> Image URL
                </button>
              </div>
              {inputMode === "upload" ? (
                <div>
                  <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
                  <div onClick={() => fileRef.current?.click()} className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center cursor-pointer hover:border-gray-300 transition-colors">
                    {uploading ? (
                      <div className="flex flex-col items-center gap-2"><Loader2 className="h-8 w-8 text-gray-400 animate-spin" /><p className="text-sm text-gray-500">Uploading...</p></div>
                    ) : previewUrl ? (
                      <img src={previewUrl} alt="Preview" className="w-full h-48 object-contain rounded-lg" />
                    ) : (
                      <div className="flex flex-col items-center gap-2"><Upload className="h-8 w-8 text-gray-300" /><p className="text-sm text-gray-500">Click to upload a product photo</p><p className="text-xs text-gray-400">JPEG, PNG or WebP · Max 10MB</p></div>
                    )}
                  </div>
                  {imageUrl && !uploading && <p className="text-xs text-green-600 mt-2">✓ Photo uploaded successfully</p>}
                </div>
              ) : (
                <div className="space-y-2">
                  <input type="url" className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-gray-900" placeholder="https://example.com/product.jpg" value={imageUrl} onChange={(e) => { setImageUrl(e.target.value); setPreviewUrl(e.target.value); }} />
                  {previewUrl && <img src={previewUrl} alt="Preview" className="w-full h-48 object-cover rounded-lg border border-gray-100" />}
                </div>
              )}
              <Button className="w-full" onClick={() => generate.mutate()} disabled={!selectedProduct || !imageUrl || generating || uploading}>
                {generating ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating... (~90 seconds)</> : <><ImagePlus className="h-4 w-4 mr-2" />Generate Content Pack</>}
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-3">
                {steps.map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${result && i < 4 ? "bg-green-100 text-green-700" : generating ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-500"}`}>
                      {result && i < 4 ? "✓" : i + 1}
                    </div>
                    <span className="text-sm text-gray-600">{item.label}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
        <div>
          {generating && (
            <Card><CardContent className="pt-6 space-y-4"><Skeleton className="h-48 w-full rounded-lg" /><Skeleton className="h-4 w-3/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-full" /></CardContent></Card>
          )}
          {result && !generating && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{result.copy?.title}</CardTitle>
                  <Badge variant="default">Ready</Badge>
                </div>
                <p className="text-xs text-gray-500">{result.details?.jewellery_type} · {result.details?.material} · {result.details?.occasion}</p>
              </CardHeader>
              <CardContent className="space-y-6">
                {result.lifestyle_urls?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase mb-2">Generated Images</p>
                    <div className="grid grid-cols-3 gap-2">
                      {result.lifestyle_urls.map((url: string, i: number) => (
                        <img key={i} src={url} alt={`Lifestyle ${i + 1}`} className="rounded-lg w-full h-24 object-cover" />
                      ))}
                    </div>
                  </div>
                )}
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase mb-2">Product Description</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{result.copy?.description}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase mb-2">Instagram Captions</p>
                  <Tabs defaultValue="en">
                    <TabsList className="mb-3"><TabsTrigger value="en">English</TabsTrigger><TabsTrigger value="hi">Hindi</TabsTrigger></TabsList>
                    <TabsContent value="en" className="space-y-2">
                      {result.copy?.captions_en?.map((c: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg"><p className="text-sm text-gray-700 flex-1">{c}</p><CopyButton text={c} /></div>
                      ))}
                    </TabsContent>
                    <TabsContent value="hi" className="space-y-2">
                      {result.copy?.captions_hi?.map((c: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg"><p className="text-sm text-gray-700 flex-1">{c}</p><CopyButton text={c} /></div>
                      ))}
                    </TabsContent>
                  </Tabs>
                </div>
              </CardContent>
            </Card>
          )}
          {!result && !generating && (
            <Card><CardContent className="flex flex-col items-center justify-center py-16"><ImagePlus className="h-12 w-12 text-gray-300 mb-4" /><p className="text-gray-500 text-sm">Your content pack will appear here</p></CardContent></Card>
          )}
        </div>
      </div>
    </div>
  );
}

