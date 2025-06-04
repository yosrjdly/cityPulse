"""
Geographic boundaries for the CityPulse project.
"""

# Tunis city center coordinates (latitude, longitude)
TUNIS_CENTER = (36.8065, 10.1815)

# Bounding box for Greater Tunis (min_lon, min_lat, max_lon, max_lat)
# Includes Tunis, Ariana, Ben Arous, and Manouba governorates
GREATER_TUNIS_BBOX = (10.0315, 36.7065, 10.3315, 36.9065)

# Administrative boundaries
ADMIN_LEVELS = {
    "governorate": 4,  # Wilaya/Governorate
    "delegation": 5,   # Delegation/District
    "municipality": 6, # Municipality
    "sector": 8        # Sector/Imada
}

# Study area definitions
STUDY_AREAS = {
    "tunis_city": {
        "name": "Tunis City",
        "osm_relation_id": 1435843,  # OSM relation ID for Tunis Municipality
        "buffer": 0  # No buffer
    },
    "greater_tunis": {
        "name": "Greater Tunis",
        "osm_relation_ids": [1435843, 1441155, 1441154, 1441156],  # Tunis, Ariana, Ben Arous, Manouba
        "buffer": 2000  # 2km buffer
    },
    "tunis_governorate": {
        "name": "Tunis Governorate",
        "osm_relation_id": 1441153,
        "buffer": 1000  # 1km buffer
    }
}

# Points of interest categories
POI_CATEGORIES = {
    "education": ["school", "university", "college", "library"],
    "healthcare": ["hospital", "clinic", "pharmacy", "doctors"],
    "recreation": ["park", "playground", "sports_centre", "swimming_pool"],
    "shopping": ["supermarket", "marketplace", "mall", "convenience"],
    "transport": ["bus_station", "tram_stop", "railway_station", "taxi_stand"],
    "government": ["townhall", "public_building", "police", "post_office"],
    "finance": ["bank", "atm"]
}
