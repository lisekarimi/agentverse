# 🔌 MCP (Model Context Protocol) - Beginner's Guide

## ❓ What is MCP?

MCP is a **standard protocol** that connects AI agents to tools — like USB connects devices to computers.

![](https://github.com/lisekarimi/agentverse/blob/main/assets/11_mcp_archi.png?raw=true)

**Key Points:**
- It's a **connector**, not a framework
- Lets AI apps use community-built tools easily
- Value grows with adoption (like HTML for websites)

**Core Components:**
- **Host** = the app running your AI (e.g., Claude Desktop)
- **Client** = the MCP connector inside the Host
- **MCP Server** = provides the actual tools
- **Protocol** = the communication standard they all speak

## 🔗 How MCP Servers Connect: 2 Transport Types

![](https://github.com/lisekarimi/agentverse/blob/main/assets/11_mcp_transport.png?raw=true)

### 1. 💻 STDIO (Local Connection)

STDIO (Standard Input/Output) means the client and MCP server communicate locally on the same machine through stdin/stdout text messages.

**Use when:** Server runs on the same computer as your app

**How it works:**
- Host launches server as a subprocess
- They communicate through text messages (stdin/stdout)
- Messages use JSON-RPC format, one per line
- Fast and secure (no network needed)

```json
{"method":"list_tools", "id":1}
{"result":["send_message","get_data"], "id":1}
```

**Rules:**
- stdin = Client sends JSON-RPC MCP messages to server
- stdout = Server sends JSON-RPC MCP messages to client
- stderr = logs/errors only
- Each message = one line (no line breaks inside)

---

### 2. 🌐 SSE (Remote Connection)

Server-Sent Events (SSE) is a way for a remote server to send messages to the client continuously over HTTP, like a live stream of JSON messages.

**Use when:** Server is on a different computer/network

**How it works:**
- Client opens an HTTP stream to receive messages (SSE endpoint)
- Client sends requests via HTTP POST (Message endpoint)
- Server responds through the stream
- Server can push updates anytime

**Perfect for:**
- Web apps
- Remote servers
- Real-time updates

---

## ⚡ Quick Decision Guide

**Use STDIO if:**
- ✅ Everything runs locally
- ✅ Building CLI tools
- ✅ Need maximum speed/security

**Use SSE if:**
- ✅ Server is remote
- ✅ Building web apps
- ✅ Need server-initiated updates
- ✅ Working across networks

---

## 🎯 The Big Picture

**Now:** MCP doesn't change much if you already build AI tools

**Future:** MCP could become the universal standard for sharing AI tools across all apps and platforms
