## Set up path to your database
1. Change `server\cellstar_server\app\settings.py`:
`DB_PATH` variable should point to the path to your database that was build using preprocessor. Assuming you followed example https://github.com/aliaksei-chareshneu/cellstar-volume-server-v2/blob/main/readme_new_preprocessor.md, it should be set to `test_db`

2. Run `server\cellstar_server\serve.py` from repository root after activating environment:
```
python server\cellstar_server\serve.py
```