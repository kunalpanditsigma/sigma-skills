# Sigma report and workbook skills

Agent skills for [Sigma Computing](https://sigmacomputing.com): pixel-perfect, print-quality reports built from code, field-tested rules for building workbooks and data apps through the REST API, and a recipe for custom plugins. The same skill content runs in **Claude Code**, **Cursor**, **OpenAI Codex**, and **Snowflake Cortex Code**.

This repository follows the layout of [`sigmacomputing/sigma-agent-skills`](https://github.com/sigmacomputing/sigma-agent-skills). To see what shipped in each release, see [`CHANGELOG.md`](./CHANGELOG.md).

## Installation

### Claude Code

```bash
/plugin marketplace add https://github.com/kunalpanditsigma/sigma-skills.git
/plugin install sigma-skills@sigma-skills
```

### Cursor

Configure `.cursor-plugin/plugin.json` from this repo as a Cursor plugin source.

### OpenAI Codex

Codex auto-loads `AGENTS.md` from the repo root.

### Snowflake Cortex Code

Inside a Cortex Code session:

```
/skill add https://github.com/kunalpanditsigma/sigma-skills.git
```

To update to the latest version:

```
/skill sync
```

## Skills

Agents activate these automatically based on the user's request.

| Skill | Description |
|-------|-------------|
| **sigma-pixel-perfect-report** | Build a pixel-perfect, print-quality Sigma report (PDF) from code, styled after a chosen annual-report design: pick from a gallery of 456 annual reports, measure your own PDF or brand spec, or let the agent choose. |
| **sigma-workbook-field-notes** | Field-tested rules and API gotchas for building and editing Sigma workbooks from code: spec shapes that verify but render wrong, formulas and sources, input tables and write-back actions, forms, agents, plugins, embedding, and QA without warehouse reads. Use alongside the `sigma-workbooks` skill in [`sigmacomputing/sigma-agent-skills`](https://github.com/sigmacomputing/sigma-agent-skills). |
| **sigma-plugins** | Design, build, host, register and wire custom Sigma plugins (maps, Sankeys, percentile bars, heat maps, canvas scenes) with the `@sigmacomputing/plugin` SDK. Includes a tested starter template, a local test harness, and a catalogue of plugin patterns. |

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
