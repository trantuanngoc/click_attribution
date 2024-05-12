from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructType,
    TimestampType,
)

spark = SparkSession.builder.appName('example').getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

click_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "clicks")
    .option("startingOffsets", "earliest")
    .load()
)

click_df1 = click_df.selectExpr("CAST(value AS STRING)", "timestamp")

click_schema = (
    StructType()
    .add("click_id", StringType())
    .add("user_id", StringType())
    .add("product_id", StringType())
    .add("product", StringType())
    .add("price", StringType())
    .add("url", StringType())
    .add("user_agent", StringType())
    .add("ip_address", StringType())
    .add("datetime_occured", TimestampType())
)

click_df2 = (
    click_df1.withColumn("value", from_json(click_df1["value"], click_schema))
    .select("value.*")
    .alias('cl')
    .withWatermark("datetime_occured", "15 seconds")
    .createOrReplaceTempView("clicks")
)

checkout_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "checkouts")
    .option("startingOffsets", "earliest")
    .load()
)

checkout_df1 = checkout_df.selectExpr("CAST(value AS STRING)", "timestamp")

checkout_schema = (
    StructType()
    .add("checkout_id", StringType())
    .add("user_id", StringType())
    .add("product_id", StringType())
    .add("payment_method", StringType())
    .add("total_amount", IntegerType())
    .add("shipping_address", StringType())
    .add("billing_address", StringType())
    .add("user_agent", StringType())
    .add("ip_address", StringType())
    .add("datetime_occured", TimestampType())
)

checkout_df2 = (
    checkout_df1.withColumn(
        "value", from_json(checkout_df1["value"], checkout_schema)
    )
    .select("value.*")
    .alias('co')
    .withWatermark("datetime_occured", "15 seconds")
    .createOrReplaceTempView("checkouts")
)

database_url = "jdbc:postgresql://postgres:5432/postgres"

user_df = (
    spark.read.format('jdbc')
    .option('url', database_url)
    .option('dbtable', 'commerce.users')
    .option('user', 'postgres')
    .option('password', 'postgres')
    .load()
    .alias('u')
    .createOrReplaceTempView("users")
)


enrich = spark.sql(
    """
    SELECT
            co.checkout_id,
            u.username AS user_name,
            cl.click_id,
            co.product_id,
            co.payment_method,
            co.total_amount,
            co.shipping_address,
            co.billing_address,
            co.user_agent,
            co.ip_address,
            co.datetime_occured AS checkout_time,
            cl.datetime_occured AS click_time
        FROM
            checkouts AS co
            JOIN users AS u ON co.user_id = u.id
            LEFT JOIN clicks AS cl ON co.user_id = cl.user_id
            AND co.product_id = cl.product_id
            AND co.datetime_occured BETWEEN cl.datetime_occured
            AND cl.datetime_occured + INTERVAL '1' HOUR
"""
)

def foreach_batch_function(df, epoch_id):
    df = df.dropDuplicates(['checkout_id'])
    df.write.format("jdbc").mode('append').option(
        "url", "jdbc:postgresql://postgres:5432/postgres"
    ).option("dbtable", "commerce.attributed_checkouts").option(
        "user", "postgres"
    ).option(
        "password", "postgres"
    ).save()


enrich.writeStream.foreachBatch(
    foreach_batch_function
    ).start().awaitTermination()


