
0. Clone repo and cd into it
```bash
git clone <this repo>
cd <this repo>

export PYTHONPATH=$PWD
```

1. Parse all fights statistics
```bash
python src/pipelines/parse_all_fights.py --save_path=<where to save .json result>
```

## Start prefect cloud

1. 
```bash
prefect orion start
```

2.
```bash
 prefect agent start --pool default-agent-pool --work-queue default
 ```

3. Run a flow that parses data and loads it to minio with
```bash
python src/pipelines/flows/parse_and_save_to_minio.py
```

3.1 Alternatively (preferably) you can set parsing on schedule
```bash
prefect deployment build src/pipelines/flows/parse_and_save_to_minio.py:load_data_to_minio -n parse_data_and_load_to_minio -a
```


