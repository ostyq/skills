#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from env_utils import load_dotenv

DEFAULT_GRAPHQL_ENDPOINT = "https://portal.firmhouse.com/graphql"


def resolve_token() -> str:
    token = os.getenv("FIRMHOUSE_API_TOKEN")
    if token:
        return token.strip()

    raise ValueError("Missing Firmhouse API token. Set FIRMHOUSE_API_TOKEN in workspace .env.")


def resolve_endpoint() -> str:
    return os.getenv("FIRMHOUSE_API_URL") or DEFAULT_GRAPHQL_ENDPOINT


def post_graphql(endpoint: str, token: str, query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Project-Access-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {body}") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Firmhouse Customer Portal v2 templates through GraphQL.")
    parser.add_argument("--template", help="Template file name, e.g. dashboard.liquid")
    parser.add_argument(
        "--write-to-dir",
        help="Optional directory where fetched template body files should be written",
    )
    return parser.parse_args()


def ensure_output_dir(path: str) -> Path:
    output_dir = Path(path).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_templates(output_dir: Path, templates: list[dict]) -> None:
    for template in templates:
        file_name = template["templateFileName"]
        body = template.get("body") or ""
        target = output_dir / file_name
        target.write_text(body, encoding="utf-8")


def main() -> int:
    args = parse_args()
    load_dotenv()

    try:
        token = resolve_token()
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1

    endpoint = resolve_endpoint()
    if not endpoint:
        print("Missing GraphQL endpoint.", file=sys.stderr)
        return 1

    if args.template:
        query = (
            "query SelfServiceCenterTemplate($templateFileName: String!) { "
            "selfServiceCenterTemplate(templateFileName: $templateFileName) { "
            "id templateFileName body createdAt updatedAt "
            "} }"
        )
        variables = {"templateFileName": args.template}
    else:
        query = (
            "query SelfServiceCenterTemplates { "
            "selfServiceCenterTemplates { id templateFileName body createdAt updatedAt } "
            "}"
        )
        variables = {}

    try:
        response = post_graphql(endpoint, token, query, variables)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.write_to_dir:
        output_dir = ensure_output_dir(args.write_to_dir)
        if args.template:
            template = (response.get("data") or {}).get("selfServiceCenterTemplate")
            if not template:
                print(json.dumps(response, indent=2))
                print("Template not found in GraphQL response.", file=sys.stderr)
                return 2
            write_templates(output_dir, [template])
        else:
            templates = (response.get("data") or {}).get("selfServiceCenterTemplates") or []
            write_templates(output_dir, templates)

    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
