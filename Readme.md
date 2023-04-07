
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




