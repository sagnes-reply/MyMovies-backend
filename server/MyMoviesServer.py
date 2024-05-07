import base64
import json
from flask import request, Flask, jsonify
from DbManager import DbManager
import mysql.connector
from mysql.connector import Error
import requests

cache_file="cache.sqlite3"
app = Flask(__name__)

dbManager = DbManager()

@app.post('/register')
def register():
    try:
        credentials = request.get_json()
        username = credentials['username']
        password = credentials['password']
        register_user_query = "insert into user values ('"+username+"', aes_encrypt('"+password+"', 'my_key'), '', '', '', '')"
        connection = dbManager.create_db_connection("localhost","root","","mymovies")
        dbManager.execute_query(connection, register_user_query)
        response_data = {
                'message': 'OK'
            }
        print(dbManager.read_query(connection, "select username, aes_decrypt(password,'my_key') from user;"))
        return jsonify(response_data)
    except Error as err:
        print("error in saving data: ", err)
        if err.__class__ == mysql.connector.errors.IntegrityError:
            response_data = {
                    'message': 'USERNAME ALREADY EXISTING'
                }
            return jsonify(response_data)
   

@app.post('/login')
def login():
    try:
        credentials = request.get_json()
        print(credentials)
        username = credentials['username']
        password = credentials['password']
        connection = dbManager.create_db_connection("localhost","root","","mymovies")
        bytearray_pwd = dbManager.read_query(connection, "select aes_decrypt(password, 'my_key') from user where username = '"+username+"';")
   
        if bytearray_pwd == []:
            response_data = {
                'message': 'USER NOT FOUND'
            }
            return jsonify(response_data)
        
        pwd = bytearray_pwd[0][0].decode("utf-8")
        if pwd != password:
            response_data = {
                'message': 'INCORRECT PWD'
            }
            return jsonify(response_data)
        
        print("------LOGIN------")
        response_data = {
                'message': 'OK'
            }
        return jsonify(response_data)
    except Error as err:
        print("error in loading data: ", err)
        response_data = {
            'message': 'ERROR'
        }
        return jsonify(response_data)
        
@app.post("/user_profile")
def user_profile():
    try:
        profile = request.get_json()
        username = profile['username']
        password = profile['password']
        email = profile['email']
        name = profile['name']
        surname = profile['surname']
        genres = profile ['genres']

        connection = dbManager.create_db_connection("localhost","root","","mymovies")

        query = "update user set password = aes_encrypt('"+password+"','my_key'), email ='"+email+"', name ='"+name+"', surname ='"+surname+"', genres = '"+genres+"' where username = '"+username+"';"

        dbManager.execute_query(connection, query)
        response_data = {
            'message': 'OK'
        }

        print("-------USER_PROFILE-------")
        return jsonify(response_data)

    except Error as err:
        print("error in inserting user data: ", err)
        response_data = {
            'message': 'ERROR'
        }
        return jsonify(response_data)

@app.route("/get_user_profile", methods = ["GET"])
def get_user_profile():
    print("----------------------------")
    try:
        username = request.args.get("username")
        query = "select aes_decrypt(password,'my_key'), email, name, surname, genres from user where username = '"+username+"';"

        connection = dbManager.create_db_connection("localhost","root","","mymovies")

        profile = dbManager.read_query(connection, query)
        print(profile)
        password = profile[0][0].decode("utf-8")
        email = profile[0][1]
        name = profile[0][2]
        surname = profile[0][3]
        genres = profile[0][4]

        response_data = {
            'username': username,
            'email': email,
            'name': name,
            'surname': surname,
            'genres': genres
        }

        print("-------GET_USER_PROFILE-------")
        return jsonify(response_data)

    except Error as err:
        print("error in loading user data: ", err)
        response_data = {
            'message': 'ERROR'
        }
        return jsonify(response_data)
    

@app.post("/update_password")
def change_password():
    try:
        username = request.get_json()['username']
        password = request.get_json()['password']
        new_password = request.get_json()['newPassword']
        query = "select aes_decrypt(password,'my_key') from user where username = '"+username+"';"
        connection = dbManager.create_db_connection("localhost","root","","mymovies")

        bytearray_pwd = dbManager.read_query(connection, query)
    
        pwd = bytearray_pwd[0][0].decode("utf-8")
        if pwd != password:
            response_data = {
                'message': 'INCORRECT PWD'
            }
            return jsonify(response_data)
        
        query = "update user set password = aes_encrypt('"+new_password+"','my_key') where username = '"+username+"';"

        dbManager.execute_query(connection, query)
        response_data = {
                'message': 'OK'
            }
        print("-------CHANGE PASSWORD-------")
        return jsonify(response_data)
    
    except Error as err:
        print("error in loading user data: ", err)
        response_data = {
            'message': 'ERROR'
        }
        return jsonify(response_data)
    
@app.route("/get_movies", methods = ["GET"])
def get_movies():
    url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }
    response = requests.get(url, headers=headers)
    movies = create_movie_response(response.json()['results'])

    # Serializza l'array di film in JSON
    return jsonify(movies)

def create_movie_response(raw_response):
    movies = []
    for movie in raw_response:
        movie_dict = dict()
        movie_dict['title'] = movie['title']
        movie_dict['id'] = movie['id']
        movie_dict['overview'] = movie['overview']
        movie_dict['genres'] = convert_genre_id(movie['genre_ids'])
        movie_dict['releaseDate'] = convert_date(movie['release_date'])
        movie_dict['poster'] = get_poster(movie['poster_path'])
        movies.append(movie_dict)
    return movies

@app.route("/get_genres", methods = ["GET"])
def get_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list?language=en"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    genres = response.json()['genres']
    genres_strings = []
    for genre in genres:
        genres_strings.append(genre['id'])
    return genres_strings

def convert_genre_id(ids):
    url = "https://api.themoviedb.org/3/genre/movie/list?language=en"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    genres = response.json()['genres']

    genres_string_array = []
    for movie_id in ids:
        for genre in genres:
            if movie_id == genre['id']:
                genres_string_array.append(genre['name'])

    return genres_string_array

def convert_date(date = ""):
    date = date.split("-")
    new_date = date[2]+"-"+date[1]+"-"+date[0]
    return new_date

def get_poster(poster_url):
    url = "https://image.tmdb.org/t/p/w500" + poster_url
    response = requests.get(url) 
    return base64.b64encode(response.content).decode('utf-8')

app.run(host="0.0.0.0", port="5001")


connection = dbManager.create_db_connection("localhost","root","","mymovies")
#query = "delete from user"
#dbManager.execute_query(connection, query)
print(dbManager.read_query(connection, "select username, aes_decrypt(password,'my_key'), name, surname, email, genres from user;"))


        