# Heat and hot-water review demo

This demo shows how a housing-enforcement supervisor could review heat and
hot-water building signals with Strategy. It is not an official city service.

## Working data path

```text
NYC Open Data
    -> Azure ingestion
    -> ADLS Gen2
    -> Strategy Mosaic
    -> Strategy dashboard
    -> review worklist
```

ADLS Gen2 stores stable current files and dated archive files. Strategy's
Azure Data Lake Storage Gen2 file-storage connector imports those files. Mosaic
owns attributes, relationships, measures, hierarchies, and the saved refresh.

Power BI is not part of the final architecture.

## Run locally

```bash
make install
make dev
```

The browser app starts at `http://localhost:5173`. The API starts at
`http://127.0.0.1:8000`.

## Prepare and upload data

```bash
make ingest-local
make ingest
```

`make ingest` requires `ADLS_ACCOUNT_URL` and uses managed identity or the
signed-in Azure CLI identity. It never uses a storage key.

## Check the code

```bash
make lint
make test
```

## Documentation

See [docs/README.md](docs/README.md).

## Live demo

The production app is available at
[https://strategy-heat.eps-demos.site](https://strategy-heat.eps-demos.site).
Azure Container Apps provides managed HTTPS.
