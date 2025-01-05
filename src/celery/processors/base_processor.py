"""
This file will define processors for the datasets, responsible for filtering the data of interest
"""
import pandas as pd
import numpy as np
from lxml import etree
from abc import ABC

from src.mongo.models.lunar_pits_dataheap import LunarPitBatch

MOON_RADIUS_KM = 1737.4  # Average Moon radius in kilometers



class BaseProcessor(ABC):

    def assign_points_to_pits(
        df,
        pits,
        tolerance_km,
        pit_name_col="name",
        data_lat_col="clat",
        data_lon_col="clon",
        pit_lat_col="latitude",
        pit_lon_col="longitude",
    ):
        """
        Assign data points to pits within a tolerance distance and create MongoDB-style documents.

        Args:
            df (pd.DataFrame): DataFrame containing the data points with latitude and longitude columns.
            data_lat_col (str): Column name for the data points' latitudes.
            data_lon_col (str): Column name for the data points' longitudes.
            pits (pd.DataFrame): DataFrame containing pits with latitude, longitude, and name columns.
            pit_name_col (str): Column name for the pits' names.
            pit_lat_col (str): Column name for the pits' latitudes.
            pit_lon_col (str): Column name for the pits' longitudes.
            tolerance_km (float): Tolerance distance in kilometers.

        Returns:
            list: A list of dictionaries, each representing a pit and its associated data points.
        """
        # Convert data points and pits' coordinates to radians
        data_lat = np.radians(df[data_lat_col].values)
        data_lon = np.radians(df[data_lon_col].values)
        pits_lat = np.radians(pits[pit_lat_col].values)
        pits_lon = np.radians(pits[pit_lon_col].values)

        # List to store the resulting documents
        pit_dataheaps = []

        # Iterate through each pit
        for i, (pit_lat, pit_lon, pit_name) in enumerate(zip(pits_lat, pits_lon, pits[pit_name_col])):
            # Calculate the haversine distance to each data point
            dlat = data_lat - pit_lat
            dlon = data_lon - pit_lon
            a = np.sin(dlat / 2) ** 2 + np.cos(data_lat) * np.cos(pit_lat) * np.sin(dlon / 2) ** 2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
            distances = MOON_RADIUS_KM * c

            # Identify points within the tolerance distance
            within_tolerance = distances <= tolerance_km

            # Collect data entries for the current pit
            assigned_points = df[within_tolerance].to_dict(orient="list")

            # Create a MongoDB-style document if data found
            if assigned_points:
                pit_document = LunarPitBatch(url=f"{pit_name}_{i}", lunar_pit_name=pit_name, data=assigned_points)
                pit_dataheaps.append(pit_document)

        return pit_dataheaps

    @staticmethod
    def parse_pds4_metadata(xml_data):
        """Extract field metadata from the PDS4 XML file."""
        root = etree.fromstring(xml_data)
        ns = root.nsmap
        # Extract field metadata from the XML
        fields = []
        for field in root.xpath(".//pds:Field_Character", namespaces=ns):
            invalid_constant = field.find(".//pds:invalid_constant", namespaces=ns)
            unknown_constant = field.find(".//pds:unknown_constant", namespaces=ns)

            fields.append(
                {
                    "name": field.findtext("pds:name", namespaces=ns).strip(),
                    "field_length": int(field.findtext("pds:field_length", namespaces=ns)),
                    "field_location": int(field.findtext("pds:field_location", namespaces=ns)),
                    "special_constants": {
                        "invalid": invalid_constant.text if invalid_constant is not None else None,
                        "unknown": unknown_constant.text if unknown_constant is not None else None,
                    },
                }
            )
        return fields

    @staticmethod
    def load_tab_file(tab_data, fields):
        """Load the .tab file using extracted metadata."""
        # Extract column names and calculate dynamic widths
        col_names = [field["name"] for field in fields]
        col_locations = [field["field_location"] for field in fields]

        # Calculate column widths based on locations
        col_widths = [b - a for a, b in zip(col_locations[:-1], col_locations[1:])]
        col_widths.append(fields[-1]["field_length"])  # Add the width of the last column

        # Extract special constants (invalid and unknown)
        special_constants = {
            field["name"]: [
                float(field["special_constants"]["invalid"]) if field["special_constants"]["invalid"] else None,
                float(field["special_constants"]["unknown"]) if field["special_constants"]["unknown"] else None,
            ]
            for field in fields
            if field["special_constants"]["invalid"] or field["special_constants"]["unknown"]
        }

        # Load the .tab file from string data and skip incorrect header rows
        df = pd.read_fwf(pd.compat.StringIO(tab_data.decode("utf-8")), widths=col_widths, names=col_names, skiprows=4)

        # Replace special constants with NaN
        for col, constants in special_constants.items():
            invalid, unknown = constants
            if col in df.columns:
                df[col] = df[col].replace([invalid, unknown], np.nan)

        # Clean up column names and ensure proper formatting
        df.columns = df.columns.str.strip()

        # Fix string columns like 'date' and 'utc' (strip quotes and clean up)
        for col in ["date", "utc"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.replace('"', "", regex=True)

        # Drop rows with all NaN values and reset index
        df = df.dropna(how="all").reset_index(drop=True)

        return df

