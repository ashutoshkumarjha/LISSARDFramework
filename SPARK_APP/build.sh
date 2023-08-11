sbt assembly
mv target/scala-2.13/geotrellis-spark-job-assembly-0.1.0.jar /mnt/data/Server/app.jar

java \
--add-opens=java.base/java.lang=ALL-UNNAMED \
--add-opens=java.base/java.lang.invoke=ALL-UNNAMED \
--add-opens=java.base/java.lang.reflect=ALL-UNNAMED \
--add-opens=java.base/java.io=ALL-UNNAMED \
--add-opens=java.base/java.net=ALL-UNNAMED \
--add-opens=java.base/java.nio=ALL-UNNAMED \
--add-opens=java.base/java.util=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED \
--add-opens=java.base/sun.nio.ch=ALL-UNNAMED \
--add-opens=java.base/sun.nio.cs=ALL-UNNAMED \
--add-opens=java.base/sun.security.action=ALL-UNNAMED \
--add-opens=java.base/sun.util.calendar=ALL-UNNAMED \
--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED \
-cp \
/mnt/data/Server/app.jar \
com.gishorizon.operations.WorkProcess \
'{"inputs":[{"id":"fmarwr","tIndexes":[926823940,926651880,927429139,926046705,927429091,927429115,926046729,928034265,928034289,926046681],"isTemporal":true,"aoiCode":"YTDLILOHPKFDAMOO","dsName":"Landsat_OLI"}],"operations":[{"id":"sa06f7","type":"op_mosaic","inputs":[{"id":"fmarwr","band":0}],"output":{"id":"vao0tb"},"params":"1556668800000#1559260800000#12#months"},{"id":"61d47l","type":"op_ndi","inputs":[{"id":"vao0tb","band":0}],"output":{"id":"vtcg0p"},"params":"vao0tb:3#vao0tb:4"}],"output":{"id":"vtcg0p"}}' \
QKLGKOPHVMKLKWFZ \
/mnt/data/data_dir/tiles/ \
/mnt/data/data_dir/temp_data/ \
http://localhost:8083 \
/mnt/data/data_dir/geoprocess/ \
spark://10.128.0.26:7077 > app.log
