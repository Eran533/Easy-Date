from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.user_name,
            'email': self.email,
            'password': self.password,
            'phone': self.phone
        }

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    location = db.Column(db.String(50))
    hobbies = db.Column(db.String(50))
    about_me = db.Column(db.String(255))
    gender = db.Column(db.String(15))
    interestedIn = db.Column(db.String(15))
    likes = db.relationship('Like', backref='profile', lazy=True)
    profile_photo = db.Column(db.String(255))
    normal_photos = db.Column(db.String(255))
    likes_me = db.Column(db.String(255), default='')
    dissLike = db.Column(db.String(255), default='')
    maxDistance = db.Column(db.Integer, default=30)
    maxAge = db.Column(db.Integer, default=40)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'age': self.age,
            'location': self.location,
            'hobbies': self.hobbies,
            'about_me': self.about_me,
            "gender": self.gender,
            "interestedIn": self.interestedIn,
            'profile_photo': self.profile_photo,
            'normal_photos': self.normal_photos.split(",") if self.normal_photos else [],
            'likes_me': self.likes_me,
            'Disslike': self.dissLike,
            'maxDistance': self.maxDistance,
            'maxAge': self.maxAge
        }

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'profile_id': self.profile_id,
            'name': self.name
        }

class DissLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(db.String(255))
    users_ids = db.Column(db.String(255))
    user_photo = db.Column(db.String(255))
    user2_photo = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'names': self.names,
            'user_ids': self.users_ids,
            'user_photo': self.user_photo,
            'user2_photo': self.user2_photo
        }

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    profile_id = db.Column(db.Integer)
    message = db.Column(db.String(255))
    profile_name = db.Column(db.String(255))

    def __init__(self, user_id, profile_id, message, profile_name):
        self.user_id = user_id
        self.profile_id = profile_id
        self.message = message
        self.profile_name = profile_name
