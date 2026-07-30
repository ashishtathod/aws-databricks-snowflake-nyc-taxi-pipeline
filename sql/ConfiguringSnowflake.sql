---To create a warehouse, database and schema in snowflake for our NYC taxi pipeline
CREATE OR REPLACE WAREHOUSE COMPUTE_WH
WITH
WAREHOUSE_SIZE = 'XSMALL'
AUTO_SUSPEND = 60
AUTO_RESUME = TRUE
INITIALLY_SUSPENDED = TRUE;


CREATE OR REPLACE DATABASE NYC_TAXI_DB;


CREATE OR REPLACE SCHEMA NYC_TAXI_DB.ANALYTICS;

USE WAREHOUSE COMPUTE_WH;--use created warehouse

USE DATABASE NYC_TAXI_DB;--use created DB

USE SCHEMA ANALYTICS;--use created Schema


SHOW DATABASES;--verify DB

SHOW SCHEMAS;--verify schema

SHOW WAREHOUSES;--verify warehouses


CREATE OR REPLACE STORAGE INTEGRATION nyc_taxi_s3_int
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = S3
ENABLED = TRUE
STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::215939711325:role/SnowflakeAnalyticsReadRole'
STORAGE_ALLOWED_LOCATIONS = (
's3://ashish-nyc-taxi-lakehouse/analytics/'
);---create storage integration for integrating S3 bucket to snowflake


DESC STORAGE INTEGRATION nyc_taxi_s3_int;--to look up for external id and arn id

CREATE OR REPLACE FILE FORMAT parquet_format
TYPE = PARQUET;---create file format for our parquet files


SHOW FILE FORMATS;--verify file formats


CREATE OR REPLACE STAGE analytics_stage
URL = 's3://ashish-nyc-taxi-lakehouse/analytics/'
STORAGE_INTEGRATION = nyc_taxi_s3_int
FILE_FORMAT = parquet_format;-----Create a stage pointing to your analytics folder.


--Test the Connection
LIST @analytics_stage;

--Inspect a Folder
LIST @analytics_stage/dashboard/gold_dashboard_metrics_aws;


--Automatically Infer the Schema
SELECT *
FROM TABLE(
    INFER_SCHEMA(
        LOCATION => '@analytics_stage/dashboard/gold_dashboard_metrics_aws',
        FILE_FORMAT => 'parquet_format'
    )
);


--Now generate the DDL automatically
CREATE OR REPLACE TABLE GOLD_DASHBOARD_METRICS
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => '@analytics_stage/dashboard/gold_dashboard_metrics_aws',
            FILE_FORMAT => 'parquet_format'
        )
    )
);

--verify the table
DESC TABLE GOLD_DASHBOARD_METRICS;

--load the data
COPY INTO GOLD_DASHBOARD_METRICS
FROM @analytics_stage/dashboard/gold_dashboard_metrics_aws
FILE_FORMAT = (FORMAT_NAME = parquet_format)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
PATTERN = '.*\.parquet';


