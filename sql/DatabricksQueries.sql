select count(*) from workspace.nyc_taxi_aws.bronze_taxi_trips--Bronze table count
select count(*) from workspace.nyc_taxi_aws.silver_taxi_trips_curated;--Silver table count
select total_records from workspace.nyc_taxi_aws.data_quality_aws order by execution_timestamp desc;--Data quality table count

--Gold Tables verification
select pickup_date from workspace.nyc_taxi_aws.gold_daily_metrics_aws order by pickup_date limit 10;
select * from workspace.nyc_taxi_aws.gold_hourly_metrics_aws;--
select * from workspace.nyc_taxi_aws.gold_payment_metrics_aws;
select * from workspace.nyc_taxi_aws.gold_vendor_metrics_aws;

----Pipeline monitoring table verification
select * from workspace.nyc_taxi_aws.pipeline_monitoring;

------to verify the latest file is loaded---------
Select tpep_pickup_datetime,tpep_dropoff_datetime from workspace.nyc_taxi_aws.bronze_taxi_trips
where tpep_pickup_datetime between '2026-01-01' and '2026-04-01' order by tpep_pickup_datetime desc

------To check duplicates-----------------
SELECT
    trip_record_hash,
    COUNT(*) AS cnt
FROM workspace.nyc_taxi_aws.silver_taxi_trips_curated
GROUP BY trip_record_hash
HAVING COUNT(*) > 1
LIMIT 1;

------verify the dashbaord metrics table is created and loaded with data
select * from workspace.nyc_taxi_aws.gold_dashboard_metrics_aws

