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
    print("------- GET MOVIES ---------")
    username = request.args.get("username")
    lang = request.args.get("lang")
    url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language="+lang+"&page=1&sort_by=popularity.desc"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }
    response = requests.get(url, headers=headers)
    array_id = get_favourites(username)
    movies = create_movie_response(response.json()['results'], array_id)
    # Serializza l'array di film in JSON
    return jsonify(movies)

def create_movie_response(raw_response, array_id):
    movies = []
    for movie in raw_response:
        movie_dict = dict()
        movie_dict['title'] = movie['title']
        movie_dict['id'] = movie['id']
        movie_dict['overview'] = movie['overview']
        movie_dict['genres'] = (movie['genre_ids'])
        movie_dict['releaseDate'] = convert_date(movie['release_date'])
        movie_dict['poster'] = get_poster(movie['poster_path'])
        movie_dict['favourite'] = check_favourite(movie['id'], array_id)
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
        genres_strings.append(genre['name'])
   
    #get tv shows genres
    url = "https://api.themoviedb.org/3/genre/tv/list?language=en"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    genres = response.json()['genres']
  
    for genre in genres:
        if genre['name'] not in genres_strings:
            genres_strings.append(genre['name'])

    return genres_strings


def convert_genre_id(ids):
    url = "https://api.themoviedb.org/3/genre/movie/list?language=en"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    genres = response.json()['genres']

    genres_string = ""
    for movie_id in ids:
        for genre in genres:
            if movie_id == genre['id']:
                genres_string = genres_string + genre['name']+" - "
    if len(genres_string) >= 2:
        genres_string = genres_string[:-2]
    return genres_string

def convert_date(date = ""):
    date = date.split("-")
    new_date = date[2]+"-"+date[1]+"-"+date[0]
    return new_date

def get_poster(poster_url):
    url = "https://image.tmdb.org/t/p/w500" + poster_url
    
    return url

def get_favourites(username):
    connection = dbManager.create_db_connection("localhost","root","","mymovies")
    query = "select movie_id from user_favourites where user='"+username+"'"
    res = dbManager.read_query(connection, query) #[(693134],), (934632,), (940721,)]
    array_id = [tupla[0] for tupla in res] 
    return array_id

def check_favourite(movie_id, array_id):
    if movie_id in array_id:
        return True
    else:
        return False


@app.post("/update_favourite_movies")
def update_favourite_movies():
    try:
        username = request.get_json()['username']
        movie_id = str(request.get_json()['id'])
        print("-------- UPDATE FAVOURITES ---------")
        query = "select * from user_favourites where user = '"+username+"' and movie_id = '"+movie_id+"'"
        connection = dbManager.create_db_connection("localhost","root","","mymovies")
        res = dbManager.read_query(connection, query)
        #se non trovo righe con username,movie_id inserisco il movie_id preferito per username
        if len(res) == 0:
            query = "insert into user_favourites values('"+username+"','"+movie_id+"');"
            dbManager.execute_query(connection, query)
            return jsonify(True), 200
        #se la trovo vuol dire che lo user ha rimosso quel film dai preferiti quando arrivo a questo punto
        else:
            query = "delete from user_favourites where user = '"+username+"' and movie_id = '"+movie_id+"'"
            dbManager.execute_query(connection, query)
            return jsonify(False), 200
       
        
    except Error as err:
        print("error in updeting user favourite movies: ", err)
        return jsonify(False), 500


#----------------------------------------------------- TV SHOWS ----------------------------------------------------------------------------
@app.route("/get_tv_shows", methods = ["GET"])
def get_tv_shows():
    print("------- GET TV SHOWS ---------")
    username = request.args.get("username")
    lang = request.args.get("lang")
    url = "https://api.themoviedb.org/3/discover/tv?include_adult=false&include_null_first_air_dates=false&language="+lang+"&page=1&sort_by=popularity.desc"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }
    response = requests.get(url, headers=headers)
    array_id = get_favourites(username)
    shows = create_tv_shows_response(response.json()['results'], array_id)
    # Serializza l'array di film in JSON
    return jsonify(shows)

def create_tv_shows_response(raw_response, array_id):
    shows = []
    for show in raw_response:
        show_dict = dict()
        show_dict['title'] = show['original_name']
        show_dict['id'] = show['id']
        show_dict['overview'] = show['overview']
        show_dict['genres'] = (show['genre_ids'])
        show_dict['poster'] = get_poster(show['poster_path'])
        show_dict['favourite'] = check_favourite(show['id'], array_id)
        shows.append(show_dict)
    return shows

@app.route("/get_tv_shows_genres", methods = ["GET"])
def get_tv_shows_genres():
    url = "https://api.themoviedb.org/3/genre/tv/list?language=en"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    genres = response.json()['genres']
    genres_strings = []
    for genre in genres:
        genres_strings.append(genre['name'])
    print(genres_strings)
    return genres_strings

app.run(host="0.0.0.0", port="5001")


connection = dbManager.create_db_connection("localhost","root","","mymovies")
#query = "delete from user_favourites"
#dbManager.execute_query(connection, query)
#print(dbManager.read_query(connection, "select username, aes_decrypt(password,'my_key'), name, surname, email, genres from user;"))
print(dbManager.read_query(connection, "select * from user_favourites;"))


        