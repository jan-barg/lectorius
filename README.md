# lectorius

interactive audiobook app that answers your questions without spoilers

## status

work in progress

## structure
```
apps/web/       # sveltekit frontend (coming soon)
pipeline/       # python data pipeline
docs/           # specifications
books/          # pipeline output (gitignored)
```

## docs

- [prd](docs/prd.md)
- [pipeline spec](docs/pipeline.md)
- [system architecture](docs/architecture.md)
- [data model](docs/data-model.md)
- [api spec](docs/api-spec.md)
- [playback state machine](docs/playback-state-machine.md)
- [llm prompts](docs/llm-prompts.md)

## setup
```bash
# pipeline
cd pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## license

mit