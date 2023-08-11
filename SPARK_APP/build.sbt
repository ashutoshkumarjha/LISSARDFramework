name := "geotrellis-spark-job"
organization := "com.gishorizon"
version := "0.1.0"
//2.13.8, 2.12.15
scalaVersion := "2.13.8"
mainClass := Some("com.gishorizon.operations.WorkProcess")
val akkaV       = "2.7.0"
val akkaHttpV   = "10.4.0"
retrieveManaged := true

libraryDependencies ++= Seq(
  "com.monovore" %% "decline" % "1.2.0",
  "org.locationtech.geotrellis" %% "geotrellis-spark" % "3.6.3",
  "org.locationtech.geotrellis" %% "geotrellis-s3" % "3.6.3",
  "org.locationtech.geotrellis" %% "geotrellis-raster" % "3.6.3",
  "org.locationtech.geotrellis" %% "geotrellis-vector" % "3.6.3",
  "org.locationtech.geotrellis" %% "geotrellis-gdal" % "3.6.3",
  "org.locationtech.geotrellis" %% "geotrellis-s3" % "3.6.3",
  "com.typesafe.akka" %% "akka-actor" % akkaV,
  "com.typesafe.akka" %% "akka-stream" % akkaV,
  "com.typesafe.akka" %% "akka-http" % akkaHttpV,
  "com.typesafe.akka" %% "akka-http-spray-json" % akkaHttpV,
  "com.typesafe.akka" %% "akka-http-testkit" % akkaHttpV,
  "ch.megard" %% "akka-http-cors" % "1.1.3",
  "org.apache.spark" %% "spark-core" % "3.3.2",
  "org.apache.spark" %% "spark-sql" % "3.3.2",
  "org.apache.spark" %% "spark-hive" % "3.3.2",
  "org.apache.spark" %% "spark-mllib" % "3.3.2",
  "org.apache.hadoop" % "hadoop-common" % "3.3.2",
  "org.apache.hadoop" % "hadoop-mapreduce-client-core" % "3.3.2",
  "com.typesafe.play" %% "play-json" % "2.9.4",
  "org.postgresql" % "postgresql" % "42.5.4"
)

console / initialCommands :=
"""
import java.net._
import geotrellis.layer._
import geotrellis.vector._
import geotrellis.raster._
import geotrellis.raster.gdal._
import geotrellis.spark._
import com.gishorizon._
""".stripMargin

// Fork JVM for test context to avoid memory leaks in Metaspace
Test / fork := true
Test / outputStrategy := Some(StdoutOutput)

// Settings for sbt-assembly plugin which builds fat jars for spark-submit
assembly / assemblyMergeStrategy := {
  case "reference.conf"   => MergeStrategy.concat
  case "application.conf" => MergeStrategy.concat
  case PathList("META-INF", xs @ _*) =>
    xs match {
      case ("MANIFEST.MF" :: Nil) =>
        MergeStrategy.discard
      case ("services" :: _ :: Nil) =>
        MergeStrategy.concat
      case ("javax.media.jai.registryFile.jai" :: Nil) | ("registryFile.jai" :: Nil) | ("registryFile.jaiext" :: Nil) =>
        MergeStrategy.concat
      case (name :: Nil) if name.endsWith(".RSA") || name.endsWith(".DSA") || name.endsWith(".SF") =>
        MergeStrategy.discard
      case _ =>
        MergeStrategy.first
      }
  case _ => MergeStrategy.first
}

// Settings from sbt-lighter plugin that will automate creating and submitting this job to EMR
import sbtlighter._

sparkEmrRelease := "emr-6.4.0"
sparkAwsRegion := "us-east-1"
sparkClusterName := "geotrellis-spark-job"
sparkEmrApplications := Seq("Spark", "Zeppelin", "Ganglia")
sparkJobFlowInstancesConfig := sparkJobFlowInstancesConfig.value.withEc2KeyName("geotrellis-emr")
sparkS3JarFolder := "s3://geotrellis-test/jobs/jars"
sparkS3LogUri := Some("s3://geotrellis-test/jobs/logs")
sparkMasterType := "m4.xlarge"
sparkCoreType := "m4.xlarge"
sparkInstanceCount := 5
sparkMasterPrice := Some(0.5)
sparkCorePrice := Some(0.5)
sparkEmrServiceRole := "EMR_DefaultRole"
sparkInstanceRole := "EMR_EC2_DefaultRole"
sparkMasterEbsSize := Some(64)
sparkCoreEbsSize := Some(64)
sparkEmrBootstrap := List(
  BootstrapAction(
    "Install GDAL",
    "s3://geotrellis-demo/emr/bootstrap/conda-gdal.sh",
    "3.1.2"
  )
)
sparkEmrConfigs := List(
  EmrConfig("spark").withProperties(
    "maximizeResourceAllocation" -> "true"
  ),
  EmrConfig("spark-defaults").withProperties(
    "spark.driver.maxResultSize" -> "3G",
    "spark.dynamicAllocation.enabled" -> "true",
    "spark.shuffle.service.enabled" -> "true",
    "spark.shuffle.compress" -> "true",
    "spark.shuffle.spill.compress" -> "true",
    "spark.rdd.compress" -> "true",
    "spark.driver.extraJavaOptions" ->"-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
    "spark.executor.extraJavaOptions" -> "-XX:+UseParallelGC -XX:+UseParallelOldGC -XX:OnOutOfMemoryError='kill -9 %p'",
    "spark.yarn.appMasterEnv.LD_LIBRARY_PATH" -> "/usr/local/miniconda/lib/:/usr/local/lib",
    "spark.executorEnv.LD_LIBRARY_PATH" -> "/usr/local/miniconda/lib/:/usr/local/lib"
  ),
  EmrConfig("yarn-site").withProperties(
    "yarn.resourcemanager.am.max-attempts" -> "1",
    "yarn.nodemanager.vmem-check-enabled" -> "false",
    "yarn.nodemanager.pmem-check-enabled" -> "false"
  )
)
