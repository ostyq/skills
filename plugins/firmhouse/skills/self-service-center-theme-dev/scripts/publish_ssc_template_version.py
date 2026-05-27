#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

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
    parser = argparse.ArgumentParser(
        description="Publish an existing Firmhouse Customer Portal v2 template version through GraphQL."
    )
    parser.add_argument("--template", required=True, help="Template file name, e.g. dashboard.liquid")
    parser.add_argument("--version-number", required=True, type=int, help="Existing saved version number to publish")
    return parser.parse_args()


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

    mutation = (
        "mutation PublishSelfServiceCenterTemplateVersion($templateFileName: String!, $versionNumber: Int!) { "
        "publishSelfServiceCenterTemplateVersion(input: { templateFileName: $templateFileName, versionNumber: $versionNumber }) { "
        "errors { attribute message } "
        "selfServiceCenterTemplateVersion { id versionNumber title published createdAt } "
        "} }"
    )
    variables = {
        "templateFileName": args.template,
        "versionNumber": args.version_number,
    }

    try:
        response = post_graphql(endpoint, token, mutation, variables)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1

    print(json.dumps(response, indent=2))

    top_level_errors = response.get("errors") or []
    mutation_payload = ((response.get("data") or {}).get("publishSelfServiceCenterTemplateVersion") or {})
    validation_errors = mutation_payload.get("errors") or []

    if top_level_errors:
        print("GraphQL returned top-level errors. Re-query template state before retrying.", file=sys.stderr)
        return 2
    if validation_errors:
        print("Template publish errors were returned.", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
