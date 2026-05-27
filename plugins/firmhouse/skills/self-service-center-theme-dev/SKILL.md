---
name: self-service-center-theme-dev
description: Develop and maintain Firmhouse Customer Portal v2 templates by reading templates through GraphQL, preparing local Liquid changes, saving preview versions through the API, and publishing only after explicit approval. Use when Codex needs to fetch, edit, bootstrap, preview, or apply approved Customer Portal template files for a merchant workspace.
---

# Customer Portal v2 Theme Dev

## Overview

Use this skill to manage the Liquid templates that power the Firmhouse Customer Portal v2 for a merchant project.
Saving a template version for preview is allowed by default after local preparation. Do not publish template changes unless the latest user request explicitly asks to publish, apply, deploy, push, or otherwise update the customer-facing remote template.
Always base new edits on one of two sources: the published merchant template if one exists, otherwise the current Firmhouse default template. Do not start from a locally saved proposal, an unpublished remote draft, or a "latest" remote body. If the correct source is unclear, ask the user whether to start from the published template or the Firmhouse default.
Use the Customer Portal v2 component docs at `https://docs.firmhouse.com/self-service-center-v2/components/overview` as the main entry point for page-template and component-tag documentation.
Use Tailwind CSS v4 utility classes in template markup for styling updates.

## Prerequisites

- Work from the merchant workspace you are actively using.
- Inspect the current working directory before doing anything else.
- If the current working directory is empty or has no checked-out project files yet, stop and ask the user to initialize a git repository there before continuing.
- During that bootstrap guidance, tell the user to add `.env` to `.gitignore` and create a `.env.sample` file that documents the expected token configuration.
- Read the project access token from workspace `.env` using `FIRMHOUSE_API_TOKEN=<token>`.
- Read an optional endpoint override from workspace `.env` using `FIRMHOUSE_API_URL=<url>`.
- Default the GraphQL endpoint to `https://portal.firmhouse.com/graphql` when no override is provided.
- Treat the workspace `.env` as the only source of token and endpoint configuration; do not pass those values as script arguments.
- For saving preview versions or publishing, use a write project token. Read tokens may fail on mutations.

## First Use

On the first use of this skill in a workspace, explain the setup before attempting any GraphQL calls.

Tell the user they need to:

1. Create or obtain a Firmhouse "Customer Portal Templates Token" for the specific project they want to edit.
2. Make sure the token has write access if they want preview versions or template publishing, not just read access.
3. Ensure the workspace `.gitignore` includes `.env` so secrets are not committed.
4. Add a workspace `.env.sample` file that documents the expected token variable, for example `FIRMHOUSE_API_TOKEN=<token>`.
5. Create a workspace `.env` file with `FIRMHOUSE_API_TOKEN`.
6. Copy the relevant template files into the merchant repository themselves before making changes, then commit that baseline locally.

If the token configuration is missing, stop after explaining the setup and ask the user to add it before continuing.

## Required Workflow

Follow this sequence:

1. Inspect the current working directory first. If it is empty, follow the first-use guidance above and stop.
2. On first use in a workspace, explain the token and `.env` setup before making GraphQL calls.
3. Check the Liquid docs at `https://developer.firmhouse.com/liquid/available-tags` for relevant Liquid objects and properties.
4. Check the Customer Portal v2 docs at `https://docs.firmhouse.com/self-service-center-v2/components/overview` before planning changes.
5. Resolve the target template file from [references/available_templates.md](references/available_templates.md).
6. Fetch the starting template source. Use the published merchant template if one exists; if not, use the current Firmhouse default template for that file.
   - Do not use a local saved template file as the starting point unless it has just been verified against the published merchant template or Firmhouse default.
   - Do not use a GraphQL "latest", draft, unpublished, or pending body as the starting point.
   - If the available GraphQL helper cannot distinguish published content from unpublished content, or cannot tell whether a merchant-published template exists, ask the user whether to start from the published template or the Firmhouse default. Do not prepare edits from an ambiguous body.
7. Propose a full updated Liquid body, not a partial snippet, unless the user explicitly asks for a partial.
8. Save the updated template body into the current workspace so the user can inspect the exact proposed version.
9. Save a new remote preview version with `scripts/update_ssc_template.py` or the `saveSelfServiceCenterTemplateVersion` mutation. This is not publishing.
10. Stop after saving the preview version and report the saved version number/title. Do not publish unless the latest user request explicitly asked to publish/apply/deploy the customer-facing remote template.
11. Only after explicit publish approval, publish the chosen saved version with `scripts/publish_ssc_template_version.py` or the `publishSelfServiceCenterTemplateVersion` mutation.
    - Publishing a saved/current version must not create another version.
    - Never use `updateSelfServiceCenterTemplate` or `saveSelfServiceCenterTemplateVersion` as a fallback for a publish request; those create new versions.
    - If publishing fails with a top-level GraphQL error or HTTP 5xx, re-query the template/version state to check whether the publish completed server-side. If it did not complete, report the publish failure instead of creating a replacement version.
12. If validation errors return from GraphQL while saving, fix and retry with the full body. If validation errors return while publishing, report them against the chosen version; do not create a new version unless the user explicitly asks for a revised preview version.
13. After a successful publish, if the current workspace is a git repository, create a git commit that captures the published template change before moving on.
14. Keep the helper scripts inside this plugin; do not copy them into the merchant repository unless the user explicitly asks for that.

## Commands

### Read all templates

```bash
python3 scripts/get_ssc_template.py
```

### Read one template

```bash
python3 scripts/get_ssc_template.py \
  --template dashboard.liquid
```

Only treat this as a valid starting point when it is known to return either the published merchant template body or, when no merchant-published template exists, the Firmhouse default body. If it returns the latest editable body, any unpublished draft state, or an ambiguous body, ask the user which of the two allowed sources to use before editing.

### Save one preview version from a local file

This creates a saved project version for preview and does not publish it.

```bash
python3 scripts/update_ssc_template.py \
  --template dashboard.liquid \
  --body-file /absolute/path/to/dashboard.liquid \
  --title "Dashboard background update"
```

### Publish one saved version

Use this only after the user explicitly approves publishing the saved template body. This publishes an existing saved version by version number and must not save, update, or create another template version.

```bash
python3 scripts/publish_ssc_template_version.py \
  --template dashboard.liquid \
  --version-number 7
```

## References

- Supported templates: [references/available_templates.md](references/available_templates.md)
- GraphQL queries and mutation shape: [references/graphql_operations.md](references/graphql_operations.md)
- Customer Portal v2 component docs overview: `https://docs.firmhouse.com/self-service-center-v2/components/overview`
- Liquid object docs: `https://developer.firmhouse.com/liquid/available-tags`

## Guardrails

- Only work with supported template file names from [references/available_templates.md](references/available_templates.md).
- Do not continue from an empty workspace; ask the user to initialize the repository first.
- On first use, explain the `.env`, `.env.sample`, and token setup before making API calls.
- Keep secrets in `.env`; never write tokens into committed files.
- Do not add CLI flags for token or endpoint overrides; scripts must read configuration from workspace `.env`.
- Do not copy helper scripts into the merchant repository unless the user explicitly asks for that.
- Before making local edits, confirm the starting body is the published merchant template or the Firmhouse default. If source status is ambiguous, ask the user which of those two sources to use.
- Never start a new change from a previous local proposal, cached file, or unpublished remote latest/draft body.
- Save preview versions with `saveSelfServiceCenterTemplateVersion`; this is allowed without separate approval after preparing the local body.
- Never call `publishSelfServiceCenterTemplateVersion` merely because the user asked to change, edit, update, tweak, style, or customize a template. Treat those as local preparation plus preview-version requests unless the latest user request explicitly says to publish/apply/deploy the customer-facing remote template.
- Never use `updateSelfServiceCenterTemplate` or `saveSelfServiceCenterTemplateVersion` to satisfy a request to publish a specific/current saved version. Publishing must use `publishSelfServiceCenterTemplateVersion` for the existing version number and must not create a new version.
- Publishing saved versions does not send a template body. Only send full template bodies when saving preview versions.
- Use Tailwind CSS v4 classes for styling changes.
- Use the Customer Portal v2 component docs and Liquid docs before guessing at available tags, objects, or properties.
