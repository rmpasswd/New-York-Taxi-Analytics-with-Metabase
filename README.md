# New-York-Taxi-Analytics-with-Metabase
<img width="1401" height="902" alt="image" src="https://github.com/user-attachments/assets/8e2627f5-e066-4c02-8730-03458c4a9e54" />

**1. Average of Fare Amount by each Hour (24x30days)**
   - Learned the difference between `TRUNC` VS `EXTRACT`. TRUNC ('hour', datetime) will only _truncate_ the smaller durations, e.g. minutes, seconds, but not the date. Hence trunc will still produce 30 days times 24 hour = 700+ datapoints.
    <img width="2096" height="660" alt="Metabase-Average of Fare Amount by each Hour (24x30days)-7_2_2026, 4_34_50 PM" src="https://github.com/user-attachments/assets/a3711970-be47-4c8d-8793-ce1feda13974" />

**2. Average of Fare Amount by each Hour (00 to 23)**  
  - This is a crucial metric to know when in a day the fares are the highest or lowest. (Early bird gets the ~~worm~~ fare!)
    ```
    SELECT
    AVG("public"."yellow_tripdata_2026_03"."fare_amount") AS "avg",
    EXTRACT(
      HOUR FROM "public"."yellow_tripdata_2026_03"."tpep_pickup_datetime"
    ) AS "tpep_pickup_datetime"
    FROM
    "public"."yellow_tripdata_2026_03"
    GROUP BY
    EXTRACT(
      HOUR FROM "public"."yellow_tripdata_2026_03"."tpep_pickup_datetime"
    )
       
    ```
    <img width="1482" height="735" alt="Metabase-Average of Fare Amount by each Hour (00 to 23)-7_2_2026, 4_35_03 PM" src="https://github.com/user-attachments/assets/8f607a63-72f2-41a0-87cd-5e2dac2a5b01" />

**3. Average Tip Amount X Passenger Count**  
  - I was wondering whether peopled tipped more or less depending on how much were travelling, not much difference!
    <img width="602" height="695" alt="Metabase-Average Tip Amount X Passenger Count-7_2_2026, 4_35_08 PM" src="https://github.com/user-attachments/assets/f3e1f99b-6646-40b8-9cee-57e1dd2437f0" />

**4. Distribution of Taxi Pickups across NYC**  
   - It seems that airports are the place to be!
   - I wanted to present this in a treemap but Metabase do not support that visualization; a traditional bar chart it is then.
   - The main issue was the location names were in another dataset, downloaded the csv, made a left join with zone-lookup table:
     ```
     with merged as (
      SELECT
      	"public"."taxi_zone_lookup_20260702083039"."zone" as zone, "yellow_tripdata_2026_03"."tpep_pickup_datetime"
      FROM
        "public"."taxi_zone_lookup_20260702083039"
        LEFT JOIN "public"."yellow_tripdata_2026_03" ON "public"."taxi_zone_lookup_20260702083039"."locationid" = "yellow_tripdata_2026_03"."PULocationID"
        )
      
      SELECT zone, count(*)
      from merged
      group by zone
      ORDER BY zone asc
     ```
      <img width="2096" height="1211" alt="Metabase-Distribution of Taxi Pickups across NYC-7_2_2026, 4_35_12 PM" src="https://github.com/user-attachments/assets/0b4b7056-69e1-4f53-bf40-97d2359aad6b" />


### Deployment:
1. To actually deploy it publically, the metabase installation has to be installed in a 'server', be it my own  laptop or an AWS EC2 instance. I was already using it in a docker container. Took a snapshot with `docker commit container_id   rmpasswd/metabase-taxi:1.0` then after making sure I am logged in with `docker login`,  pushed the image to my own docker hub registry with `docker push rmpasswd/metabase-taxi:1.0`.
2. From a cloud VM(because I will not run my lapto 24/7), I simply logged in again (because I'll be pulling from my private registry) and `sudo docker run -d -p 3000:3000 --name metabase rmpasswd/metabase-taxi:1.0`
3. todo: metabase takes up 1GB+ memory, allocate bigger machine
4. todo: reverse proxy to serve different ports, metabase with other apps, in same VM.



