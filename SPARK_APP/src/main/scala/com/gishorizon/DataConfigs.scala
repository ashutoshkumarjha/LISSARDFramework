package com.gishorizon

object DataConfigs {
  val Layers = Map{
    "bathymetry" -> Map(
      "path" -> "data/out/bathymetry",
      "render" -> "terrain"
    )
    "liss3" -> Map(
      "path" -> "data/out/liss3",
      "render" -> "terrain"
    )
  }

  val RenderStyles = Map(
    "terrain" -> Map(
      "min" -> -7000,
      "max" -> 8000,
      "numSteps" -> 100
    )
  )
  var OUT_PATH = "G:/ProjectData/geoprocess/"
  var TEMP_PATH = "G:/ProjectData/temp_data/"
  var TILE_PATH = "G:/ProjectData/tiles/"
  var DATA_HOST = "https://test2.gishorizon.com"
  var SPARK_MASTER = "local[*]"
  var EXE_MEM = "12g"
  var DRI_MEM = "12g"
}
