# Clothing Scraper and API

This project is a web scraping application built with Scrapy and FastAPI, designed to extract clothing product information from various e-commerce websites. It includes a PostgreSQL database for storing scraped data and a RESTful API for managing products and triggering scraping jobs.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [Docker Setup](#docker-setup)
  - [Python Virtual Environment Setup](#python-virtual-environment-setup)
- [Running the Application](#running-the-application)
  - [Running the API](#running-the-api)
  - [Running Spiders](#running-spiders)
- [Celio Spider Specifics](#celio-spider-specifics)

## Features
- Web scraping using Scrapy.
- RESTful API with FastAPI for product management (CRUD operations).
- PostgreSQL database for data storage.
- Dockerized setup for easy deployment.
- Support for multiple e-commerce websites (Bershka, Canda, Celio, Nike, Pull&Bear).

## Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.12
- pip (Python package installer)
- venv (Python virtual environment)

## Setup

### Docker Setup

1.  **Build the Docker images:**
    Navigate to the project root directory and run:
    ```bash
    docker-compose build
    ```

2.  **Start the Docker containers:**
    This will start the PostgreSQL database and the FastAPI application.
    ```bash
    docker-compose up -d
    ```
    You can verify that the containers are running using `docker-compose ps`.

3.  **Initialize the database:**
    Run the database setup command within the `app` container. This will create the necessary tables.
    ```bash
    docker-compose exec app python main.py setup
    ```

### Python Virtual Environment Setup

While the application can run entirely within Docker, you might want to set up a local Python virtual environment for development, running tests, or executing spiders directly.

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    ```

2.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

### Running the API

The API runs automatically when you start the Docker Compose services (`docker-compose up -d`). It will be accessible at `http://localhost:8000`.

You can access the API documentation (Swagger UI) at `http://localhost:8000/docs`.

### Running Spiders

You can run individual spiders either directly from your local Python environment or within the Docker `app` container.

**From local Python environment (after virtual environment setup):**
```bash
python main.py scrape --spider <spider_name>
```
Replace `<spider_name>` with one of the available spiders (e.g., `pullandbear`, `bershka`, `canda`, `nike`, `celio`).

Example:
```bash
python main.py scrape --spider bershka
```

**From Docker `app` container:**
```bash
docker-compose exec app python main.py scrape --spider <spider_name>
```
Example:
```bash
docker-compose exec app python main.py scrape --spider canda
```

## Celio Spider Specifics

The `celio` spider uses `undetected_chromedriver` and `python-2captcha` to bypass advanced bot detection and CAPTCHAs.

-   Ensure your local Chrome browser is updated to a version compatible with `undetected_chromedriver`.
-   You need to provide your 2Captcha API key in `clothing_scraper/downloaders_celio.py` for the CAPTCHA solving to work. Look for the placeholder `'YOUR_2CAPTCHA_API_KEY'` and replace it with your actual key.
