import math
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from twilio.base.exceptions import TwilioRestException

from data_models import db
from twilio.rest import Client
from datamanager.SQLiteDataManager import SQLiteDataManager
from flask_socketio import SocketIO, emit
import requests

app = Flask(__name__)
db_path = os.path.join(os.path.dirname(__file__), "datamanager", "EasyDateApp.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
data_manager = SQLiteDataManager(app)
socketio = SocketIO(app, async_mode='eventlet')

def get_lat_lon_location(city):
    url = "https://forward-reverse-geocoding.p.rapidapi.com/v1/forward"

    querystring = {"city": f"{city}"}

    headers = {
        "X-RapidAPI-Key": "234f5498c9msh8226e93fd4984d6p11b844jsn286c0f051d2e",
        "X-RapidAPI-Host": "forward-reverse-geocoding.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()[0]['lon'], response.json()[0]['lat']

def haversine(lat1, lon1, lat2, lon2):
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))
    earth_radius = 6371.0
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c
    return distance

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html")

@app.route('/log_in', methods=['GET', 'POST'])
def log_in():
    return render_template("log_in.html")

@app.route('/process_login', methods=['GET', 'POST'])
def process_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = data_manager.get_all_users()
        for user in users:
            if username == user['username'] and password == user['password']:
                id = user['id']
                user_profile = data_manager.get_profile(id)
                interestedIn = user_profile["interestedIn"]
                return redirect(url_for("app_page", id=id, interestedIn=interestedIn))
        error_message = "Incorrect username or password. Please try again."
        return render_template('log_in.html', error_message=error_message)
    return render_template('log_in.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        users = data_manager.get_all_users()
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            confirm_password = request.form.get('confirm_password')
            phone_number = request.form.get('phone_number')
            if password != confirm_password:
                return render_template("register.html", error_message="Passwords do not match")
            if any(account["username"].lower() == username.lower() or account["email"].lower() == email.lower() for
                   account in users):
                return render_template("register.html", error_message="Username/Email already exists")
            new_id = 1 if not users else max(account['id'] for account in users) + 1
            new_account = {
                "username": username,
                "email": email,
                "password": password,
                "phone": phone_number
            }
            data_manager.add_user(new_account)
            return redirect(url_for('verify', phone_number=phone_number, id=new_id))
        return render_template("register.html")
    except Exception as e:
        error_message = str(e)
        return render_template("register.html", error_message=error_message)

@app.route('/verify/<phone_number>/<id>', methods=['GET', 'POST'])
def verify(phone_number, id):
    if request.method == 'GET':
        try:
            account_sid = "AC81da557652ce9fdffc259a77d20e4af7"
            auth_token = "cf985887a5a61d81ffb1d86a4ba88b8b"
            verify_sid = "VA183b1a8c08603c924b6415880fdad754"
            verified_number = f"+972{str(phone_number)[1:]}"
            client = Client(account_sid, auth_token)

            verification = client.verify.v2.services(verify_sid) \
                .verifications \
                .create(to=verified_number, channel="sms")

            return render_template("verify.html", phone_number=phone_number, id=id)
        except TwilioRestException as e:
            print(f"Twilio error: {e}")

    elif request.method == 'POST':
        otp_code = request.form.get('verification_code')
        account_sid = "AC81da557652ce9fdffc259a77d20e4af7"
        auth_token = "cf985887a5a61d81ffb1d86a4ba88b8b"
        verify_sid = "VA183b1a8c08603c924b6415880fdad754"
        verified_number = f"+972{str(phone_number)[1:]}"
        client = Client(account_sid, auth_token)

        verification_check = client.verify.v2.services(verify_sid) \
            .verification_checks \
            .create(to=verified_number, code=otp_code)

        if verification_check.status == 'approved':
            return redirect(url_for('create_profile', id=id))
        else:
            return render_template("verify.html", phone_number=phone_number, id=id)

    return render_template("verify.html", phone_number=phone_number, id=id)

@app.route('/create_profile/<id>', methods=['GET', 'POST'])
def create_profile(id):
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            age = request.form.get('age')
            location = request.form.get('location')
            hobbies = request.form.get('hobbies')
            about = request.form.get('about')
            gender = request.form['gender']
            interestedIn = request.form['interestedIn']
            profile_photo = request.files['profile_photo']
            profile_filename = f'{name}.png'
            normal_photos = request.files.getlist('normal_photos[]')
            if profile_photo:
                try:
                    profile_photo.save(f'static/profiles/{profile_filename}')
                except:
                    return render_template("create_profile.html", error_message="Failed to save the image file")
            n_photos = []
            if normal_photos:
                i = 0
                for normal_photo in normal_photos:
                    if normal_photo:
                        try:
                            filename = f'{name + str(i)}.png'
                            n_photos.append(filename)
                            normal_photo.save(f'static/users_photos/{filename}')
                            i += 1
                        except:
                            return render_template("create_profile.html", error_message="Failed to save the image file")
            profile_data = {
                "user_id": id,
                "name": name,
                "age": age,
                "location": location,
                "hobbies": hobbies,
                "about_me": about,
                "gender": gender,
                "interestedIn": interestedIn,
                "profile_photo": profile_filename if profile_photo else "",
                "normal_photos": ",".join([normal_photo for normal_photo in n_photos if normal_photo])
            }
            data_manager.add_profile(profile_data)
            return redirect(url_for('app_page', id=id, interestedIn=interestedIn))
        return render_template("create_profile.html", id=id)
    except Exception as e:
        error_message = str(e)
        print(error_message)
    return render_template("create_profile.html", id=id, error_message=error_message)

@app.route('/app_page/<id>/<interestedIn>', methods=['GET'])
def app_page(id, interestedIn):
    profiles = data_manager.get_gender_profiles(interestedIn, id)
    user_profile = data_manager.get_profile(id)
    matches = data_manager.get_all_matches(id)
    profiles_after_distance = []
    user_profile_distance = user_profile['maxDistance']
    maxDistance = request.args.get('maxDistance', type=float, default=user_profile_distance)
    user_profile_MaxAge = user_profile['maxAge']
    maxAge = request.args.get('maxAge', type=float, default=user_profile_MaxAge)
    data_manager.update_profile_distance(id, maxDistance)
    data_manager.update_profile_maxAge(id, maxAge)
    if profiles:
        for profile in profiles:
            location_profile = profile['location']
            location_user = user_profile['location']
            location_profile = get_lat_lon_location(location_profile)
            location_user = get_lat_lon_location(location_user)
            if haversine(location_user[0], location_user[1], location_profile[0], location_profile[1]) <= maxDistance and profile['age'] <= maxAge:
                profiles_after_distance.append(profile)
        if profiles_after_distance:
            profile = profiles_after_distance[-1]
            return render_template("app_page.html", profile=profile, id=id,
                                   interestedIn=interestedIn, maxDistance=maxDistance, len_matches=len(matches), maxAge=maxAge)
    return render_template("no_profiles.html", id=id, interestedIn=interestedIn, maxDistance=maxDistance, maxAge=maxAge, len_matches=len(matches), profile=user_profile)

@app.route('/profile_details/<user_id>/<profile_id>', methods=['GET'])
def profile_details(user_id, profile_id):
    user_profile = data_manager.get_profile(user_id)
    profile = data_manager.get_profile(profile_id)
    if profile:
        return render_template("profile_details.html", profile=profile, user_profile=user_profile)
    else:
        return render_template("profile_not_found.html")

@app.route('/app_page/<user_id>/like/<profile_id>', methods=['POST'])
def like(user_id, profile_id):
    profile = data_manager.get_profile(profile_id)
    user_profile = data_manager.get_profile(user_id)
    like_data = {
        "user_id": user_id,
        "name": profile["name"],
        "profileId": profile_id
    }
    profileObj = data_manager.get_profileObj(profile_id)
    data_manager.add_like(like_data)
    if profileObj.likes_me:
        profileObj.likes_me += f",{user_id}"
    else:
        profileObj.likes_me = user_id
    db.session.commit()
    mutual_match = data_manager.get_all_likes(user_id)
    for m in mutual_match:
        if int(profile_id) == int(m["user_id"]):
            match_data = {
                "name": f"{user_profile['name']}❤️{profile['name']}",
                "user_ids": f"{user_profile['user_id']},{profile['user_id']}",
                "user_img": f"{user_profile['profile_photo']}",
                "user_img2": f"{profile['profile_photo']}"
            }
            data_manager.add_match(match_data)
            interestedIn = user_profile["interestedIn"]
            return render_template("match.html", user_id=user_id, profile_id=profile_id, profile=profile, user_profile=user_profile)
    user_profile = data_manager.get_profile(user_id)
    interestedIn = user_profile["interestedIn"]
    return redirect(url_for("app_page", id=user_id, interestedIn=interestedIn))

@app.route('/app_page/<user_id>/DissLike/<profile_id>', methods=['POST'])
def Disslike(user_id, profile_id):
    profile = data_manager.get_profile(profile_id)
    user_profile = data_manager.get_profile(user_id)
    Disslike_data = {
        "user_id": user_id,
        "name": profile["name"],
        "profileId": profile_id
    }
    profileObj = data_manager.get_profileObj(profile_id)
    data_manager.add_Disslike(Disslike_data)
    if profileObj.dissLike:
        profileObj.dissLike += f",{user_id}"
    else:
        profileObj.dissLike = user_id
    db.session.commit()
    interestedIn = user_profile["interestedIn"]
    return redirect(url_for("app_page", id=user_id, interestedIn=interestedIn))

@app.route('/matches/<user_id>', methods=['GET'])
def matches(user_id):
    user_profile = data_manager.get_profile(user_id)
    matches = data_manager.get_all_matches(user_id)
    return render_template("matches.html", matches=matches, user_id=user_id, user_profile=user_profile)

@app.route('/delete_match/<user_id>/<profile_id>', methods=['POST'])
def delete_match(user_id, profile_id):
    profile = data_manager.get_profile(profile_id)
    user_profile = data_manager.get_profile(user_id)
    data_manager.delete_match(profile["id"], user_profile["id"])
    matches = data_manager.get_all_matches(user_id)
    return redirect(url_for('matches', matches=matches, user_id=user_id))

@app.route('/view_match/<user_id>/<profile_id>', methods=['GET'])
def view_match(user_id, profile_id):
    profile = data_manager.get_profile(profile_id)
    user_profile = data_manager.get_profile(user_id)
    return render_template("match.html", user_id=user_id, profile_id=profile_id, profile=profile, user_profile=user_profile)

@app.route('/chat/<user_id>/<profile_id>', methods=['GET'])
def chat(user_id, profile_id):
    chat_history = data_manager.get_chat_messages(user_id, profile_id)
    user_profile = data_manager.get_profile(user_id)
    return render_template("chat.html", user_id=user_id, profile_id=profile_id, chat_history=chat_history, user_profile=user_profile)

@app.route('/get_chat_history/<user_id>/<profile_id>')
def get_chat_history(user_id, profile_id):
    chat_history = data_manager.get_chat_messages(user_id, profile_id)
    return jsonify(chat_history)

@socketio.on('send_message')
def handle_message(data):
    user_id = data['user_id']
    profile_id = data['profile_id']
    message = data['message']
    profile = data_manager.get_profile(user_id)
    profile_name = profile['name']
    data_manager.save_message(user_id, profile_id, message, profile_name)
    emit('receive_message',
         {'user_id': user_id, 'profile_id': profile_id, 'message': message, 'profile_name': profile_name},
         broadcast=True)

@app.route('/<int:profile_id>/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(profile_id, user_id):
    user = data_manager.get_profile(user_id)
    interestedIn = user["interestedIn"]
    try:
        if request.method == "POST":
            name = request.form.get('name')
            age = request.form.get('age')
            location = request.form.get('location')
            hobbies = request.form.get('hobbies')
            about = request.form.get('about')
            profile_data = {
                "name": name,
                "age": age,
                "location": location,
                "hobbies": hobbies,
                "about_me": about,
            }
            data_manager.edit_profile(profile_id, profile_data)
            return redirect(url_for("app_page", id=user_id, interestedIn=interestedIn))
        return render_template('edit_profile.html', user=user)
    except Exception as e:
        error_message = str(e)
        return render_template('error.html', error_message=error_message), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, port=5001)
