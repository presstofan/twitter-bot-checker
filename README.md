# Twitter Bot Checker Powered by Botometer

A Streamlit app that retrieves all the followers of a Twitter account and use [Botometer API](https://botometer.osome.iu.edu/) to check for bots.

## How to use

### Download and set up the Streamlit app

```{sh}
git clone https://github.com/presstofan/twitter-bot-checker
cd twitter-bot-checker
pip install -r requirements.txt
streamlit run app.py
```

### Get the Twitter and Botometer Rapid API credentials

Please see [this page](https://github.com/IUNetSci/botometer-python#rapidapi-and-twitter-access-details) for setting up the credentials.

### Use the app to retrieve followers and check for bots

1. Select the JSON file that contains the Twitter and Botometer credentials. credentials.json is a template of credential file, which can be found with the app. Credential loaded will be cached for later use.
2. Provide an existing database. If not provided, the app will look for database in the temp folder. If no cached database available, a new database will be created.
3. Specify the account whose followers need to be checked, and set the timeframe you want to keep the bot check data.
4. Run "Retrieve Twitter followers", which uses Tweepy API to retrieve all the followers of a specific account. If a database is provided or cached in the temp folder, the app will only add new followers that are not already in the database. If no database is available, the app will create a new database from scratch.
5. Run "Check bot", which call the Botometer Rapid API to check for bot in the database. It will not re-check the followers unless the bot data is expired. A download link will be available at the bottom of the sidebar when the process is completed. Alternatively, you can click the "Download bot check results" button to get the download link.
