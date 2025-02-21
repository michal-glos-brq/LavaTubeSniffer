# SPICE DSK Error Reference Guide

This document lists common SPICE errors encountered while generating a DSK file and provides possible causes and solutions.

## 1. `SPICE(BADVERTEXCOUNT)`
**Error:** `Vertex count NV = 42467328; count must be in the range 3:16000002.`  
**Cause:** Too many vertices processed at once.  
**Fix:** Reduce batch size to ensure `NV <= 16,000,002`.

## 2. `SPICE(WORKSPACETOOSMALL)`
**Error:** `Workspace size = 5000000; should be at least 16000000 * (average number of voxels intersected by each plate).`  
**Cause:** Insufficient workspace size.  
**Fix:** Increase `worksz` to handle voxel-plate associations.

## 3. `SPICE(BARRAYTOOSMALL)`
**Error:** `Output value count is larger than B-list array room.`  
**Cause:** `spxisz` is too small for voxel-plate associations.  
**Fix:** Increase `spxisz` slightly (e.g., `spxisz = 4000001`).

## 4. `SPICE(CELLARRAYTOOSMALL)`
**Error:** `NCELL larger than cell array. Cell index = 30000001. Array size = 30000000.`  
**Cause:** `worksz` is too small for spatial indexing.  
**Fix:** Increase `worksz` and reduce batch size.

## 5. `SPICE(VALUEOUTOFRANGE)`
**Error:** `Coarse voxel scale = 5; scale must be in the range 1:NVXTOT**3, where NVXTOT = 0.`  
**Cause:** `NVXTOT` is zero, meaning no valid dataset.  
**Fix:** Ensure `NVXTOT > 0` before calling `dskmi2`. Reduce `corscl`.

## 6. `SPICE(BARRAYTOOSMALL) - Index Overflow`
**Error:** `Index larger than output array. Index = 27173193. Array size = 27173192.`  
**Cause:** Off-by-one indexing error.  
**Fix:** Increase `spxisz` and `voxlsz` to prevent overflow.

## 7. `SPICE(PLATELISTTOOSMALL)`
**Error:** `Voxel-plate list array size = 5000000; size is too small to hold all voxel-plate associations. Size should be at least 6793298 * (average number of voxels intersected by each plate).`  
**Cause:** `voxlsz` is too small to store voxel-plate mappings.  
**Fix:** Increase `voxlsz` to `>= 6793298 * (avg. number of voxels per plate)`.

## 8. `ValueError: Array length must be >= 0, not -1794967296`
**Error:** 
ValueError: Array length must be >= 0, not -1794967296
**Cause:** `spxisz` (spatial index size) has an overflow, often due to too large of a value exceeding integer limits.  
**Fix:** Reduce `spxisz`, ensuring it is within a valid integer range (e.g., `spxisz < 2,147,483,647` for 32-bit integers).  

## General Fixes:
- **Reduce Batch Sizes** – Keep vertex count below SPICE limits.  
- **Increase Memory (`worksz`, `spxisz`, `voxlsz`)** – Ensure arrays are large enough.  
- **Validate Input Data** – Ensure `NVXTOT > 0`.  
- **Adjust Voxel Scales (`finscl`, `corscl`)** – Use reasonable values.  
- **Fix Off-by-One Errors** – Increase array sizes slightly.  

By following these guidelines, SPICE DSK generation can be optimized and errors minimized.
