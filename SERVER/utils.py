
import random
import string
import math
from osgeo import ogr

def generate_string():
    name = ''.join(random.choices(string.ascii_uppercase, k=16))
    return name

def tilenum2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg1 = xtile / n * 360.0 - 180.0
    lat_rad1 = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg1 = math.degrees(lat_rad1)
    
    lon_deg2 = (xtile+1) / n * 360.0 - 180.0
    lat_rad2 = math.atan(math.sinh(math.pi * (1 - 2 * (ytile+1) / n)))
    lat_deg2 = math.degrees(lat_rad2)

    return [lon_deg1, lat_deg1, lon_deg2, lat_deg2]

def get_tile_geom(x, y, z):
    bbox = tilenum2deg(x, y, z)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(bbox[0], bbox[3])
    ring.AddPoint(bbox[0], bbox[1])
    ring.AddPoint(bbox[2], bbox[1])
    ring.AddPoint(bbox[2], bbox[3])
    ring.AddPoint(bbox[0], bbox[3])

    tile_geom = ogr.Geometry(ogr.wkbPolygon)
    tile_geom.FlattenTo2D()
    tile_geom.AddGeometry(ring)
    return tile_geom