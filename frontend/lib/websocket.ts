const API = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export function connectPolarisSocket(
  onMessage: (data: unknown) => void
): WebSocket | null {
  if (typeof window === "undefined") return null;
  try {
    const ws = new WebSocket(API);
    ws.onmessage = (ev) => {
      try {
        onMessage(JSON.parse(ev.data));
      } catch {
        onMessage(ev.data);
      }
    };
    return ws;
  } catch {
    return null;
  }
}
