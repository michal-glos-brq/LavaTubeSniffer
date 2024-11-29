start:
	docker-compose up -d

# Will scrape data from lro
load_pits_db: start
	python3 src/dataset/suspected_objects_dataset/pits_database.py

# Will parse data scraped from LRO into pydantic-compatible new DB
# Will drop existing parsed data
parse_local_db: start
	python3 src/dataset/suspected_objects_dataset/parse_mongo.py
