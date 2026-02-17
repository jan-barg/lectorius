# lectorius

interactive audiobook app that answers your questions without spoilers

## status

work in progress 
— pipeline (all stages 1-7) is functional, tested on gutenberg epubs.
- audio playback works, Q&A flow functional

## structure
```
apps/web/       # sveltekit frontend (coming soon)
pipeline/       # python data pipeline (epub → book packs)
docs/           # specifications
source/         # source epub files
books/          # pipeline output (audio files gitignored due to size)
```

## pipeline quickstart

```bash
cd pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e .

# set api key for LLM-assisted analysis (recommended)
export ANTHROPIC_API_KEY=sk-ant-...

# process a book
lectorius-pipeline process \
  --input ../source/the-great-gatsby.epub \
  --book-id great-gatsby \
  --output-dir ../books/great-gatsby \
  --llm-assist
```

see [pipeline/README.md](pipeline/README.md) for full usage, CLI reference, and post-processing validation instructions.

## docs

- [prd](docs/prd.md)
- [pipeline spec](docs/pipeline.md) — full pipeline specification with schemas, stages, LLM prompts
- [pipeline readme](pipeline/README.md) — quickstart, CLI reference, tested books, validation prompt
- [system architecture](docs/architecture.md)
- [data model](docs/data-model.md)
- [api spec](docs/api-spec.md)
- [playback state machine](docs/playback-state-machine.md)
- [llm prompts](docs/llm-prompts.md)

## license

mit
