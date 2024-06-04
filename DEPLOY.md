epinio service create crossplane-postgresql-dev msdocs-db
epinio app create msdocs \
    --env DBNAME='$(PSQL_DB_NAME)' \
    --env DBHOST='$(PSQL_HOSTNAME)' \
    --env DBUSER='$(PSQL_USERNAME)' \
    --env DBPASS='$(PSQL_PASSWORD)' \
    --chart-value appListeningPort=5000
epinio service bind msdocs-db msdocs
epinio app push -n msdocs --builder-image heroku/builder:22
epinio app exec msdocs

```bash
export PYTHONPATH=/layers/heroku_python/dependencies/lib/python3.12/site-packages/:$PYTHONPATH
export PATH=$PATH:/layers/heroku_python/dependencies/bin/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/layers/heroku_python/python/lib/
flask db upgrade
```
