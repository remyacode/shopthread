"use client";

import { useState, useRef, useEffect } from "react";

const BACKEND = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  from: "buyer" | "vendor";
  text: string;
  time: string;
}

interface Vendor {
  id: string;
  name: string;
  handle: string;
  instagram_page_id: string;
  connected: boolean;
}

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function newSenderId(): string {
  return "demo_" + Math.random().toString(36).slice(2, 10) + "_" + Date.now();
}

function MessageBubble({ msg, initial }: { msg: Message; initial: string }) {
  const hasUpi = msg.text.includes("upi://");
  const upiMatch = hasUpi ? msg.text.match(/(upi:\/\/[^\s]+)/) : null;
  const upiUrl = upiMatch ? upiMatch[1] : null;
  const amountMatch = upiUrl ? upiUrl.match(/am=([^&]+)/) : null;
  const amount = amountMatch ? amountMatch[1] : "";
  const beforeUpi = upiUrl ? msg.text.split(upiUrl)[0] : msg.text;
  const afterUpi = upiUrl ? msg.text.split(upiUrl)[1] : "";

  return (
    <div style={{
      maxWidth: "70%",
      background: msg.from === "buyer" ? "#3797f0" : "#efefef",
      color: msg.from === "buyer" ? "#fff" : "#000",
      padding: "8px 12px",
      borderRadius: msg.from === "buyer" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
      fontSize: 14,
      lineHeight: 1.5,
      wordBreak: "break-word" as const
    }}>
      {hasUpi && upiUrl ? (
        <>
          {beforeUpi && <span style={{ display: "block", marginBottom: 6 }}>{beforeUpi.trim()}</span>}
          <a href={upiUrl} style={{ display: "block", background: "#1a1a1a", color: "#fff", padding: "10px 14px", borderRadius: 10, textAlign: "center" as const, textDecoration: "none", fontSize: 13, fontWeight: 600 }}>
            💳 Pay {amount ? `₹${amount}` : ""} Now
          </a>
          {afterUpi && <span style={{ display: "block", marginTop: 6 }}>{afterUpi.trim()}</span>}
        </>
      ) : msg.text}
      <div style={{ fontSize: 10, opacity: 0.6, marginTop: 4, textAlign: "right" as const }}>{msg.time}</div>
    </div>
  );
}

export default function SimulatorPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const senderIdRef = useRef<string>(newSenderId());
  const messageIndexRef = useRef(0);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${BACKEND}/webhook/vendors/list`)
      .then(r => r.json())
      .then((data: Vendor[]) => {
        setVendors(data);
        if (data.length > 0) selectVendor(data[0]);
      })
      .catch(() => {});
  }, []);

  function selectVendor(v: Vendor) {
    setSelectedVendor(v);
    setMessages([{ from: "vendor", text: `Hi! Welcome to ${v.name}. How can I help you today?`, time: nowTime() }]);
    setInput("");
    senderIdRef.current = newSenderId();
    messageIndexRef.current = 0;
    if (pollingRef.current) clearInterval(pollingRef.current);
  }

  function clearChat() {
    if (!selectedVendor) return;
    senderIdRef.current = newSenderId();
    messageIndexRef.current = 0;
    setMessages([{ from: "vendor", text: `Hi! Welcome to ${selectedVendor.name}. How can I help you today?`, time: nowTime() }]);
    setInput("");
    if (pollingRef.current) clearInterval(pollingRef.current);
  }

  useEffect(() => {
    if (!selectedVendor) return;
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(
          `${BACKEND}/webhook/conversation/latest?vendor_id=${selectedVendor.id}&sender_id=${senderIdRef.current}&after_index=${messageIndexRef.current}`
        );
        const data = await res.json();
        if (data.messages?.length > 0) {
          setMessages(prev => [
            ...prev,
            ...data.messages.map((m: any) => ({ from: "vendor" as const, text: m.content, time: nowTime() }))
          ]);
          messageIndexRef.current = data.total;
        }
      } catch {}
    }, 3000);
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [selectedVendor]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    if (!input.trim() || loading || !selectedVendor) return;
    const text = input.trim();
    setInput("");
    setMessages(prev => [...prev, { from: "buyer", text, time: nowTime() }]);
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND}/webhook/simulate-dm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender_id: senderIdRef.current, message: text, vendor_id: selectedVendor.id })
      });
      const data = await res.json();
      if (data.reply) {
        setMessages(prev => [...prev, { from: "vendor", text: data.reply, time: nowTime() }]);
        messageIndexRef.current += 2;
      }
    } catch {
      setMessages(prev => [...prev, { from: "vendor", text: "Sorry, something went wrong.", time: nowTime() }]);
    } finally {
      setLoading(false);
    }
  }

  const initial = selectedVendor ? selectedVendor.name.charAt(0).toUpperCase() : "S";

  return (
    <div style={{ minHeight: "100vh", background: "#000", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ color: "#888", fontSize: 13 }}>Chatting with:</span>
        <select
          value={selectedVendor?.id || ""}
          onChange={e => { const v = vendors.find(x => x.id === e.target.value); if (v) selectVendor(v); }}
          style={{ background: "#1a1a1a", color: "#fff", border: "1px solid #333", borderRadius: 8, padding: "6px 12px", fontSize: 13, cursor: "pointer", outline: "none" }}
        >
          {vendors.map(v => (
            <option key={v.id} value={v.id}>{v.name} {v.handle ? `(@${v.handle})` : ""}</option>
          ))}
        </select>
        <button
          onClick={clearChat}
          style={{ background: "#1a1a1a", color: "#888", border: "1px solid #333", borderRadius: 8, padding: "6px 12px", fontSize: 13, cursor: "pointer" }}
        >
          New Chat
        </button>
      </div>

      <div style={{ width: 380, background: "#fff", borderRadius: 16, overflow: "hidden", boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}>
        <div style={{ borderBottom: "1px solid #efefef", padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: "50%", background: "linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 700, fontSize: 16 }}>{initial}</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{selectedVendor?.handle ? `@${selectedVendor.handle}` : selectedVendor?.name || "Shop"}</div>
            <div style={{ fontSize: 12, color: "#8e8e8e" }}>Active now</div>
          </div>
        </div>
        <div style={{ height: 460, overflowY: "auto", padding: "16px 12px", display: "flex", flexDirection: "column", gap: 8 }}>
          {messages.map((msg, i) => (
            <div key={i} style={{ display: "flex", justifyContent: msg.from === "buyer" ? "flex-end" : "flex-start", alignItems: "flex-end", gap: 8 }}>
              {msg.from === "vendor" && (
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(45deg,#f09433,#bc1888)", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 11, fontWeight: 700 }}>{initial}</div>
              )}
              <MessageBubble msg={msg} initial={initial} />
            </div>
          ))}
          {loading && (
            <div style={{ display: "flex", justifyContent: "flex-start", alignItems: "flex-end", gap: 8 }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(45deg,#f09433,#bc1888)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 11, fontWeight: 700 }}>{initial}</div>
              <div style={{ background: "#efefef", padding: "10px 16px", borderRadius: "18px 18px 18px 4px", fontSize: 18, letterSpacing: 2 }}>···</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <div style={{ borderTop: "1px solid #efefef", padding: "8px 12px", display: "flex", alignItems: "center", gap: 8 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && sendMessage()}
            placeholder="Message..."
            style={{ flex: 1, border: "1px solid #dbdbdb", borderRadius: 22, padding: "8px 16px", fontSize: 14, outline: "none" }}
          />
          <button onClick={sendMessage} disabled={!input.trim() || loading} style={{ background: "none", border: "none", color: "#3797f0", fontWeight: 600, fontSize: 14, cursor: "pointer", opacity: input.trim() ? 1 : 0.4 }}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
