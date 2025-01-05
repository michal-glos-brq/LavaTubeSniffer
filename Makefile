CONDA_ENV_NAME := lavatubesniffer
PYTHON_VERSION := 3.9
REQUIREMENTS_FILE := requirements.txt


### Scraping and parsing the Lunar Pit Atlas
scrape-lunar-pit-atlas: activate-conda-env
	 python3 src/mongo/scrape_lunar_pit_database.py

parse-local-lunar-pit-atlas: activate-conda-env
	 python3 src/mongo/parse_lunar_pits_database.py


### Conda env related

create-conda-env:
	@conda info --envs | grep -q "^$(CONDA_ENV_NAME)[[:space:]]" || \
		conda create -y -n $(CONDA_ENV_NAME) python=$(PYTHON_VERSION) && \
		echo "Environment $(CONDA_ENV_NAME) created with Python $(PYTHON_VERSION)."

install-requirements: create-conda-env
	@conda run -n $(CONDA_ENV_NAME) pip3 install -r $(REQUIREMENTS_FILE) && \
		echo "Requirements from $(REQUIREMENTS_FILE) installed in $(CONDA_ENV_NAME)."

activate-conda-env:
	@export PYTHONPATH=$(pwd)/src:${PYTHONPATH}
	@conda activate $(CONDA_ENV_NAME)


### Processing the actual data

# TODO
run-celery-worker: activate-conda-env
	@celery -A src.celery worker --loglevel=info

# TODO
initiate-diviner-sweep: activate-conda-env
	@python3 src/diviner/diviner_sweep.py

