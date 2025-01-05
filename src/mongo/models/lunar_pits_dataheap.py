"""
This module contains the Pydantic model for the LunarPitBatch data structure
"""
from pydantic import BaseModel


class LunarPitBatch(BaseModel):
    """
    Each datafile could generate 1 instance of LunarPitBatch when a lunar pit is within some given distance, with data relevant to that lunar pit
    """
    url: str
    lunar_pit_name: str
    data: dict
