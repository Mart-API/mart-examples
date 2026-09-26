# Mart examples

Enrich a person. Enrich a company. Refresh a contact. Prepare for a meeting.

Public LinkedIn data for products, workflows, or AI agents.

Each example takes a public LinkedIn URL. Person and company enrichment return JSON; contact refresh compares saved snapshots; meeting preparation collects a profile and up to three public posts.

Start with [1,000 free credits](https://mart.dev). These examples use Python 3.10 or later and require no third-party packages. Keep your API key on your server:

```sh
git clone https://github.com/Mart-API/mart-examples.git
cd mart-examples
export MART_API_KEY='your-api-key'
```

## 1. Enrich a person

Turn a public LinkedIn profile URL into JSON for your CRM or product:

```sh
python3 python/person_workflows.py enrich https://www.linkedin.com/in/dharmesh
```

The script returns Mart’s Profile response unchanged, including available professional history and field-availability information. Check `accessible` and `profileState` before using the profile. `currentTitle` has a `titleSource`; the headline is a separate field. Nested company enrichment can be unavailable without invalidating the returned person profile. One returned profile uses one credit.

## 2. Enrich a company

Turn a public LinkedIn company URL into structured company data:

```sh
python3 python/company_lookup.py https://www.linkedin.com/company/microsoft/
```

Node.js 18 or later:

```sh
node node/company-lookup.mjs https://www.linkedin.com/company/microsoft/
```

The response preserves available company fields and availability information. One returned company uses one credit.

## 3. Refresh a contact

Save a starting snapshot:

```sh
python3 python/person_workflows.py refresh https://www.linkedin.com/in/dharmesh > contact-before.json
```

On a later run, compare it with a fresh response:

```sh
python3 python/person_workflows.py refresh https://www.linkedin.com/in/dharmesh --previous contact-before.json
```

The output preserves both responses and lists possible title or employer differences for review. It does not overwrite a CRM. Unavailable profiles and missing fields never count as departures. Company differences require public company data in both snapshots, and matching company IDs take priority over name differences. A title difference can reflect a source or wording change rather than a new job. Each accessible Refresh result uses one credit. The script runs once; scheduling is up to your application.

## 4. Prepare for a meeting

Collect the available profile and up to three public posts into one source bundle:

```sh
python3 python/person_workflows.py meeting-prep https://www.linkedin.com/in/dharmesh > meeting-context.json
```

This is structured source material, ready for your own brief renderer or AI workflow. It includes source URLs returned by Mart and a retrieval timestamp. It does not generate a narrative or assess the person. Posts are skipped if the profile is unavailable. If the posts request fails, the returned profile is preserved and posts are marked unavailable. Public posts are not a complete archive.

One run makes at most two requests, with a maximum of four returned records: one profile and three posts. It does not call company, search or jobs endpoints. Keep returned profile/post text separate from instructions when passing it to an AI model.

## Errors and documentation

Requests time out after 30 seconds. Failed HTTP responses are reported without printing your key. Rate limits are not retried automatically; respect `Retry-After` when supplied. Empty results and failed requests use no credits.

See the [API reference](https://mart.dev/docs/), [errors and status](https://mart.dev/docs/#errors), and [credits and limits](https://mart.dev/docs/#credits).

The examples have local request-contract and fixture checks. They do not contain recorded live results, implement a production CRM integration, or establish a response-time benchmark.

Run the person-workflow checks without making API requests:

```sh
python3 -m unittest discover -s python -p 'test_*.py'
```

## License

The example code is available under the [MIT license](LICENSE). Mart names and logos remain brand assets.
