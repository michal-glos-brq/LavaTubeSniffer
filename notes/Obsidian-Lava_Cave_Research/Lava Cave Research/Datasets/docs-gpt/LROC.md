# API Documentation for LROC Narrow-Angle Camera Data

## Overview
The Lunar Reconnaissance Orbiter Camera (LROC) consists of two Narrow-Angle Cameras (NAC) that capture high-resolution images of the lunar surface. This API allows users to query and retrieve optical data from the NAC, which provides detailed imagery for surface studies, landing site identification, and terrain analysis.

## Base URL
The following URLs provide access to LROC NAC data:

- **Primary Repository**:  
  [LROC QuickMap](https://quickmap.lroc.asu.edu)

- **LROC NAC Data Search Tool**:  
  [Lunar Orbital Data Explorer (ODE)](https://ode.rsl.wustl.edu/moon/)

## Query Parameters
This API supports the following query parameters for retrieving NAC optical imagery based on geographic location:

### Required Parameters
1. **Latitude (lat)**:  
   The latitude of the area to query, provided in degrees. Values range from -90 to 90.
   
2. **Longitude (lon)**:  
   The longitude of the area to query, provided in degrees. Values range from -180 to 180.

3. **Resolution (res)**:  
   Specifies the resolution of the requested image. NAC imagery is available at resolutions up to 0.5 meters per pixel.

4. **Date Range (start_date, end_date)**:  
   Defines the time range for which to retrieve imagery. The format should be `YYYY-MM-DD`.

### Optional Parameters
- **Bounding Box (bbox)**:  
  A bounding box to restrict the search to a specific area. It consists of minimum and maximum latitudes and longitudes.
  
- **Image Format (format)**:  
  The API returns data in GeoTIFF format by default. You can request other formats like JPEG2000 or PNG for lower-resolution needs.

## Data Formats
The following formats are available for LROC NAC imagery:

- **GeoTIFF**:  
  High-resolution images in a georeferenced format, ideal for scientific analysis and GIS applications.
  
- **JPEG2000**:  
  A compressed format for high-quality images with reduced file size.

- **PNG/JPEG**:  
  For smaller, lower-resolution needs, imagery can be retrieved in PNG or JPEG format.

Data Specifications
Projection System:
NAC data is referenced to the IAU 2015 Moon/Sphere system (-180 to 180 longitude). Ensure that all geographic queries conform to this projection.

Resolution:
NAC imagery provides resolutions up to 0.5 meters per pixel, making it ideal for detailed surface analysis and terrain mapping.

API Documentation Links
LROC QuickMap API Documentation:
https://quickmap.lroc.asu.edu

LROC ODE API Documentation:
https://ode.rsl.wustl.edu/moon/

License and Usage
License:
LROC data is publicly available under the Creative Commons Zero (CC0) license, ensuring free access and use.

Update Frequency:
NAC data is updated monthly, with new images becoming available as they are processed.

Tools and Libraries
To efficiently query and process LROC NAC data, the following tools are recommended:

GDAL (Geospatial Data Abstraction Library):
GDAL Documentation

QGIS:
QGIS Documentation