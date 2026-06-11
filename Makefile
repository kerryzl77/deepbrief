.PHONY: doctor scout rank article m4 m5 m6 m7 m9a test install uninstall

doctor:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli doctor

scout:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli scout

rank:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli rank

article:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli analyst article --url "$(URL)"

m4:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli verify m4-fixtures

m5:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli feedback m5-fixtures

m6:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli tuner m6-fixtures

m7:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli render m7

m9a:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli soak m9a

test:
	@PYTHONPATH=src uv run --no-sync python -m unittest discover -s tests

install:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli install

uninstall:
	@PYTHONPATH=src uv run --no-sync python -m deepbrief.cli uninstall
