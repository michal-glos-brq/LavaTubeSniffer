# API Documentation for LiDAR LOLA Data

## Overview
The Lunar Orbiter Laser Altimeter (LOLA) instrument aboard the Lunar Reconnaissance Orbiter (LRO) provides high-resolution topographic data of the lunar surface. This API allows users to query and retrieve LOLA LiDAR data based on geographic coordinates and specific parameters. The data is available in Cloud Optimized Point Cloud (COPC) format, designed for efficient data streaming and querying large datasets.

## Base URL
The following URLs provide access to LOLA data:

- **Primary Repository**:  
  [https://lunar.gsfc.nasa.gov](https://lunar.gsfc.nasa.gov)

- **AWS Cloud-Optimized Point Cloud Data**:  
  `arn:aws:s3:::astrogeo-ard/moon/lro/lola/`  
  [AWS LOLA Data Registry](https://registry.opendata.aws/nasa-usgs-lunar-orbiter-laser-altimeter/)

- **LOLA Query Tool**:  
  [LOLA RDR Tool](https://ode.rsl.wustl.edu/moon/)

## Query Parameters
This API supports the following query parameters for retrieving LiDAR data based on geographic location:

### Required Parameters
1. **Latitude (lat)**:  
   The latitude of the area to query, provided in degrees. Values range from -90 to 90.
   
2. **Longitude (lon)**:  
   The longitude of the area to query, provided in degrees. Values range from -180 to 180.

3. **Radius (rad)**:  
   The lunar radius, in meters, corresponding to the elevation data. LOLA provides elevation data relative to the mean lunar radius (1737.4 km).

4. **Tile**:  
   COPC data is stored in 15°x15° tiles. Specify the tile’s geographic bounding box using min and max latitude/longitude to get the relevant data.

### Optional Parameters
- **Bounding Box (bbox)**:  
  Defines a bounding box to filter results. This consists of minimum and maximum latitudes and longitudes.
  
- **Spatial Resolution (res)**:  
  Specifies the spatial resolution of the output data. The default is the highest resolution available (~1 meter vertical accuracy).
  
- **File Format (format)**:  
  The API returns data in LAZ (compressed LAS) format by default. Optionally, specify the format as CSV or JSON for smaller datasets.

## Data Formats
The following formats are available for querying LiDAR data:

- **COPC (Cloud-Optimized Point Cloud)**:  
  This format allows efficient querying of large LiDAR datasets. It’s structured using an octree for spatial indexing and can be streamed using HTTP range requests.
  
- **CSV**:  
  For simple topographic data, CSV files provide a list of locations with their respective elevation values.
  
- **Shapefile**:  
  Shapefiles are available for geographic information system (GIS) applications, enabling spatial analysis.




## API Documentation Links

- **LOLA RDR Query Tool**:  
    [https://ode.rsl.wustl.edu/moon/](https://ode.rsl.wustl.edu/moon/)
    
- **LOLA COPC Specification**:  
    [https://stac.astrogeology.usgs.gov/docs/data/moon/lola/](https://stac.astrogeology.usgs.gov/docs/data/moon/lola/)
    
- **AWS Data Access**:  
    [https://registry.opendata.aws/nasa-usgs-lunar-orbiter-laser-altimeter/](https://registry.opendata.aws/nasa-usgs-lunar-orbiter-laser-altimeter/)
    

## License and Usage

- **License**:  
    Data is available under the Creative Commons Zero (CC0) license, ensuring free access and usage.
    
- **Update Frequency**:  
    LOLA data is updated quarterly with new releases. Users can subscribe to NASA’s release notifications to stay updated.
    

## Tools and Libraries

To work with LOLA data efficiently, the following libraries can be used:

- **PDAL (Point Data Abstraction Library)**:  
    [https://pdal.io](https://pdal.io)
    
- **PySTAC (Python Client for STAC)**:  
    [https://github.com/stac-utils/pystac](https://github.com/stac-utils/pystac)