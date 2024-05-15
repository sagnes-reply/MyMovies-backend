
import mysql.connector
from mysql.connector import Error
import pandas as pd

class DbManager:
    def __init__(self) -> None:
        pass

    def create_server_connection(self, host_name, user_name, user_password):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=host_name,
                user=user_name,
                passwd=user_password
            )
            print("MySQL Database connection successful")
        except Error as err:
            print(f"Error: '{err}'")

        return connection
    
    def create_database(self, connection, query):
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            print("Database created successfully")
        except Error as err:
            print(f"Error: '{err}'")

    def create_db_connection(self, host_name, user_name, user_password, db_name):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=host_name,
                user=user_name,
                passwd=user_password,
                database=db_name
            )
            #print("MySQL Database connection successful")
        except Error as err:
            print(f"Error: '{err}'")

        return connection
    
    def execute_query(self, connection, query):
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        #print("Query successful")

    def read_query(self, connection, query):
        cursor = connection.cursor()
        result = None
        cursor.execute(query)
        result = cursor.fetchall()
        return result
       
    


db = DbManager()
#connection = db.create_server_connection("localhost", "root", "")

# query = "create database if not exists mymovies"
# db.create_database(connection, query)
# # ------ creating tables ----------
# user_table_query = """
# create table if not exists user (
#     username varchar(20) primary key,
#     password varchar(20) not null
# );
# """

connection = db.create_db_connection("localhost","root","","mymovies")
#print(db.read_query(connection, "select * from user;"))
#db.execute_query(connection, "insert into user values ('Sabrina', aes_encrypt('1234','my_key'), 'sabrina@gmail.it', 'Sabrina', 'Agnes', 'Comedy,');")
#res = db.read_query(connection, query = "select aes_decrypt(password,'my_key'), email, name, surname, genres from user where username = 'Sabrina';")
#print(res[0][0])

query = """
    create table if not exists user_favourite_tvshows (
    user varchar(20) references user(username),
    tvshow_id int(15),
    primary key (user, tvshow_id)
 );
 """
db.execute_query(connection, query)