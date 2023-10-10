# Stream processinig


Assume we run an e-commerce website. An everyday use case with e-commerce is to identify, for every product purchased, the click that led to this purchase. Attribution is the joining of checkout(purchase) of a product to a click. There are multiple types of **[attribution](https://www.shopify.com/blog/marketing-attribution#3)**; we will focus on `First Click Attribution`. 

Our objectives are:
 1. Enrich checkout data with the user name. The user data is in a transactional database.
 2. Identify which click leads to a checkout (aka attribution). For every product checkout, we consider **the earliest click a user made on that product in the previous hour to be the click that led to a checkout**.
 3. Log the checkouts and their corresponding attributed clicks (if any) into a table.



## Architecture

Our streaming pipeline architecture is as follows (from left to right):

1. **`Application`**: Website generates clicks and checkout event data.
2. **`Queue`**: The clicks and checkout data are sent to their corresponding Kafka topics.
3. **`Stream processing`**: 
   1. Flink reads data from the Kafka topics.
   2. The click data is stored in our cluster state. Note that we only store click information for the last hour, and we only store one click per user-product combination. 
   3. The checkout data is enriched with user information by querying the user table in Postgres.
   4. The checkout data is left joined with the click data( in the cluster state) to see if the checkout can be attributed to a click.
   5. The enriched and attributed checkout data is logged into a Postgres sink table.
4. **`Monitoring & Alerting`**: Apache Flink metrics are pulled by Prometheus and visualized using Graphana.

![Architecture](./assets/images/arch.png)



