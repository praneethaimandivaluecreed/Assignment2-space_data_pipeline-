Assignment2-space_data_pipeline/
│
├── data/
│   │
│   ├── raw/
│   │   │
│   │   ├── agencies/
│   │   │   ├── page_1.json
│   │   │   ├── page_2.json
│   │   │   ├── page_3.json
│   │   │   └── page_4.json
│   │   │
│   │   ├── launcher_configurations/
│   │   │   ├── page_1.json
│   │   │   ├── page_2.json
│   │   │   ├── page_3.json
│   │   │   ├── page_4.json
│   │   │   ├── page_5.json
│   │   │   └── page_6.json
│   │   │
│   │   ├── launches/
│   │   │   ├── page_1.json
│   │   │   └── page_2.json
│   │   │
│   │   └── pads/
│   │       └── page_3.json
│   │
│   └── processed/
│       ├── agencies.csv
│       ├── launcher_configurations.csv
│       ├── launches.csv
│       └── pads.csv
│
├── sql/
│   ├── .vs/
│   ├── 01_create_agencies.sql
│   ├── 02_create_launcher_configurations.sql
│   ├── 03_create_pads.sql
│   └── 04_create_launches.sql
│
├── src/
│   ├── __pycache__/
│   ├── logs/
│   │   └── pipeline.log
│   │
│   ├── extract.py
│   ├── failure_scenario.py
│   ├── load.py
│   ├── logger.py
│   ├── main.py
│   ├── transform.py
│   └── validate.py
│
├── .env
├── .gitignore
└── README.md


## Project Structure

- `data/raw/` - Stores raw JSON data extracted from the SpaceDevs API.
- `data/processed/` - Stores cleaned and transformed CSV datasets.
- `sql/` - Contains SQL scripts used to create the database tables.
- `src/extract.py` - Extracts data from the API and stores it in raw files.
- `src/transform.py` - Cleans and transforms raw data into processed CSV files.
- `src/validate.py` - Performs data quality and validation checks.
- `src/load.py` - Loads processed data into SQL Server.
- `src/failure_scenario.py` - Tests transaction rollback behavior.
- `src/main.py` - Runs the complete ETL pipeline.
- `src/logger.py` - Configures pipeline logging.
- `src/logs/pipeline.log` - Stores pipeline execution logs.
- `.env` - Stores database and environment configuration.
- `.gitignore` - Specifies files and folders that should not be committed to Git.
- `README.md` - Contains project documentation.