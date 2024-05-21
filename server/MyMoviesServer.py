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
        print(dbManager.read_query(connection, "select * from user"))
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
    page = request.args.get("page")

    array_id = get_favourites(username)
    favourites_left = len(array_id)
    favourite_request = bool(request.args.get("favouriteRequest"))
    movies = []
    for i in range(1,int(page)+1):
        url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language="+lang+"&page="+str(i)+"&sort_by=popularity.desc"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
        }
        response = requests.get(url, headers=headers)
       
        movies, favourites_left = create_movie_response(movies,response.json()['results'], array_id, favourite_request, favourites_left)

    while favourites_left != 0 and favourite_request:
        i += 1
        url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language="+lang+"&page="+str(i)+"&sort_by=popularity.desc"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
        }
        response = requests.get(url, headers=headers)
        array_id = get_favourites(username)
        movies, favourites_left = create_movie_response(movies,response.json()['results'], array_id, favourite_request, favourites_left)
    
    more = int(page) <= response.json()['total_pages']
    response = {
        "items" : movies,
        "more" : more
        }
    return jsonify(response)

def create_movie_response(movies,raw_response, array_id, favourite_request, favourites_left):
    for movie in raw_response:
        movie_dict = dict()
        movie_dict['title'] = movie['title']
        movie_dict['id'] = movie['id']
        movie_dict['overview'] = movie['overview']
        movie_dict['genres'] = (movie['genre_ids'])
        movie_dict['releaseDate'] = convert_date(movie['release_date'])
        movie_dict['poster'] = get_poster(movie['poster_path'])
        movie_dict['type'] = "movie"
        movie_dict['favourite'] = check_favourite(movie['id'], array_id)
        if check_favourite(movie['id'], array_id) and favourite_request:
            favourites_left -= 1
        movies.append(movie_dict)
    return movies, favourites_left

@app.route("/get_genres", methods = ["GET"])
def get_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list?language=en"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    genres = response.json()['genres']
    genres_id = []
    for genre in genres:
        genres_id.append(genre['id'])
   
    #get tv shows genres
    url = "https://api.themoviedb.org/3/genre/tv/list?language=en"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    genres = response.json()['genres']
  
    for genre in genres:
        if genre['id'] not in genres_id:
            genres_id.append(genre['id'])

    return genres_id


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

def get_favourites(username, movies = True):
    connection = dbManager.create_db_connection("localhost","root","","mymovies")
    if movies:
        query = "select movie_id from user_favourites where user='"+username+"'"
    else:
        query = "select tvshow_id from user_favourite_tvshows where user='"+username+"'"
    res = dbManager.read_query(connection, query) #[(693134],), (934632,), (940721,)]
    array_id = [tupla[0] for tupla in res] 
    if movies:
        print("fav movies", array_id)
    else:
        print("fav tv shows", array_id)
    return array_id

def check_favourite(movie_id, array_id):
    if movie_id in array_id:
        return True
    else:
        return False


@app.post("/update_favourite_movies")
def update_favourite_movies():
    try:
        print(request.get_json())
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
            print(dbManager.read_query(connection, "select * from user_favourites"))
            return jsonify(True), 200
        #se la trovo vuol dire che lo user ha rimosso quel film dai preferiti quando arrivo a questo punto
        else:
            query = "delete from user_favourites where user = '"+username+"' and movie_id = '"+movie_id+"'"
            dbManager.execute_query(connection, query)
            print(dbManager.read_query(connection, "select * from user_favourites"))
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
    page = request.args.get("page")
    
    array_id = get_favourites(username, False)
    favourites_left = len(array_id)
    favourite_request = bool(request.args.get("favouriteRequest"))
    print("array id", array_id)
    shows = []
    for i in range(1,int(page)+1):
        url = "https://api.themoviedb.org/3/discover/tv?include_adult=false&include_null_first_air_dates=false&language="+lang+"&page="+str(i)+"&sort_by=popularity.desc"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
        }
        response = requests.get(url, headers=headers)
        shows, favourites_left = create_tv_shows_response(shows,response.json()['results'], array_id, favourite_request, favourites_left)
        # Serializza l'array di film in JSON
    
    while favourites_left != 0 and favourite_request:
        i += 1
        url = "https://api.themoviedb.org/3/discover/tv?include_adult=false&include_null_first_air_dates=false&language="+lang+"&page="+str(i)+"&sort_by=popularity.desc"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
        }
        response = requests.get(url, headers=headers)
        shows, favourites_left = create_tv_shows_response(shows,response.json()['results'], array_id, favourite_request, favourites_left)
        print("left:", array_id)
    more = int(page) <= response.json()['total_pages']
    response = {
        "items" : shows,
        "more" : more
        }
    return jsonify(response)

def create_tv_shows_response(shows, raw_response, array_id, favourite_request, favourites_left):
    for show in raw_response:
        show_dict = dict()
        show_dict['title'] = show['original_name']
        show_dict['id'] = show['id']
        show_dict['overview'] = show['overview']
        show_dict['genres'] = (show['genre_ids'])
        if show['poster_path'] != None:
            show_dict['poster'] = get_poster(show['poster_path'])
        show_dict['type'] = "tvShow"
        show_dict['favourite'] = check_favourite(show['id'], array_id)
        if check_favourite(show['id'], array_id) and favourite_request:
            print("arrey favourites:", array_id, "\nremoved: ",  show['id'] )
            favourites_left -= 1
        shows.append(show_dict)
    return shows, favourites_left

@app.post("/update_favourite_tvshows")
def update_favourite_tvshows():
    try:
        username = request.get_json()['username']
        tvshow_id = str(request.get_json()['id'])
        print("-------- UPDATE FAVOURITES ---------")
        query = "select * from user_favourite_tvshows where user = '"+username+"' and tvshow_id = '"+tvshow_id+"'"
        connection = dbManager.create_db_connection("localhost","root","","mymovies")
        res = dbManager.read_query(connection, query)
        #se non trovo righe con username,movie_id inserisco il movie_id preferito per username
        if len(res) == 0:
            query = "insert into user_favourite_tvshows values('"+username+"','"+tvshow_id+"');"
            dbManager.execute_query(connection, query)
            query = "select * from user_favourite_tvshows"
            print(dbManager.read_query(connection, query))
            return jsonify(True), 200
        #se la trovo vuol dire che lo user ha rimosso quel film dai preferiti quando arrivo a questo punto
        else:
            query = "delete from user_favourite_tvshows where user = '"+username+"' and tvshow_id = '"+tvshow_id+"'"
            dbManager.execute_query(connection, query)
            query = "select * from user_favourite_tvshows"
            print(dbManager.read_query(connection, query))
            return jsonify(False), 200
    
    except Error as err:
        print("error in updating user favourite movies: ", err)
        return jsonify(False), 500
        
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

# -------------------------------------- REVIEWS --------------------------------------------------
@app.route("/get_reviews", methods = ["GET"])
def get_reviews():
    print("------- GET REVIEWS ---------")
    username = request.args.get("username")
    lang = request.args.get("lang")
    page = request.args.get("page")
    type = request.args.get("type")
    id = request.args.get("id")
    reviews_dicts = []
    if type == "tvShow":
        type = "tv"
    for i in reversed(range(1,int(page)+1)):
        url = "https://api.themoviedb.org/3/"+type+"/"+id+"/reviews?language="+lang+"&page="+str(i)
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
        }

        response = requests.get(url, headers=headers)
        reviews_dicts = create_reviews_response(response.json()['results'], headers, reviews_dicts)

    url = "https://api.themoviedb.org/3/"+type+"/"+id+"/reviews?language="+lang+"&page="+str(i+1)
    
    if requests.get(url, headers=headers).json()['results'] == []:
        response = {
            "reviews": reviews_dicts,
            "more": False
        }
    else:
        response = {
            "reviews": reviews_dicts,
            "more": True
        }
    return jsonify(response)

def create_reviews_response(reviews, headers, reviews_dicts):
    for review in reversed(reviews):
        url = "https://api.themoviedb.org/3/review/"+review['id']
        response = requests.get(url, headers=headers).json()
        review_dict = {}
        review_dict['author'] = response['author']
        review_dict['date'] = get_date(response['created_at'])
        review_dict['review'] = response['content']
        reviews_dicts.append(review_dict)
    return reviews_dicts

def get_date(date):
    if "T" in date:
        date = date.split("T")[0].split("-")
        date = date[2]+"-"+date[1]+"-"+date[0]
    return date

#---------------------------------------- CAST ------------------------------------------------
@app.route('/get_cast', methods = ['GET'])
def get_cast():
    print("------- GET CAST ---------")
    lang = request.args.get("lang")
    type = request.args.get("type")
    id = request.args.get("id")
    if type == "tvShow":
        type = "tv"
    url = "https://api.themoviedb.org/3/"+type+"/"+id+"/credits?language="+lang
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }

    response = requests.get(url, headers=headers)
    cast_dict = create_cast_response(response.json()['cast'], headers, lang)
    return jsonify(cast_dict)

def create_cast_response(raw_data, headers, lang):
    cast = []
    for acthor in raw_data:
        dict = {}
        url = "https://api.themoviedb.org/3/person/"+str(acthor['id'])+"?language="+lang
        response = requests.get(url, headers=headers).json()
        dict['id'] = acthor['id']
        dict['name'] = acthor['name']
        dict['character'] = acthor['character']
        if response['profile_path'] != None:
            dict['image'] = get_poster(response['profile_path'])
        dict['biography'] = response['biography']
        if response['birthday'] != None:
            dict['birthday'] = convert_date(response['birthday'])
        dict['placeOfBirth'] = response['place_of_birth']
        dict['gender'] = response['gender']

        cast.append(dict)
    return cast

@app.route("/get_credits", methods = ["GET"])
def get_credits():
    lang = request.args.get("lang")
    id = request.args.get("id")
    url = "https://api.themoviedb.org/3/person/"+str(id)+"/combined_credits?language="+lang
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZmJlNDlmZTQyZDE2MjRiOTliYWZkMzZhNTJmZjEwZiIsInN1YiI6IjY2MzBjNDM4NWIyZjQ3MDEyODAzYjhmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bhhXiBgwizqz5K98QXxE984zx9fh6Am_aNKObE3wi4k"
    }
    credits = requests.get(url, headers=headers).json()
    credits_array = []
    for credit in credits['cast']:
        credit_dict = {}
        credit_dict['id'] = credit['id']
        credit_dict['type'] = credit['media_type']
        if 'original_title' in credit:
            credit_dict['title'] = credit['original_title']
        credit_dict['character'] = credit['character']
        if credit['poster_path'] != None:
            credit_dict['poster'] = get_poster(credit['poster_path'])
        credits_array.append(credit_dict)

    return jsonify(credits_array)


app.run(host="0.0.0.0", port="5001")


connection = dbManager.create_db_connection("localhost","root","","mymovies")
#query = "delete from user_favourites"
#dbManager.execute_query(connection, query)
#print(dbManager.read_query(connection, "select username, aes_decrypt(password,'my_key'), name, surname, email, genres from user;"))
print(dbManager.read_query(connection, "select * from user_favourites;"))


        