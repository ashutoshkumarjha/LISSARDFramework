package com.gishorizon

import geotrellis.layer.{SpaceTimeKey, SpatialKey, TileLayerMetadata}
import geotrellis.raster.{ArrayTile, MultibandTile, RGB, Tile}
import geotrellis.spark.store.file.FileLayerReader
import geotrellis.store.{Between, Intersects, LayerId, LayerQuery}
import geotrellis.vector.Extent
import org.apache.spark.SparkContext

import java.time.{Instant, ZoneOffset, ZonedDateTime}
import java.time.format.DateTimeFormatter

object TileServerUtils {

  def getCatalogDetails(
                         sc: SparkContext,
                         path: String,
                         layerName: String
                       ): (FileLayerReader, Int) = {
    val outputCatalogPath = path
    val reader = FileLayerReader(outputCatalogPath)(sc)
    val layerIds = reader.attributeStore.layerIds.filter { id => id.name == layerName }
    val zooms = layerIds.map {
      _.zoom
    }
    val maxZoom = zooms.max
    (reader, maxZoom)
  }

  def reZoom(reader: FileLayerReader, layerName: String, maxZoom: Int, x: Int, y: Int, z: Int): Tile = {
    val dz = z - maxZoom
    val key = SpatialKey((x / math.pow(2, dz)).toInt, (y / math.pow(2, dz)).toInt)
    val dx = x - key._1 * math.pow(2, dz).toInt
    val dy = y - key._2 * math.pow(2, dz).toInt
    val rdd = readTileBySpatialKey(reader, layerName, maxZoom, key)
    val w = rdd.cols
    val h = rdd.rows
    val tw = (w / math.pow(2, dz)).toInt
    val th = (h / math.pow(2, dz)).toInt
    val x0 = tw * dx
    val x1 = tw * (dx + 1)
    val y0 = th * dy
    val y1 = th * (dy + 1)
    rdd.crop(x0, y0, x1, y1).resample(w, h)
  }

  def reZoomMultiband(reader: FileLayerReader, layerName: String, maxZoom: Int, x: Int, y: Int, z: Int, sTs: ZonedDateTime, eTs: ZonedDateTime): MultibandTile = {
    val dz = z - maxZoom
    val key = SpatialKey((x / math.pow(2, dz)).toInt, (y / math.pow(2, dz)).toInt)
    val dx = x - key._1 * math.pow(2, dz).toInt
    val dy = y - key._2 * math.pow(2, dz).toInt
    val rdd = readTileBySpaceTimeKey(reader, layerName, maxZoom, key, sTs, eTs)
    val w = rdd.cols
    val h = rdd.rows
    val tw = (w / math.pow(2, dz)).toInt
    val th = (h / math.pow(2, dz)).toInt
    val x0 = tw * dx
    val x1 = tw * (dx + 1)
    val y0 = th * dy
    val y1 = th * (dy + 1)
    rdd.crop(x0, y0, x1, y1).resample(w, h)
  }

  private def readTileBySpaceTimeKey(reader: FileLayerReader, layerName: String, z: Int, key: SpatialKey, sTs: ZonedDateTime, eTs: ZonedDateTime): MultibandTile = {
    val timeFrom = sTs
    val timeTo = eTs
    val m = reader.attributeStore.readMetadata[TileLayerMetadata[SpaceTimeKey]](LayerId(layerName, z))
    val res = reader
      .query[SpaceTimeKey, MultibandTile, TileLayerMetadata[SpaceTimeKey]](LayerId(layerName, z))
      .where(
        Intersects(
          key.extent(m.layout)
        )
      )
      .where(
        Between(
          timeFrom, timeTo
        )
      )
      .result.collect()
    handleMultipleMultibandTiles(res)
  }

  private def handleMultipleMultibandTiles(tiles: Array[(SpaceTimeKey, MultibandTile)]): MultibandTile = {
    if (tiles.length == 1) {
      return tiles.head._2
    } else {
      val noOfBands = 7
      var _tiles = Array[Tile]()
      if(tiles.length==0){
        for (band_no <- 0 until noOfBands) {
          val tile: Tile = ArrayTile(Array.fill(256 * 256)(0), 256, 256)
          _tiles = _tiles :+ tile
        }

        MultibandTile(_tiles)
      }else{
        val r = tiles.reduce{
          (t1: (SpaceTimeKey, MultibandTile), t2: (SpaceTimeKey, MultibandTile))=>{
            (t1._1, t1._2.merge(t2._2))
          }
        }
        r._2
//        var _tilesData = Array[Array[Double]]()
//        for (band_no <- 0 until noOfBands) {
//          if(_tilesData.length<=band_no){
//            _tilesData = _tilesData :+ Array.fill(256 * 256)(0.0)
//          }
//          for (i <- 0 until 256*256){
//            for (ti <- tiles.indices) {
//              val v = tiles(ti)._2.band(band_no).getDouble(i%256, Math.floor(i/256).toInt)
//              if (v != 0) {
//                _tilesData(band_no)(i) = v
//              }
//            }
//          }
//          _tiles = _tilesData.map {
//            td => ArrayTile(td, 256, 256)
//          }
//        }
      }
    }
  }

  private def readTileBySpatialKey(reader: FileLayerReader, layerName: String, z: Int, key: SpatialKey): Tile = {
    val m = reader.attributeStore.readMetadata[TileLayerMetadata[SpatialKey]](LayerId(layerName, z))
    reader.query[SpatialKey, Tile, TileLayerMetadata[SpatialKey]](LayerId(layerName, z))
      .where(
        Intersects(
          key.extent(m.layout)
        )
      ).result.collect().head._2
  }

  def getTileForXYZ(reader: FileLayerReader, layerName: String, maxZoom: Int, x: Int, y: Int, z: Int): Tile = {
    if (maxZoom < z) {
      TileServerUtils.reZoom(
        reader, layerName, maxZoom, x, y, z
      )
    } else {
      val key = SpatialKey(x, y)
      TileServerUtils.readTileBySpatialKey(
        reader, layerName, z, key
      )
    }
  }

  def getMultibandTileForXYZTime(reader: FileLayerReader, layerName: String, maxZoom: Int, x: Int, y: Int, z: Int, startDateStr: String, endDateStr: String): MultibandTile = {
    val sTs = ZonedDateTime.parse(f"${startDateStr}T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)))
    val eTs = ZonedDateTime.parse(f"${endDateStr}T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)))
    if (maxZoom < z) {
      TileServerUtils.reZoomMultiband(
        reader, layerName, maxZoom, x, y, z, sTs, eTs
      )
    } else {
      val key = SpatialKey(x, y)
      TileServerUtils.readTileBySpaceTimeKey(
        reader, layerName, z, key, sTs, eTs
      )
    }
  }
}
