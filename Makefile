up:
	docker compose up --build -d

down:
	docker compose down

run-checkout-attribution-job:
	docker exec jobmanager spark-submit  ./code/checkout_attribution.py

sleep:
	sleep 20 
