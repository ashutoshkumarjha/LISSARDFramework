package com.gishorizon

import org.apache.spark.sql.SparkSession
import org.apache.spark.{SparkConf, SparkContext}

object Spark {
  def conf: SparkConf = new SparkConf()
    .setIfMissing("spark.master", DataConfigs.SPARK_MASTER)
//    .setIfMissing("spark.master", "yarn")
    .set("spark.submit.deployMode", "cluster")
//    .setIfMissing("spark.master", "spark://localhost:7077")
//    .setMaster("spark://0.0.0.0:7077")
//    .setJars(Array("G:\\geotrellis-spark-job-assembly-0.1.0.jar"))
//    .setIfMissing("spark.driver.memory", "4g")
//    .setIfMissing("spark.driver.bindAddress","127.0.0.1")
//    .setIfMissing("spark.master", "192.168.14.41[*]")
//    .setIfMissing("spark.master", "192.168.102.2[*]")
    .setAppName("spark-ee")
    .set("spark.network.timeout", "600s")
//    .set("spark.kryo.registrationRequired", "true")
    .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    .set("spark.kryoserializer.buffer.max", "128m")
    .set("spark.kryo.registrator", "geotrellis.spark.store.kryo.KryoRegistrator")
    .set("spark.executor.userClassPathFirst", "true")
//    .set("spark.sql.warehouse.dir", "file:///c:/tmp/spark-warehouse")
    .set("spark.driver.memory", DataConfigs.DRI_MEM)
    .set("spark.executor.memory", DataConfigs.EXE_MEM)
//    .setExecutorEnv("GEOTRELLIS_HOME", Properties.envOrElse("GEOTRELLIS_HOME", "/usr/local/geotrellis"))
//    .setJars(Array[String](
//      "/usr/local/geotrellis/geotrellis-spark_2.12-3.6.0-SNAPSHOT.jar",
//      "/usr/local/geotrellis/geotrellis-s3_2.12-3.6.0-SNAPSHOT.jar",
//      "/usr/local/geotrellis/geotrellis-gdal_2.12-3.6.0-SNAPSHOT.jar",
//    ))
//    .registerKryoClasses(
//      Array(
//        Class.forName("geotrellis.spark.store.kryo.KryoRegistrator"))
//    )
//    .registerKryoClasses(
//      Array(classOf[com.gishorizon.MyRegistrar])
//    )
//    .set("spark.driver.bindAddress","127.0.0.1")
//      .set("spark.driver.host","10.128.0.2")
//    .set("spark.driver.port", "40065")
//    .set("spark.executionEnv.AWS_PROFILE", Properties.envOrElse("AWS_PROFILE", "default"))

  implicit val session: SparkSession = SparkSession.builder.config(conf).enableHiveSupport.getOrCreate
//  session.sparkContext.addJar("G:\\geotrellis-spark_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-gdal_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-raster_2.13-3.6.3.jar")
////  session.sparkContext.addJar("/mnt/data/common/geotrellis-spark-job-assembly-0.1.0.jar")
//  session.sparkContext.addJar("G:\\geotrellis-vector_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-util_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-s3_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-layer_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-macros_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-store_2.13-3.6.3.jar")
//  session.sparkContext.addJar("G:\\geotrellis-proj4_2.13-3.6.3.jar")
  implicit def context: SparkContext = session.sparkContext
  context.setCheckpointDir("/mnt/data/chkpts")
}
