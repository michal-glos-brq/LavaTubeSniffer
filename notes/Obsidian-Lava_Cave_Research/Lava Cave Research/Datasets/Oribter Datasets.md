This website aggregates lots of 
https://pds-geosciences.wustl.edu/


Tool which would probably help a lot?
https://stereopipeline.readthedocs.io/en/latest/introduction.html#background

## LRO

**Diviner**
Is dataset of temperatures of the moon surface and 
Web: https://www.diviner.ucla.edu/science
Data: https://pds-geosciences.wustl.edu/missions/lro/diviner.htm
Specification: https://pds-geosciences.wustl.edu/lro/lro-l-dlre-2-edr-v1/lrodlr_0001/document/dp_archsis.pdf

**LROC**
Optical data
Guide: 
Web: https://www.lroc.asu.edu/images/1382
Data: https://pds.lroc.asu.edu/data/

Wide angle would be good too

**LOLA**
Alitimeter data of the Moon:
Web: https://ode.rsl.wustl.edu/moon/
Data: https://pds-geosciences.wustl.edu/missions/lro/lola.htm


**Might be useful datasets:**
Spectral data can help identify surface compositional differences, potentially indicating subsurface lava tubes: - **Moon Mineralogy Mapper (M3)**: High-resolution spectral data from **Chandrayaan-1**, useful for detecting basaltic lava flows and possible tube openings. [M3 Data Access](https://pds-imaging.jpl.nasa.gov/volumes/m3.html) - **Kaguya Spectrometer**: Spectral data from the Japanese **Kaguya mission**, aiding in identifying lunar mineral compositions.


**GRAIL** mapped the Moon’s gravity field, revealing subsurface voids or density anomalies, which might indicate lava tubes. Combining **GRAIL** and **LOLA** topographic data can refine search areas. [GRAIL PDS Data](https://pds-geosciences.wustl.edu/missions/grail/)



# ChatGPT-generated notes
# Lunar Reconnaissance Orbiter Data Query API Resources

This document provides all the resources needed to build an API for querying Lunar Reconnaissance Orbiter (LRO) data, including LiDAR, optical, and temperature data. It consolidates everything into accessible URLs and documentation links to ensure ease of use.

## LOLA LiDAR Data
The Lunar Orbiter Laser Altimeter (LOLA) provides high-resolution topographic data of the lunar surface. Below are the resources for accessing and querying LOLA data.

- **Primary Data Repository**:  
  [LOLA PDS Archive at NASA GSFC](https://lunar.gsfc.nasa.gov)
  
- **Cloud-Optimized Point Cloud (COPC) Format**:  
  Data available via AWS S3 bucket.  
  `arn:aws:s3:::astrogeo-ard/moon/lro/lola/`  
  [AWS LOLA Data Registry](https://registry.opendata.aws/nasa-usgs-lunar-orbiter-laser-altimeter/)

- **LOLA RDR Query Tool**:  
  [LOLA RDR Tool](https://ode.rsl.wustl.edu/moon/)
  
- **API Documentation**:  
  LOLA API documentation and data formats can be found at:  
  [STAC and COPC documentation](https://stac.astrogeology.usgs.gov/docs/data/moon/lola/)

- **LiDAR Data Format (LAZ)**:  
  LOLA data is compressed into LAZ files (a variant of LAS 1.4).  
  [LiDAR Data Specification](https://stac.astrogeology.usgs.gov/docs/data/moon/lola/)

## LROC Optical Data
Lunar Reconnaissance Orbiter Camera (LROC) captures high-resolution images. The following resources help access LROC optical imagery.

- **High-Resolution Imagery Tool**:  
  [LROC QuickMap](https://quickmap.lroc.asu.edu)
  
- **LROC Data Search Tool**:  
  [Lunar Orbital Data Explorer (ODE)](https://ode.rsl.wustl.edu/moon/)
  
- **Data Formats**:  
  LROC data is available in CSV, Topography, and Shapefile formats. API access via QuickMap:  
  [LROC QuickMap API](https://quickmap.lroc.asu.edu)

## Diviner Temperature Data
The Diviner instrument measures lunar surface temperatures. Below are the resources for temperature data querying.

- **Diviner Data Archive**:  
  [Diviner Archive at UCLA](https://www.diviner.ucla.edu)
  
- **Diviner RDR Query Tool**:  
  [Diviner RDR Tool](https://ode.rsl.wustl.edu/moon/)
  
- **API Documentation**:  
  Diviner RDR data query API is documented as part of the ODE platform.  
  [ODE Platform](https://ode.rsl.wustl.edu/moon/)

## Coordinate Systems
All LRO data is mapped using the IAU 2015 Moon/Sphere coordinate system, essential for geographic queries.

- **Coordinate System Specification**:  
  [IAU 2015 Projection Details](https://stac.astrogeology.usgs.gov/docs/data/moon/lola/)

## Supporting Libraries
To efficiently query large datasets, use the following libraries:

- **Point Data Abstraction Library (PDAL)**:  
  [PDAL Documentation](https://pdal.io)
  
- **PySTAC (Python Client for STAC)**:  
  [PySTAC GitHub](https://github.com/stac-utils/pystac)

## API Specifications
Here are the relevant API specifications for querying the LRO datasets.

- **LOLA RDR API Documentation**:  
  [LOLA API Documentation](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/LOLA/Intro.htm)

- **LROC QuickMap API Documentation**:  
  [LROC QuickMap API](https://quickmap.lroc.asu.edu)

---

## Additional Notes
- **Data Licensing**:  
  Data from the LOLA and Diviner instruments is publicly available under the [Creative Commons Zero (CC0)](https://creativecommons.org/publicdomain/zero/1.0/) license, ensuring free access and use.

- **Update Frequency**:  
  LOLA and Diviner datasets are updated quarterly. Subscribe to NASA’s data update service to get notifications on the latest releases.

---

This document provides all the raw resources and documentation URLs needed to build the API, ready to be copied and used by any intelligent AI system that requires these inputs.  
