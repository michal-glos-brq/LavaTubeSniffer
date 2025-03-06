import re
import os
import numpy as np

###############################################
#           LRO SPICE METADATA                #
###############################################

BASE_URL = (
    "https://naif.jpl.nasa.gov/pub/naif/pds/data/lro-l-spice-6-v1.0/lrosp_1000/data/"
)
DESTINATION = "/media/mglos/HDD_8TB2/SPICE"

###############################################
#             LRO RESOURCES                   #
###############################################

LRO_RESOURCES = {
    # CK (C Kernel): Spacecraft pointing/orientation data
    "ck": re.compile(r"(lrodv|lrosc).*.(bc|lbl)"),
    # SPK (SP Kernel): Spacecraft trajectory/ephemeris data
    "spk": re.compile(r"lrorg.*.(bsp|lbl)"),
    # SCLK (Spacecraft Clock Kernel): Time correlation data, newes is OK, contains all historical data
    "sclk": re.compile(r"lro_clkcor_2024262_v00.*.(tsc|lbl)"),
    # IK (Instrument Kernel): Instrument parameters/characteristics
    "ik": re.compile(r"lro_(crater|dlre|lamp|lend|lola).*.(ti|lbl)"),
    # LSK (Leap Seconds Kernel): Time system conversions
    "lsk": re.compile(r"naif.*.(tls|lbl)"),
    # FK (Frame Kernel): Reference frame definitions
    "fk": re.compile(r"(lro|moon).*.(tf|lbl)"),
    # PCK (Planetary Constants Kernel): Celestial body physical properties
    "pck": re.compile(r"(pck|moon).*.(bpc|lbl)"),
    # EK - event kernels of LRO
    "ek": re.compile(r"lroevnt.*.(bes|lbl)"),
}

###############################################
#             LONE KERNELS                    #
###############################################

LONE_KERNELS = [
    {
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de440_200625.bpc",
        "path": os.path.join(DESTINATION, "moon_pa_de440_200625.bpc"),
    },
    {
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de441_part-1.bsp",
        "path": os.path.join(DESTINATION, "de441_part-1.bsp"),
    },
    {
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de441_part-2.bsp",
        "path": os.path.join(DESTINATION, "de441_part-2.bsp"),
    },
    {
        "url": "https://naif.jpl.nasa.gov/pub/naif/LRO/kernels/ik/lro_lroc_v19.ti",
        "path": os.path.join(DESTINATION, "ik/lro_lroc_v19.ti"),
    },
]

###############################################
#             LUNAR MODEL                   #
###############################################

LUNAR_MODEL = {
    "url": "https://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
    "tif_path": "/media/mglos/HDD_8TB2/LOLA_DSK/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
    "dsk_path": "/media/mglos/HDD_8TB2/LOLA_DSK/dsk/output7_5_percent.new_gen.dsk",
    "xyz_path": "/media/mglos/HDD_8TB2/LOLA_DSK/xyz/output7_5_percent.xyz",
    "commands": None,
}
LUNAR_MODEL["commands"] = [
    (
        "gdal_translate -of XYZ -scale -32768 32767 -1737.4 1737.4 "
        "-outsize 7.5% 7.5% -a_nodata -32768 "
        f"{LUNAR_MODEL['tif_path']} {LUNAR_MODEL['xyz_path']}"
    )
]

###############################################
#           DSK CREATION CONSTANTS            #
###############################################

LUNAR_RADIUS = 1737.400  # Mean lunar radius (km)
DSK_FILE_CENTER_BODY_ID = 301  # NAIF ID for the Moon
DSK_FILESURFACE_ID = 1001  # Arbitrary surface ID
DSK_FILE_FRAME = "MOON_ME_DE421"  # Moon body-fixed frame

FINSCL = 6.9  # Fine voxel scale
CORSCL = 9    # Coarse voxel scale
WORKSZ = 400_000_000
VOXPSZ = 45_000_000   # Voxel-plate pointer array size
VOXLSZ = 135_000_000  # Voxel-plate list array size
SPXISZ = 1_250_000_000  # Spatial index size
MAKVTL = True

CORSYS = 3
CORPAR = np.zeros(10)
DCLASS = 2

###############################################
#         TRAJECTORY SIMULATION DATA          #
###############################################

# It's a little bit less, used for radius correction
LRO_SPEED = 1.7
QUERY_RADIUS_MULTIPLIER = 1.3


# Diviner instrument IDs (from https://www.diviner.ucla.edu/instrument-specs)
DIVINER_INSTRUMENT_IDS = [
    -85211, -85212, -85213, -85214, -85215, -85216, -85221, -85222, -85223
]
LOLA_INSTRUMENT_IDS = [-85511, -85512, -85513, -85514, -85515, -85521, -85522, -85523, -85523, -85525]
MINIRF_INSTRUMENT_IDS = [-85700]
WAC_INSTRUMENT_IDS = [-85621, -85626]
NAC_INSTRUMENT_IDS = [-85600, -85610]


LRO_DIVINER_FRAME_STR_ID = "LRO_DLRE"
LRO_LOLA_FRAME_STR_ID = "LRO_LOLA"
LRO_MINIRF_FRAME_STR_ID = "LRO_MINIRF"



DIVINER_INSTRUMENT_ID_TO_RDR_INDEX = {
    -85211: 1,
    -85212: 2,
    -85213: 3,
    -85214: 4,
    -85215: 5,
    -85216: 6,
    -85221: 7,
    -85222: 8,
    -85223: 9,
}




MOON_STR_ID = "MOON"
MOON_REF_FRAME_STR_ID = "MOON_ME"
LRO_STR_ID = "LUNAR RECONNAISSANCE ORBITER"




# Additional simulation configuration
ABBERRATION_CORRECTION = "CN+S"
TIME_STEP = 1.024  # Step through trajectory computation in seconds
MAX_TIME_STEP = 3600
MAX_LOADED_SPICE = 3  # Maximum number of dynamic SPICE kernels loaded at once
