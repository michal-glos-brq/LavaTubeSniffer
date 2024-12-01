We start with RDR dataset for DIVINER:
Root data folder: https://pds-geosciences.wustl.edu/lro/lro-l-dlre-4-rdr-v1/
Readme (citations etc ...): https://pds-geosciences.wustl.edu/lro/lro-l-dlre-4-rdr-v1/lrodlr_1002/aareadme.txt

Atlas of craters, which we already implemented and fetched into out MongoDB

This will test the feasebility of the project itself.  


Try to add 2 more datasets, e.g. MiniRF|GRAIL|SELENE-Radar  

Eventually, we might proceed for further dataset analysis. This would be enabled by universal dataset implementation with minor configuration of other datasets on pds-geoscience.  

Try to put the code into modules and test the code as a whole:  
	While a majority of code would have yet to be written, at this point, we would like to   implement distributed capability, for which we need:  
 -  Public IP addr. on my personal "PC"  
 - Maybe private pypi repository on some free provider to upload refactored code as a module  
 -  Prepare DB to collect points of interest in distributed manner  
 -  Create a Docker|Venv|CondaEnv ??? and installation scripts for slave nodes  
 - Invade university with this VIRUS and collect data  
 - Make a DB of "PROBED_URLS" on Master node  


If the above would be completed before 31/1/2025, I would be a very happy human being ...  

Clean all the data  

Data analysis:  
 -  Study methods on how to process each of the captured&implemented sensor type  
	 - Process the data into presentable data:  
		 - Superresolution of Radar, Altitude, Gravity data  
		 - Superresolution with temporal domain included for observation and analysis  
     - Estimate the hidden underground features of lunar pits from the processed data (very roughly, basically just enough to present the work I will have done).  