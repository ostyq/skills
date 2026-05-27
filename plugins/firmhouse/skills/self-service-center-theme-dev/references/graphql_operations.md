# GraphQL Operations for Customer Portal v2 Templates

Endpoint:
- `POST /graphql`

Authentication header:
- `X-Project-Access-Token: <token>`

Token guidance:
- Use a write project token for `saveSelfServiceCenterTemplateVersion` and `publishSelfServiceCenterTemplateVersion`.
- Read-only token usage depends on access policy and should be treated as query-only.

## Query: list templates

```graphql
query SelfServiceCenterTemplates {
  selfServiceCenterTemplates {
    id
    templateFileName
    body
    createdAt
    updatedAt
  }
}
```

## Query: fetch one template

Use query results as an editing starting point only when they are known to return one of two allowed sources: the published merchant template body, or the Firmhouse default body when no merchant-published template exists. If the field returns the latest editable version, an unpublished draft, or an ambiguous body, ask the user whether to start from the published template or the Firmhouse default before editing.

```graphql
query SelfServiceCenterTemplate($templateFileName: String!) {
  selfServiceCenterTemplate(templateFileName: $templateFileName) {
    id
    templateFileName
    body
    createdAt
    updatedAt
  }
}
```

Variables example:

```json
{
  "templateFileName": "dashboard.liquid"
}
```

## Mutation: save preview version

Creates a saved version that can be previewed in the project. This does not publish it to customer-facing rendering.

```graphql
mutation SaveSelfServiceCenterTemplateVersion($templateFileName: String!, $body: String!, $title: String) {
  saveSelfServiceCenterTemplateVersion(
    input: {
      templateFileName: $templateFileName,
      body: $body,
      title: $title
    }
  ) {
    errors {
      attribute
      message
    }
    selfServiceCenterTemplateVersion {
      id
      versionNumber
      title
      published
      createdAt
    }
  }
}
```

Variables example:

```json
{
  "templateFileName": "dashboard.liquid",
  "body": "{% latest_orders %}\n{% product_listing %}",
  "title": "Dashboard background update"
}
```

## Mutation: publish saved version

Use only after the user explicitly approves publishing a saved version.
This mutation publishes an existing version by `versionNumber`; it must not create a new version or send a template body. Do not use `updateSelfServiceCenterTemplate` or `saveSelfServiceCenterTemplateVersion` as a fallback for publishing a specific/current version. If this mutation returns an HTTP 5xx or top-level GraphQL error, re-query the template/version state to determine whether the publish completed server-side; if not, report the failure.

```graphql
mutation PublishSelfServiceCenterTemplateVersion($templateFileName: String!, $versionNumber: Int!) {
  publishSelfServiceCenterTemplateVersion(
    input: {
      templateFileName: $templateFileName,
      versionNumber: $versionNumber
    }
  ) {
    errors {
      attribute
      message
    }
    selfServiceCenterTemplateVersion {
      id
      versionNumber
      title
      published
      createdAt
    }
  }
}
```

Variables example:

```json
{
  "templateFileName": "dashboard.liquid",
  "versionNumber": 7
}
```
