import sys
import os
import base64
import io
import json
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import tweepy
import requests
import botometer
import sqlite3


def cache_file(f, path, filename, file_type="string"):
    """
    Store the user uploaded files to the temp folder.
    :param f: the stringIO or byteIO object
    :param path: the name of the temp folder
    :param filename: the name of the temp file
    :return:
    """
    if f is not None:
        if not os.path.exists(path):
            os.makedirs(path)

        temporary_location = path + "/" + filename

        if file_type == "string":
            g = f
            with open(temporary_location, mode='w') as f:
                print(g.getvalue(), file=f)
        elif file_type == "byte":
            g = io.BytesIO(f.read())
            with open(temporary_location, 'wb') as out:
                out.write(g.read())
        else:
            print("Unknown type of file", file=sys.stderr)


def get_credentials():
    """
    Load credential.json file from the temp folder
    :return:
    """
    try:
        f = open("temp/credentials.json")
    except IOError:
        st.error("Cannot find cached credentials."
                 "Please specify file containing the credentials.")
    else:
        with f:
            credentials = json.load(f)
            return(credentials)


def twitter_login():
    """
    Log in Twitter API
    :return: the api object
    """
    credentials = get_credentials()
    consumer_key = credentials["twitter_app_auth"]["consumer_key"]
    consumer_secret = credentials["twitter_app_auth"]["consumer_secret"]

    auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth)
    if (api.verify_credentials):
        st.success('Twitter API successfully logged in.')
    else:
        st.error('Login failed, please check Twitter credentials.')
    return(api)


def create_connection(db_file):
    """
    Create a database connection to the SQLite database
    specified by db_file. Create the database if not exist
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """
    Create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


def create_new_followers_table(database):
    """
    Create the followers table in the database if not exist.
    screen_name is set to be unique.
    :param db_file: Path to the cached database
    :return:
    """
    sql_create_followers_table = """ CREATE TABLE IF NOT EXISTS followers (
                                        id integer PRIMARY KEY,
                                        screen_name text NOT NULL,
                                        name text,
                                        description text,
                                        followers_count int,
                                        friends_count int,
                                        listed_count int,
                                        favourites_count int,
                                        created_at DATETIME,
                                        en_cap numeric,
                                        en_astroturf numeric,
                                        en_fake_follower numeric,
                                        en_financial numeric,
                                        en_other numeric,
                                        en_overall numeric,
                                        en_self_declared numeric,
                                        en_spammer numeric,
                                        un_cap numeric,
                                        un_astroturf numeric,
                                        un_fake_follower numeric,
                                        un_financial numeric,
                                        un_other numeric,
                                        un_overall numeric,
                                        un_self_declared numeric,
                                        un_spammer numeric,
                                        last_check_date DATETIME,
                                        last_check_status text,
                                        UNIQUE(screen_name)
                                    ); """
    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_followers_table)
    else:
        print("Error! cannot create the database connection.")


def create_follower(conn, follower):
    """
    Create a new follower into the followers table
    :param conn:
    :param follower:
    :return:
    """
    sql = """ INSERT OR IGNORE INTO followers(
                screen_name,
                name,
                description,
                followers_count,
                friends_count,
                listed_count,
                favourites_count,
                created_at)
                VALUES(?,?,?,?,?,?,?,?)
              """
    cur = conn.cursor()
    cur.execute(sql, follower)
    conn.commit()


def save_followers_to_db(user_name, followers):
    """
    Save the followers data returned by Tweepy to SQLite db
    :param user_name: the screen_name of the account for which the followers
    are collected
    :param data: data returned by get_followers()
    :return: None
    """
    database = "temp/" + user_name + "_followers.db"

    # create a database connection
    conn = create_connection(database)
    with conn:
        for i in followers:
            # create a new follower
            follower = (i._json["screen_name"],
                        i._json["name"],
                        i._json["description"],
                        i._json["followers_count"],
                        i._json["friends_count"],
                        i._json["listed_count"],
                        i._json["favourites_count"],
                        i._json["created_at"])
            create_follower(conn, follower)

    st.success("Successfully saved followers to database.")


def get_followers(user_name):
    """
    Get a list of all followers of a twitter account
    :param user_name: twitter username without '@' symbol
           api: Tweepy api
    :return: list of usernames without '@' symbol
    """
    # Check if target account name was given
    if user_name == "":
        st.error("You need to specify a target account name.")
        raise TypeError("user_name is empty")

    api = twitter_login()
    followers = []
    st.info("Begin to retrieve followers of " + user_name + "...")
    for page in tweepy.Cursor(api.followers, screen_name=user_name,
                              wait_on_rate_limit=True, count=200).pages():
        try:
            followers.extend(page)
        except tweepy.TweepError as e:
            st.text("Twitter API limit has been reached.\
                    Continue in 60s.", e)
            time.sleep(60)
    st.success("Completed retrieving all followers of " + user_name)
    return followers


def get_download_link(bin_file, file_label='File'):
    '''
    Generate link to download any files stored on your disk
    :param bin_file: path to the file
           file_label: label of the file that shows in the button
    :return: html link
    '''
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}\
        " download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href


def retrieve_followers_button(user_name):
    """
    Actions took when the "Retrieve followers" button is clicked.
    :param user_name:
    :return:
    """
    # Create the follower database if not exist
    database = "temp/" + user_name + "_followers.db"
    create_new_followers_table(database)

    # Retrieve followers
    followers = get_followers(user_name)

    # Save followers to database
    save_followers_to_db(user_name, followers)

    # Completion message
    st.balloons()
    st.success("Successfully retrieved all the followers!")

    # Display download link
    conn = create_connection(database)
    followers_df = pd.read_sql_query("SELECT * FROM followers", conn)
    followers_csv = "temp/" + user_name + "_followers.csv"
    followers_df.to_csv(followers_csv)
    st.sidebar.markdown(
        get_download_link(followers_csv, 'followers csv table'),
        unsafe_allow_html=True)


def update_follower_db(conn, result):
    """
    Update followers database with the results from bot check
    :param conn:
    :param result:
    :return:
    """
    sql = """ UPDATE followers
              SET en_cap = ? ,
                  en_astroturf = ? ,
                  en_fake_follower = ?,
                  en_financial = ?,
                  en_other = ?,
                  en_overall = ?,
                  en_self_declared = ?,
                  en_spammer = ?,
                  un_cap = ?,
                  un_astroturf = ?,
                  un_fake_follower = ?,
                  un_financial = ?,
                  un_other = ?,
                  un_overall = ?,
                  un_self_declared = ?,
                  un_spammer = ?,
                  last_check_date = ?,
                  last_check_status = ?
              WHERE screen_name = ?"""
    cur = conn.cursor()
    cur.execute(sql, result)
    conn.commit()


def update_follower_db_failed(conn, result):
    """
    Update followers database with the results from bot check
    :param conn:
    :param result:
    :return:
    """
    sql = """ UPDATE followers
              SET last_check_status = "blocked"
              WHERE screen_name = ?"""
    cur = conn.cursor()
    cur.execute(sql, result)
    conn.commit()


def check_bot(screen_name, bom):
    """
    Call the Botometer API to return bot check info for an account
    :param screen_name:
    :param bom:
    :return: result, check_action
    """
    result = (screen_name,)
    try:
        result_js = bom.check_account(screen_name)
        cap = result_js["cap"]
        raw_scores_en = result_js["raw_scores"]["english"]
        raw_scores_un = result_js["raw_scores"]["universal"]

        # Store the following results to tuple
        result = (
            cap["english"],
            raw_scores_en["astroturf"],
            raw_scores_en["fake_follower"],
            raw_scores_en["financial"],
            raw_scores_en["other"],
            raw_scores_en["overall"],
            raw_scores_en["self_declared"],
            raw_scores_en["spammer"],
            cap["universal"],
            raw_scores_un["astroturf"],
            raw_scores_un["fake_follower"],
            raw_scores_un["financial"],
            raw_scores_un["other"],
            raw_scores_un["overall"],
            raw_scores_un["self_declared"],
            raw_scores_un["spammer"],
            datetime.now(),  # stamp with current date and time
            "success",
            screen_name)  # need screen_name here as key

        check_action = "success"
        return(result, check_action)

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            st.text(screen_name + " is a private account, "
                                  "skipping bot check...")
            check_action = "skip"
            return(result, check_action)

        elif status_code == 404:
            st.text(screen_name + " has been suspended or deleted, "
                                  "skipping bot check...")
            check_action = "skip"
            return(result, check_action)

        elif status_code == 403:
            st.error("Botometer account error! "
                     "Please check Rapid API subscription and settings")
            raise requests.exceptions.HTTPError

        elif status_code == 429:
            st.warning("API rate limit reached! The app will pause for 15 "
                       "minutes and try again. Don't close the app.")
            time.sleep(900)
            check_action = "retry"
            return(result, check_action)

        else:
            st.error("HTTP error: " + str(status_code))
            raise requests.exceptions.HTTPError

    except tweepy.TweepError as e:
        error_text = e.response.text
        if "Not authorized" in error_text:
            st.text(screen_name + " is a private account, "
                                  "skipping bot check...")
            check_action = "skip"
            return(result, check_action)
        else:
            st.error("Other Tweepy error: ", error_text)
            raise

    except botometer.NoTimelineError:
        st.text(screen_name + " account does not have enough information, "
                              "skipping bot check...")
        check_action = "skip"
        return(result, check_action)

    except Exception:
        st.error("Unexpected error:", sys.exc_info()[0])
        raise


def check_bot_button(user_name, days_to_keep, account_cap):
    """
    Actions took when the "Check bot" button is clicked.
    :param user_name:
    :return:
    """
    # Check if target account name was given
    if user_name == "":
        st.error("You need to specify a target account name.")
        raise TypeError("user_name is empty")

    # Load credentials
    credentials = get_credentials()
    rapidapi_key = credentials["botometer_auth"]["rapidapi_key"]
    twitter_app_auth = credentials["twitter_app_auth"]

    # Create botometer api
    bom = botometer.Botometer(wait_on_ratelimit=True,
                              rapidapi_key=rapidapi_key,
                              **twitter_app_auth)

    # Load followers table
    database = "temp/" + user_name + "_followers.db"
    try:
        conn = create_connection(database)
    except sqlite3.Error:
        st.error("Cannot find cached database. "
                 "Either run Retrieve Twitter followers function first or"
                 "upload a database.")
        raise sqlite3.Error("Cannot connect to database")
    followers_df = pd.read_sql_query("SELECT * FROM followers", conn)

    # Calculate the total number of followers need to be checked
    # Give it an old date if last_check_date is empty
    old_date = datetime.strptime("01-01-2000", "%d-%m-%Y").date()
    followers_df.last_check_date.fillna(value=old_date, inplace=True)

    followers_df["last_check_date"] = pd.to_datetime(
        followers_df["last_check_date"])
    NOW = datetime.now()

    followers_df["expired"] = (NOW - followers_df["last_check_date"])\
        .astype('timedelta64[D]') > days_to_keep

    is_expired = followers_df["expired"]
    is_not_blocked = followers_df["last_check_status"] != "blocked"
    followers_to_check = followers_df[is_expired
                                      & is_not_blocked]["screen_name"]
    N = sum(is_expired)

    if N > 500:
        st.warning("You have more than 500 followers to check. "
                   "This is beyond the Botometer's daily limit (free plan), "
                   "which may lead to suspension of your Rapid API "
                   "account. Please make sure you set up a daily cap that "
                   "is smaller than 500 or upgrade to a paid plan.")

    # Loop through followers and check bot
    st.info("Starting to check " + str(N) + " followers..."
                                            "This may take a while.")
    i = 0  # initiate counter
    my_bar = st.progress(0)  # initiate progress bar

    for follower in followers_to_check:
        # Check if the daily cap set is reached
        if i >= account_cap:
            st.warning("You have reached the daily cap set. "
                       "Please continue the next day if you are using the "
                       "free plan. Ignore this message and re-run the app "
                       "if you are on the paid plan.")
            break
        i += 1  # counter
        my_bar.progress(i/N)  # update progress bar
        time.sleep(1)  # botometer has 1 sec per request limit
        screen_name = follower

        retry_count = 0
        while True:
            result, action = check_bot(screen_name, bom)
            if action == "success":
                update_follower_db(conn, result)  # store the result to db
                break
            elif action == "skip":
                update_follower_db_failed(conn, result)
                break
            elif action == "retry" and retry_count == 0:
                retry_count += 1
                continue
            elif action == "retry" and retry_count > 0:
                st.error("Doh! Botometer API daily limit is reached. "
                         "Please continue the next day. "
                         "Don't worry, Followers that have "
                         "been checked will not be lost.")
                raise
            else:
                print("Unknown action code!")
                raise

    # Completion message
    st.balloons()
    st.success("Bot checking is completed!")

    # Show download link
    followers_df = pd.read_sql_query("SELECT * FROM followers", conn)
    followers_csv = "temp/" + user_name + "_followers.csv"
    followers_df.to_csv(followers_csv)
    st.sidebar.markdown(
        get_download_link(followers_csv, 'followers csv table'),
        unsafe_allow_html=True)


def download_bot_result_button(user_name, days_to_keep=180):
    """
    Actions took when the "Check bot" button is clicked.
    :param user_name:
    :return:
    """
    # Check if target account name was given
    if user_name == "":
        st.error("You need to specify a target account name.")
        raise TypeError("user_name is empty")

    # Load followers table
    database = "temp/" + user_name + "_followers.db"
    try:
        conn = create_connection(database)
    except sqlite3.Error:
        st.error("Cannot find cached database. "
                 "Either run Retrieve Twitter followers function first or"
                 "upload a database.")
        raise sqlite3.Error("Cannot connect to database")

    # Show download link
    followers_df = pd.read_sql_query("SELECT * FROM followers", conn)
    followers_csv = "temp/" + user_name + "_followers.csv"
    followers_df.to_csv(followers_csv)
    st.sidebar.markdown(
        get_download_link(followers_csv, 'followers csv table'),
        unsafe_allow_html=True)
