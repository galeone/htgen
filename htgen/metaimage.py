"""
Module for extracting and processing EXIF metadata from images.
Provides functionality to extract GPS coordinates and other metadata from image files.
"""

from typing import Dict, Tuple, Union, Optional
from pathlib import Path
import time
import logging
import requests
from exif import Image

logger = logging.getLogger(__name__)


def get_location_from_coordinates(lat: float, lng: float) -> Dict[str, Optional[str]]:
    """
    Get city and country information from GPS coordinates using OpenStreetMap's Nominatim API.

    Args:
        lat: Latitude in decimal degrees
        lng: Longitude in decimal degrees

    Returns:
        Dict containing location data:
            - city: City name if available, None otherwise
            - country: Country name if available, None otherwise
    """
    result = {"city": None, "country": None}

    try:
        logger.info("Attempting reverse geocoding for coordinates: %s, %s", lat, lng)
        # Add a small delay to respect Nominatim's usage policy
        time.sleep(1)

        # Make request to Nominatim API
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lng,
                "format": "json",
                "zoom": 10,
                "addressdetails": 1,
            },
            headers={"User-Agent": "HTGen/1.0"},
            timeout=10,  # Add a timeout of 10 seconds
        )
        response.raise_for_status()
        data = response.json()

        # Extract city and country from address details
        address = data.get("address", {})

        # Try different fields that might contain the city name
        city_fields = ["city", "town", "village", "suburb", "municipality"]
        for field in city_fields:
            if field in address:
                result["city"] = address[field]
                logger.debug("Found city name in field '%s': %s", field, result["city"])
                break

        result["country"] = address.get("country")
        if result["country"]:
            logger.debug("Found country: %s", result["country"])

    except requests.RequestException as e:
        logger.error("Failed to fetch location data from Nominatim API: %s", str(e))
    except (ValueError, KeyError) as e:
        logger.error("Failed to parse location data: %s", str(e))
    except Exception as e:
        logger.error("Unexpected error during reverse geocoding: %s", str(e))

    return result


def decimal_coords(coords: Tuple[float, float, float], ref: str) -> float:
    """
    Convert GPS coordinates from degrees/minutes/seconds to decimal degrees.

    Args:
        coords: Tuple of (degrees, minutes, seconds)
        ref: GPS reference ('N', 'S', 'E', or 'W')

    Returns:
        float: Decimal degrees coordinate
    """
    try:
        decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
        if ref in ("S", "W"):
            decimal_degrees = -decimal_degrees
        return decimal_degrees
    except (TypeError, ValueError) as e:
        logger.error(
            "Failed to convert coordinates %s with ref %s: %s", coords, ref, str(e)
        )
        raise


def image_coordinates(
    image_path: Union[str, Path],
) -> Dict[str, Optional[Union[str, float]]]:
    """
    Extract EXIF metadata including GPS coordinates and timestamp from an image.

    Args:
        image_path: Path to the image file

    Returns:
        Dict containing image metadata:
            - imageTakenTime: Timestamp when image was taken
            - geolocation_lat: Latitude in decimal degrees (if available)
            - geolocation_lng: Longitude in decimal degrees (if available)
            - camera_make: Camera manufacturer (if available)
            - camera_model: Camera model (if available)
            - exposure_time: Exposure time in seconds (if available)
            - f_number: F-number of the lens (if available)
            - iso: ISO speed (if available)
            - city: City name based on GPS coordinates (if available)
            - country: Country name based on GPS coordinates (if available)

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If file is not a valid image with EXIF data
    """
    image_path = Path(image_path)
    logger.info("Processing image: %s", image_path)

    if not image_path.exists():
        logger.error("Image file not found: %s", image_path)
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with open(image_path, "rb") as src:
            img = Image(src)
    except Exception as e:
        logger.error("Failed to read image file %s: %s", image_path, str(e))
        raise ValueError(f"Failed to read image file: {e}") from e

    result = {
        "imageTakenTime": None,
        "geolocation_lat": None,
        "geolocation_lng": None,
        "camera_make": None,
        "camera_model": None,
        "exposure_time": None,
        "f_number": None,
        "iso": None,
        "city": None,
        "country": None,
    }

    if not img.has_exif:
        logger.info("No EXIF data found in image")
        return result

    # Extract basic EXIF data if available
    for field in [
        "datetime_original",
        "make",
        "model",
        "exposure_time",
        "f_number",
        "iso",
    ]:
        try:
            key = "imageTakenTime" if field == "datetime_original" else field
            key = "camera_" + key if field in ["make", "model"] else key
            result[key] = getattr(img, field)
            logger.debug("Extracted %s: %s", key, result[key])
        except AttributeError:
            logger.debug("Field %s not found in EXIF data", field)

    # Extract GPS coordinates if all required attributes are available
    gps_attrs = [
        "gps_latitude",
        "gps_longitude",
        "gps_latitude_ref",
        "gps_longitude_ref",
    ]
    if all(hasattr(img, attr) for attr in gps_attrs):
        try:
            lat = decimal_coords(img.gps_latitude, img.gps_latitude_ref)
            lng = decimal_coords(img.gps_longitude, img.gps_longitude_ref)
            result["geolocation_lat"] = lat
            result["geolocation_lng"] = lng
            logger.info("Found GPS coordinates: %s, %s", lat, lng)

            # Get city and country information if coordinates are available
            location = get_location_from_coordinates(lat, lng)
            result["city"] = location["city"]
            result["country"] = location["country"]

            if location["city"] and location["country"]:
                logger.info(
                    "Location identified as %s, %s",
                    location["city"],
                    location["country"],
                )
            else:
                logger.info("Could not determine precise location from coordinates")

        except (AttributeError, TypeError, ValueError) as e:
            logger.warning("Failed to process GPS coordinates: %s", str(e))
    else:
        logger.info("No GPS coordinates found in EXIF data")

    return result
