from typing import Any, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field
from geoalchemy2.elements import WKBElement, WKTElement
from geoalchemy2.shape import from_shape, to_shape
import shapely.geometry


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry representation."""

    type: Literal["Point"] = "Point"
    coordinates: Tuple[float, float] = Field(
        ...,
        description="Longitude and latitude coordinate pair [lon, lat]",
    )

    @classmethod
    def from_lat_lon(cls, latitude: float, longitude: float) -> "GeoJSONPoint":
        """Construct from explicit latitude and longitude coordinates."""
        return cls(coordinates=(longitude, latitude))


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon geometry representation."""

    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[Tuple[float, float]]] = Field(
        ...,
        description="List of linear rings composing the polygon coordinates",
    )


def geometry_to_shape(geom: Any) -> Optional[shapely.geometry.base.BaseGeometry]:
    """Convert DB WKB/WKT element or GeoJSON dict to a Shapely geometry object."""
    if geom is None:
        return None
    if isinstance(geom, (WKBElement, WKTElement)):
        return to_shape(geom)
    if isinstance(geom, dict):
        return shapely.geometry.shape(geom)
    if isinstance(geom, (GeoJSONPoint, GeoJSONPolygon)):
        return shapely.geometry.shape(geom.model_dump())
    if isinstance(geom, shapely.geometry.base.BaseGeometry):
        return geom
    return None


def shape_to_wkb(shape_obj: Optional[shapely.geometry.base.BaseGeometry], srid: int = 4326) -> Optional[WKBElement]:
    """Convert a Shapely geometry to a GeoAlchemy2 WKB element with SRID."""
    if shape_obj is None:
        return None
    return from_shape(shape_obj, srid=srid)
