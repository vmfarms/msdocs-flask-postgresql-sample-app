```bash
# login
sidepro login

# push and build the app
sidepro push --name msdocs

# take a look at the logs to understand why the app is not running properly
sidepro app logs msdocs                                     

# create the required database
sidepro service create postgresql-dev msdocs-db2

# create and configure the app
sidepro app update msdocs \
    --env DBNAME='$(PSQL_DB_NAME)' \
    --env DBHOST='$(PSQL_HOSTNAME)' \
    --env DBUSER='$(PSQL_USERNAME)' \
    --env DBPASS='$(PSQL_PASSWORD)' \
    --chart-value appListeningPort=5000 \
    --chart-value memory="512Mi"

# bind the database to the app
sidepro service bind msdocs-db msdocs

# connect to the app and run database migration
sidepro app exec msdocs
export PYTHONPATH=/layers/heroku_python/dependencies/lib/python3.12/site-packages/:$PYTHONPATH
export PATH=$PATH:/layers/heroku_python/dependencies/bin/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/layers/heroku_python/python/lib/
flask db upgrade
exit

# show database configuration
sidepro configuration list
sidepro configuration show YOUR-CONFIG-NAME
```
