# MVP
#### Database 
- Define the documents with Pydantic
  - Create MongoDB+GridFS deployment
	  - Persistent storage
  - Create script scraping data about pits and feeding it into database
#### Dataset
 - Diviner dataset, already processed data
#### Scripts
 - Data control script
	 - Request data fetch
	 - Process data into objects (Be libaral with padding, not a lot of data to store and we need context)

#### Classification methods
 - Clustering classifiers
	 - Comparing pits with local timeseries
	 - Embedding pit and location into single value timeseries
 - Gather some metrics about the pits

# TODO
#### Scripts
 - Data control script
	 - Add collections of points to scan large datasets ordered by time and not space
 - Visualization scripts 

#### Dataset
 - Implement one of the radar datasets
 - Implement GRAIL dataset
 - Implement one of the optical datasets, probably WAC
 - Implement higher resolution and all-channel DIVINER dataset(probably)
#### Classification methods
 - Use more data sources for classifications combined



# Eventually
#### Database
  - Manually fill in the lava tubes from [[Poggiali_AGU2021_NoAnimations_v2.pdf]]

#### Dataset
 - Instead of gathering objects, implement surface sweep

#### Detection methods
 - TBD, depends on the data sources
 - Maybe some stupid  YOLOVwhateverItsNow

#### Further dataset implementation
 - Both radar datasets
 - Both optical datasets
 - GRAIL dataset of gravitational fields
 - Narrow Angle Camera, though provides only partial data