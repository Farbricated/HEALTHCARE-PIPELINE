.PHONY: install test run clean lint format

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=src --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

run-etl:
	python src/etl/loaders.py

run-streamlit:
	streamlit run streamlit_app.py

run-airflow:
	airflow db init
	airflow webserver --port 8080 &
	airflow scheduler

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker build -t healthcare-supply-chain .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

init-db:
	python scripts/init_database.py

seed-data:
	python scripts/seed_data.py

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make run-etl       - Run ETL pipeline"
	@echo "  make run-streamlit - Run Streamlit dashboard"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean cache files"