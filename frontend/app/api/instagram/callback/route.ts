import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const error = searchParams.get("error");

  if (error) {
    return NextResponse.redirect(new URL("/dashboard?instagram=error", request.url));
  }

  const backendUrl = `${process.env.NEXT_PUBLIC_API_URL}/instagram/callback?code=${code}&state=${state}`;
  
  const res = await fetch(backendUrl, { redirect: "manual" });
  
  const location = res.headers.get("location");
  if (location) {
    return NextResponse.redirect(location);
  }

  return NextResponse.redirect(new URL("/dashboard?instagram=connected", request.url));
}
