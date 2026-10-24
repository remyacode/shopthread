"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function Home() {
  const { vendor, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (vendor) {
        router.push("/dashboard");
      } else {
        router.push("/login");
      }
    }
  }, [vendor, isLoading, router]);

  return null;
}
