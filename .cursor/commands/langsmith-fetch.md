
# LangSmith Fetch - Agent Debugging Skill

Debug LangChain and LangGraph agents by fetching execution traces directly from LangSmith Studio.

## Prerequisites

```bash
pip install langsmith-fetch
export LANGSMITH_API_KEY="your_langsmith_api_key"
export LANGSMITH_PROJECT="your_project_name"
```

## Quick Reference

```bash
# Quick debug
langsmith-fetch traces --last-n-minutes 5 --limit 5 --format pretty

# Specific trace
langsmith-fetch trace <trace-id> --format pretty

# Export session
langsmith-fetch traces ./debug-session --last-n-minutes 30 --limit 50

# Find errors
langsmith-fetch traces --last-n-minutes 30 --limit 50 --format raw | grep -i error

# With metadata
langsmith-fetch traces --limit 10 --include-metadata
```

## Notes

- Always check if `langsmith-fetch` is installed before running commands
- Verify environment variables are set
- Use `--format pretty` for human-readable output, `--format json` for analysis
- When exporting, create organized folder structures
- Always provide clear analysis and actionable insights

## Reference Files

- **`references/workflows.md`** — 4 core workflows: quick debug, deep dive trace, export session, error detection. Load when starting a debug session.
- **`references/use-cases-troubleshooting.md`** — Common use cases (agent not responding, wrong tool, memory issues, performance), advanced features, output formats, troubleshooting, best practices. Load when investigating specific issues.
