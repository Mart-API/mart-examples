# Mart examples

Public LinkedIn data for products, workflows and AI agents.

These small examples fetch a company through the [Mart API](https://mart.dev/docs/). Start with [1,000 free credits](https://mart.dev/signup/?utm_source=github&utm_medium=referral&utm_campaign=mart_examples).

## Company lookup

Keep your API key on your server. Set it as an environment variable in your shell or secret manager:

```sh
export MART_API_KEY='your-api-key'
```

Python 3.10 or later, no third-party dependencies:

```sh
python3 python/company_lookup.py https://www.linkedin.com/company/microsoft/
```

Node.js 18 or later, no third-party dependencies:

```sh
node node/company-lookup.mjs https://www.linkedin.com/company/microsoft/
```

The scripts make one request and print the returned JSON unchanged. Check `accessible` before using the company fields. Missing fields do not establish that a company lacks that attribute. A returned company uses one credit; an empty result or failed request uses none.

Requests time out after 30 seconds. A non-success HTTP response exits with an error. Rate limits are not retried automatically; wait for the server’s `Retry-After` interval when supplied. See [errors and status](https://mart.dev/docs/#errors) and [credits and limits](https://mart.dev/docs/#credits).

## More workflows

Mart also supports public profiles, posts, jobs, people search, company search and profile refresh. Choose the operation and filters in the [API reference](https://mart.dev/docs/). Search and Jobs use stored public data; consult the endpoint notes for field and freshness behavior.

Support: [support@mart.dev](mailto:support@mart.dev).

## Local verification

These examples were checked against the current request contract and exercised with mocked success, authentication, HTTP error and timeout responses. This repository does not contain recorded live results or promise a response-time benchmark.
