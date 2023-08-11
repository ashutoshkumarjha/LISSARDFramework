package com.gishorizon.ingestion

import com.gishorizon.{IngestionRequest, IngestionResponse}
import org.apache.spark.SparkContext

object IngestData {

  def run(sc: SparkContext, request: IngestionRequest): IngestionResponse = {
    request.sensor match {
      case "Landsat8" =>
        IngestLandsat.run(
          sc, request.srcPath, request.dataTime, "file"
        )
        IngestionResponse(Map {
          "message" -> "Success"
        })
    }
    IngestionResponse(Map {
      "message" -> "Error"
    })
  }
}
