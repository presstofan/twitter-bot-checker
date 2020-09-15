import streamlit as st
from utils import (
    cache_file,
    retrieve_followers_button,
    check_bot_button,
    download_bot_result_button
)


st.set_option('deprecation.showfileUploaderEncoding', False)

# App (Main Window)
st.title("Twitter Bot Checker Powered by Botometer")
st.markdown("""
    Version 0.1

    A Streamlit app that retrieves all the followers of a Twitter account
    and use [Botometer API](https://botometer.osome.iu.edu/) to check for
    bots. Please follow the instructions below to use the app. Please see
    [this page](https://github.com/IUNetSci/botometer-python) for setting
    up the credentials.

    **Step 1:** Select the JSON file that contains the Twitter and
    Botometer credentials. credentials.json is a template of credential file,
    which can be found with the app. Credential loaded will be cached for later
    use.

    **Step 2:** Provide an existing database. If not provided, the app will
    look for database in the temp folder. If no cached database available, a
    new database will be created.

    **Step 3:** Specify the account whose followers need to be checked, and set
    the timeframe you want to keep the bot check data.

    **Step 4:** Run "Retrieve Twitter followers", which uses Tweepy API to
    retrieve all the followers of a specific account. If a database is
    provided or cached in the temp folder, the app will only add new
    followers that are not already in the database. If no database is
    available, the app will create a new database from scratch.

    **Step 5:** Run "Check bot", which call the Botometer Rapid API to check
    for bot in the database. It will not re-check the followers unless
    the bot data is expired. A download link will be available at the bottom
    of the sidebar when the process is completed. Alternatively, you can
    click the "Download bot check results" button to get the download link.
    """)

# App (Side Bar)
st.sidebar.title("Settings")
credentials_file = st.sidebar.file_uploader(
    "Select the json file that contains the Twitter and Botometer credentials",
    type=["json"])
cache_file(credentials_file, "temp", "credentials.json")
db_file = st.sidebar.file_uploader(
    "Select a database (if not provided, the app will look for database "
    "in the temp folder. If no cached database available, "
    "a new database will be created.",
    type=["db"])
cache_file(db_file, "temp", "db")
account_name = st.sidebar.text_input('Twitter Account Handler (without"@"):')
days_to_keep = st.sidebar.number_input("Number of days before the\
     bot data expires:", min_value=0, max_value=360, value=180)
account_cap = st.sidebar.number_input("Accounts Check\
     Daily cap:", min_value=0, value=480)

st.sidebar.title("Functions")
# Retrieve Twitter followers
if st.sidebar.button("Retrieve Twitter followers"):
    retrieve_followers_button(account_name)

# Check bot
if st.sidebar.button("Check bot"):
    check_bot_button(account_name, days_to_keep, account_cap)

# Download results
if st.sidebar.button("Download bot check results"):
    download_bot_result_button(account_name)
