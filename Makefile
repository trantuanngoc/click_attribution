up:
	docker compose up --build -d

down:
	docker compose down

run-checkout-attribution-job:
	docker exec spark-job spark-submit  \
		--driver-class-path "/opt/spark/postgre_jdbc.jar" \
		--packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0" \
		/opt/spark/code/checkout_attribution.py

run: down up sleep run-checkout-attribution-job

sleep:
	sleep 20 
