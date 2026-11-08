# Sigma pixel-perfect report skill

An agent skill for [Sigma Computing](https://sigmacomputing.com). The same skill content runs in Claude Code, Cursor, OpenAI Codex, and Snowflake Cortex Code.

## Installation

### Claude Code

```
/plugin marketplace add https://github.com/kunalpanditsigma/sigma-pixel-perfect-report-skills.git
/plugin install sigma-pixel-perfect-report@sigma-pixel-perfect-report
```

### Cursor

Configure `.cursor-plugin/plugin.json` from this repo as a Cursor plugin source.

### OpenAI Codex

Codex auto-loads this `AGENTS.md` and the `skills/` directory from the repo root.

### Snowflake Cortex Code

Inside a Cortex Code session:

```
/skill add https://github.com/kunalpanditsigma/sigma-pixel-perfect-report-skills.git
```

To update to the latest version:

```
/skill sync
```

## Skills

Agents activate this automatically based on the user's request.

- **sigma-pixel-perfect-report** — Build a pixel-perfect, print-quality Sigma report (PDF) from code via `POST /v2/reports/spec`, styled after a chosen annual-report design.

See [`README.md`](./README.md) for full details.
