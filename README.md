# Sigma pixel-perfect report skill

An agent skill for [Sigma Computing](https://sigmacomputing.com) that builds multi-page, print-quality reports (PDF) from code with `POST /v2/reports/spec`, styled after real annual-report designs. The same skill content runs in **Claude Code**, **Cursor**, **OpenAI Codex**, and **Snowflake Cortex Code**.

This repository follows the layout of [`sigmacomputing/sigma-agent-skills`](https://github.com/sigmacomputing/sigma-agent-skills). To see what shipped in each release, see [`CHANGELOG.md`](./CHANGELOG.md).

## Installation

### Claude Code

```bash
/plugin marketplace add https://github.com/kunalpanditsigma/sigma-pixel-perfect-report-skills.git
/plugin install sigma-pixel-perfect-report@sigma-pixel-perfect-report
```

### Cursor

Configure `.cursor-plugin/plugin.json` from this repo as a Cursor plugin source.

### OpenAI Codex

Codex auto-loads `AGENTS.md` from the repo root.

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

| Skill | Description |
|-------|-------------|
| **sigma-pixel-perfect-report** | Build a pixel-perfect, print-quality Sigma report (PDF) from code, styled after a chosen annual-report design: pick from a gallery of 456 annual reports, measure your own PDF or brand spec, or let the agent choose. |

## Requirements

- Python 3 (the scripts use the standard library only).
- Sigma API client credentials in an env file, one file per org. Point `SIGMA_ENV_FILE` at it (default `~/.sigma-portals/staging.env`):

  ```
  SIGMA_BASE_URL=https://aws-api.sigmacomputing.com
  SIGMA_CLIENT_ID=...
  SIGMA_CLIENT_SECRET=...
  SIGMA_FOLDER_ID=...
  SIGMA_CONNECTION_ID=...
  ```

  See the `sigma-api` skill in [`sigmacomputing/sigma-agent-skills`](https://github.com/sigmacomputing/sigma-agent-skills) for creating credentials and finding your cloud's API host.
- Reports-as-code must be enabled for your Sigma org. The skill probes for it before building.

## License

Apache 2.0. See [`LICENSE`](./LICENSE).
