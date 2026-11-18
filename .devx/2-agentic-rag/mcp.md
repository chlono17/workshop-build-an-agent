<div class="dx-hero" data-eyebrow="MODULE 02 / 04 - MCP" data-title="Implementing MCP" data-meta="TIME::35 min|CONCEPTS::4|EXERCISES::3"></div>

The Model Context Protocol (MCP) is an open standard introduced by Anthropic for connecting applications to tools, data sources, and services through compatible servers.

In this lesson, we'll explore what MCP is, why it matters, and how it transforms the way we build agent capabilities.

<!-- fold:break -->

<div class="dx-island dx-reveal">
  <p class="dx-island-title">THE TOOL PROBLEM</p>
  <p>In the previous sections, you built tools directly into your agent - the Module 1 search tool and the RAG retriever were Python functions in your codebase. That works, but it has limits:</p>
  <p><span class="dx-chip">TIGHT COUPLING</span> Tools live inside your agent's code.</p>
  <p><span class="dx-chip">DUPLICATION</span> Every agent project rebuilds the same integrations.</p>
  <p><span class="dx-chip">NO ECOSYSTEM</span> Hard to share and reuse tools across projects.</p>
  <p>What if tools could be developed, shared, and connected independently of any specific agent?</p>
</div>

<!-- fold:break -->

## Enter MCP

MCP solves this by standardizing how agents communicate with external capabilities. Instead of building tools into your agent, you connect to **MCP Servers** that expose tools, resources, and prompts.

<center>

| Traditional Tools | MCP Approach |
|-------------------|--------------|
| Tools bundled in agent code | Tools run as separate services |
| One-off implementations | Reusable across any MCP client |
| Hardcoded integrations | Discoverable at runtime |

</center>

<!-- fold:break -->

### MCP Architecture

<img src="_static/robots/datacenter.png" alt="Architecture Robot" style="float:right;max-width:300px;margin:25px;" />

MCP follows a client-server model:

- **MCP Hosts** — Applications like Claude Desktop, Cursor, or your custom agent
- **MCP Clients** — Protocol handlers that maintain connections to servers  
- **MCP Servers** — Lightweight services that expose tools, resources, and prompts

The protocol defines three core primitives:

1. **Tools** — Functions the model can invoke (like our search tool)
2. **Resources** — Data an application can read and include in model context
3. **Prompts** — Reusable templates users can select through the host application

<!-- fold:break -->

### Why MCP Matters

MCP is transforming the agent ecosystem:

<div class="dx-bento dx-reveal">
  <div class="dx-cell"><h4>FOR DEVELOPERS</h4>Build a tool once, use it everywhere. Tap a growing library of pre-built MCP servers. Standardized patterns cut boilerplate.</div>
  <div class="dx-cell"><h4>FOR ORGANIZATIONS</h4>Consistent integrations across teams. Hosts still need authorization, appropriate permissions, and approval rules.</div>
  <div class="dx-cell is-wide"><h4>FOR THE ECOSYSTEM</h4>Open-source MCP servers for databases, APIs, and file systems; commercial servers for enterprise; a shared language for agent capabilities.</div>
</div>

<!-- fold:break -->

### MCP in Practice

You use MCP when a host is configured to connect to an MCP server, for example:

- **Claude Desktop** connected to a filesystem MCP server
- **Cursor** configured with an external MCP server
- **Custom integrations** via the MCP SDK

Built-in browser or terminal tools do not by themselves establish that MCP is involved.

The tools appear seamlessly in the model's context, ready to be invoked when needed, just like the ReAct pattern you learned earlier.

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">You connect your agent to an MCP server for search (in this fork, <code>mcp_server.py</code>; upstream, Tavily's hosted server). Where does the search tool's code actually run?</p>
  <button class="dx-quiz-opt" data-fb="That's the pre-MCP approach - bundling the tool's implementation into your agent's codebase. MCP exists precisely to decouple the two.">Inside your agent's process, after MCP copies the tool code into it</button>
  <button class="dx-quiz-opt" data-right data-fb="Right. The tool lives and runs on the MCP server (here, the separate <code>mcp_server.py</code> process; upstream, Tavily's hosted one); your agent just discovers and calls it over the protocol. Build once, use anywhere.">On the MCP server; your agent discovers and calls it over the protocol</button>
  <button class="dx-quiz-opt" data-fb="The LLM never executes tool code - it only requests a call. With MCP, the MCP server runs the tool, not the model.">The LLM runs it directly as part of generating its response</button>
</div>

<!-- fold:break -->

## MCP: A Hands-On Implementation

<img src="_static/robots/magician.png" alt="MCP Magic Robot" style="float:right;max-width:300px;margin:25px;" />

Your RAG agent is great for answering questions from the knowledge base. Now let's **add a second search tool** that lives outside the agent, using the MCP pattern.

> **Local-first fork.** There is no internet search here. The MCP server is `mcp_server.py`, running on this machine: it exposes one tool, `tavily_search`, that does a keyword (BM25) search over the same IT documents, with no key and no internet. The tool keeps Tavily's name and input so the code is identical in both modes. With `WORKSHOP_SEARCH=tavily` in `variables.env` (and a Tavily key), the same code connects to Tavily's hosted MCP server and searches the web instead.

1. **Streamable HTTP** — Connect to the MCP server at `MCP_URL` (locally `http://localhost:8002/mcp/`; hosted mode `https://mcp.tavily.com/mcp/`).
2. **SSE (optional)** — Connect to the same local server over the older SSE transport.

We'll see how to do both. 

<!-- fold:break -->

### The Goal

<img src="_static/robots/MCP.png" alt="MCP Robot Character" style="float:right;max-width:300px;margin:25px;" />

Right now your agent only has one tool:
- `company_llc_it_knowledge_base` — Internal IT policies

We're going to add:
- `web_search` — Search through the MCP server (local documents by keyword in this fork; the web in hosted mode)

**Same agent, more capabilities.**

<!-- fold:break -->

### Your Exercises

First, start the MCP server in a new <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> and leave it running (hosted Tavily mode skips this step):

```bash
cd code/2-agentic-rag && uvicorn mcp_server:app --port 8002
```

Take a look at <button onclick="goToLineAndSelect('code/2-agentic-rag/mcp_server.py', 'mcp_server =');"><i class="fas fa-code"></i> mcp_server.py</button>: `list_tools()` advertises the tool and its input schema; `call_tool()` runs it. **Workshop Health** shows *MCP search server* as running once it is up.

Then open <button onclick="openOrCreateFileInJupyterLab('code/2-agentic-rag/rag_agent.py');"><i class="fa-brands fa-python"></i> code/2-agentic-rag/rag_agent.py</button> and fill in these blanks in the **MCP section**:

#### Exercise: Configure the MCP Connection

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'MCP_CONFIG = ');"><i class="fas fa-code"></i> MCP_CONFIG</button> — Configure the MCP client to connect to the MCP server using Streamable HTTP, under the name `tavily` (the name `client.session(...)` opens).

The configuration section above already sets `MCP_URL` and `MCP_HEADERS` for your mode. Locally the server is your own process on `localhost`, so `MCP_HEADERS` is empty. In hosted mode it carries the Tavily key in an Authorization header, as supported by [Tavily's MCP server](https://github.com/tavily-ai/tavily-mcp#remote-mcp-server). This keeps the key out of request URLs and subprocess arguments.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
MCP_CONFIG = {
    "tavily": {
        "transport": "streamable_http",
        "url": MCP_URL,
        "headers": MCP_HEADERS,
    }
}
```

Locally this connects to `http://localhost:8002/mcp/` with no key. In hosted mode the same dict connects to Tavily's server, and the key travels in the `Authorization` header, never in the URL, where it could end up in logs and browser history.

</details>

<!-- fold:break -->

#### Exercise: Call the Search Tool via MCP

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'result = ...');"><i class="fas fa-code"></i> result</button> — Inside `web_search()`, call the server's `tavily_search` tool through the MCP client.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
result = await session.call_tool("tavily_search", {"query": query})
```

The `session.call_tool()` method invokes the `tavily_search` tool on the MCP server with your query. The search itself runs in the server process (watch its terminal print `Executing search for: ...`), not in your agent.

</details>

<!-- fold:break -->

#### Exercise: Give New Tool to Agent

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'AGENT =');"><i class="fas fa-code"></i> AGENT</button> — Update the `AGENT` definition to include your new tool alongside the existing one.

In addition to the `RETRIEVER_TOOL` you implemented previously, also add in `web_search` you just built. This replaces your earlier definition — we're expanding the agent's toolkit.

<details class="dx-peek is-solution">
<summary>🆘  Need some help?</summary>

```python
AGENT = create_react_agent(
    model=llm,
    tools=[RETRIEVER_TOOL, web_search],
    prompt=SYSTEM_PROMPT,
)
```

</details>

<!-- fold:break -->

### What This Enables

After filling in these blanks, your agent can now differentiate between the following queries:

<div class="dx-term dx-reveal">
  <span class="dx-term-title">rag_agent</span>
  <span class="dx-term-line" data-kind="prompt">How do I reset my password?</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">Internal IT policy - the knowledge base should have this.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[action] company_llc_it_knowledge_base("reset password")</span>
  <span class="dx-term-line" data-kind="answer" data-delay="350">...follow the self-service reset steps. [KB:source_id]</span>
  <span class="dx-term-line" data-kind="prompt" data-delay="500">Which document mentions "MFA" and "VPN" together?</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">An exact-words lookup - the keyword search tool fits.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[action] web_search("MFA VPN")</span>
  <span class="dx-term-line" data-kind="answer" data-delay="350">...the VPN guide... (file://data/it-knowledge-base/vpn.md)</span>
</div>

The agent decides which tool to use based on the question! (In hosted Tavily mode, a question about current events goes to `web_search` and comes back with web URLs.)

<!-- fold:break -->

## Test Your Agent

After completing the exercises, restart your agent in the <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button>:

Make sure you're in the `code/2-agentic-rag` directory:

```bash
cd code/2-agentic-rag
```

And start your Agent API with the LangGraph CLI.

```bash
langgraph dev
```

In the <button onclick="launch('Simple Agents Client');"><i class="fa-solid fa-rocket"></i> Simple Agents Client</button>, try:

- "How do I connect to VPN?" → Should use [KB:source_id]
- "Use web_search to find which document covers distribution lists." → Should call `web_search` and cite a `file://` URL (the MCP server's terminal logs the search)
- Hosted Tavily mode only: "What's happening in AI news today?" → Should use web URLs

If `web_search` answers *Is the local MCP server running?*, start it as shown above.

Wow! Remember that custom search tool implementation from Module 1? Now, we can eliminate the need for that by decoupling the tool from the agent. Build once, use anywhere - That's the value of MCP!

<!-- fold:break -->

#### (Optional) Exercise: Connect over SSE

MCP servers can speak more than one transport. Your local server also serves the older SSE transport at `/sse`. Let's connect to it that way.

Take a look at the local MCP server implementation in the <button onclick="goToLineAndSelect('code/2-agentic-rag/mcp_server.py', 'mcp_server =');"><i class="fas fa-code"></i> mcp_server.py</button> file: one `Server`, two transports mounted on the same port.

Make sure the MCP server is running in a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> window (`--reload` restarts it when you edit the file). In hosted Tavily mode it wraps Tavily web search and needs your Tavily key.

```bash
cd code/2-agentic-rag && uvicorn mcp_server:app --reload --port 8002
```

In <button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', '# PART 2B');"><i class="fas fa-code"></i> # PART 2B</button> of ``rag_agent.py`` do the following: 

1. Comment out `PART 2A`
2. Uncomment `PART 2B`. Save the file.
3. Restart the RAG agent: `cd code/2-agentic-rag && langgraph dev`
4. Test the agent in the Simple Agents Client. 

Responses should now use the tool on your locally running MCP server, over SSE. 

<!-- fold:break -->

## What's Next

<img src="_static/robots/hiking.png" alt="Journey Robot" style="float:right;max-width:300px;margin:25px;" />

Congrats, you now know how to leverage MCP to integrate standardized tooling into your AI agents! 

In this section, you learned how to: 

- **Connect MCP servers over Streamable HTTP** (your local one, or a hosted one like Tavily's)
- **Connect MCP servers over SSE**
- **Explore how MCP servers are built** to expose custom tools

Now that you understand what MCP is, why it matters, and how to implement it in code, you're ready to explore further. 

Continue to [Agent Skills](skills.md) to learn about how to impart your agent with custom defined skills to better align its tool calling. 
