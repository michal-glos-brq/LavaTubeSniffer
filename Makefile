##
#### User should have conda environment lavatubesniffer created and activated
## `make install-requirements && conda acticate lavatubesniffer`
##

CONDA_ENV_NAME := lavatubesniffer
PYTHON_VERSION := 3.9
REQUIREMENTS_FILE := requirements.txt

# Command to ensure commands are run within the Conda environment
CONDA_RUN := conda run -n $(CONDA_ENV_NAME)

LOW := $(shell nproc)
HIGH := $(shell echo $$(($(LOW) * 4)))


##########################################################################
#####                            Script runs                         #####
##########################################################################
scrape-lunar-pit-atlas: setup-pythonpath
	@python3 src/scripts/pit_atlas/scrape_lunar_pits_database.py

parse-local-lunar-pit-atlas: setup-pythonpath
	@python3 src/scripts/pit_atlas/parse_lunar_pits_database.py

mine-spice: setup-pythonpath
	@python3 src/scripts/SPICE/fetch.py


##########################################################################
#####                             Conda Env                          #####
##########################################################################
create-conda-env:
	@conda info --envs | grep -q "^$(CONDA_ENV_NAME)[[:space:]]" || \
		conda create -y -n $(CONDA_ENV_NAME) python=$(PYTHON_VERSION) && \
		echo "Environment $(CONDA_ENV_NAME) created with Python $(PYTHON_VERSION)."

install-requirements: create-conda-env
	@$(CONDA_RUN) pip install -r $(REQUIREMENTS_FILE) && \
		echo "Requirements from $(REQUIREMENTS_FILE) installed in $(CONDA_ENV_NAME)."

##########################################################################
#####                              Celery                            #####
##########################################################################
setup-pythonpath:
	@export PYTHONPATH=$PYTHONPATH:$(PWD)

run-celery-worker: setup-pythonpath
	celery -A src.celery.app.app  worker -l info -P gevent --autoscale=$(LOW),$(HIGH) --hostname=worker-localhost

run-celery-worker-debug: setup-pythonpath
	celery -A src.celery.app.app  worker -l debug -P gevent --autoscale=$(LOW),$(HIGH) --hostname=worker-localhost

run-flower: setup-pythonpath
	@celery -A src.celery.app.app flower --port=5555
