
# MCP Server Development Guide

Create high-quality MCP servers that enable LLMs to interact with external services. The quality of an MCP server is measured by how well it enables LLMs to accomplish real-world tasks using the tools provided.

## High-Level Workflow

| Phase | Purpose |
|-------|---------|
| **1. Deep Research & Planning** | Internalize agent-centric design principles, study MCP/SDK/API docs, create implementation plan |
| **2. Implementation** | Set up project, build shared infra, implement tools systematically |
| **3. Review & Refine** | Code quality review, test/build, run quality checklist |
| **4. Create Evaluations** | Write 10 complex evaluation questions to validate agent effectiveness |

For Phase 2-4 details, see [Implementation Guide](./reference/implementation-guide.md).


## Phase 1: Deep Research and Planning

### 1.1 Agent-Centric Design Principles

**Build for Workflows, Not Just API Endpoints:**
- Don't simply wrap existing API endpoints - build thoughtful, high-impact workflow tools
- Consolidate related operations (e.g., `schedule_event` that both checks availability and creates event)
- Focus on tools that enable complete tasks, not just individual API calls

**Optimize for Limited Context:**
- Agents have constrained context windows - make every token count
- Return high-signal information, not exhaustive data dumps
- Provide "concise" vs "detailed" response format options
- Default to human-readable identifiers over technical codes (names over IDs)

**Design Actionable Error Messages:**
- Error messages should guide agents toward correct usage patterns
- Suggest specific next steps: "Try using filter='active_only' to reduce results"
- Help agents learn proper tool usage through clear feedback

**Follow Natural Task Subdivisions:**
- Tool names should reflect how humans think about tasks
- Group related tools with consistent prefixes for discoverability

**Use Evaluation-Driven Development:**
- Create realistic evaluation scenarios early
- Let agent feedback drive tool improvements
- Prototype quickly and iterate based on actual agent performance

### 1.2 Study MCP & Framework Documentation

Fetch the latest MCP spec via WebFetch: `https://modelcontextprotocol.io/llms-full.txt`, then load:

- [MCP Best Practices](./reference/mcp_best_practices.md) - Core guidelines for all MCP servers
- **Python**: Fetch SDK README from `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`, then load [Python Guide](./reference/python_mcp_server.md)
- **TypeScript**: Fetch SDK README from `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`, then load [TypeScript Guide](./reference/node_mcp_server.md)

### 1.3 Study API Documentation

Read through **ALL** available API documentation for the target service: endpoints, auth, rate limits, pagination, error responses, and data models. Use web search and WebFetch as needed.

### 1.4 Create Implementation Plan

Plan should cover: tool selection and prioritization, shared utilities/helpers, input/output design (validation models, response formats, truncation), and error handling strategy.


## Reference Files

| Resource | Path |
|----------|------|
| MCP Best Practices | [reference/mcp_best_practices.md](./reference/mcp_best_practices.md) |
| Python Implementation Guide | [reference/python_mcp_server.md](./reference/python_mcp_server.md) |
| TypeScript Implementation Guide | [reference/node_mcp_server.md](./reference/node_mcp_server.md) |
| Evaluation Guide | [reference/evaluation.md](./reference/evaluation.md) |
| Implementation Guide (Phases 2-4) | [reference/implementation-guide.md](./reference/implementation-guide.md) |
