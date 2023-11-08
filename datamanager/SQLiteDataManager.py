from operator import or_

from sqlalchemy.exc import SQLAlchemyError

from data_models import User, db, Profile, Like, Match, ChatMessage, DissLike
from datamanager.dataManager_Interface import DataManagerInterface

class SQLiteDataManager(DataManagerInterface):
    def __init__(self, app):
        self.app = app
        with self.app.app_context():
            db.init_app(self.app)

    def add_user(self, user):
        new_user = User(user_name = user["username"], password = user["password"], email= user["email"], phone=user["phone"])
        db.session.add(new_user)
        db.session.commit()

    def add_like(self, like):
        new_like = Like(user_id = like["user_id"], name = like["name"], profile_id= like["profileId"])
        db.session.add(new_like)
        db.session.commit()

    def add_Disslike(self, Disslike):
        new_like = DissLike(user_id = Disslike["user_id"], name = Disslike["name"], profile_id= Disslike["profileId"])
        db.session.add(new_like)
        db.session.commit()

    def add_match(self, like):
        new_match = Match(names=like["name"], users_ids=like["user_ids"], user_photo=like["user_img"], user2_photo=like["user_img2"])
        db.session.add(new_match)
        db.session.commit()

    def delete_match(self, profile_id, user_profile_id):
        try:
            match_to_delete = Match.query.filter(
                (Match.users_ids.like(f"%{profile_id},{user_profile_id}%")) |
                (Match.users_ids.like(f"%{user_profile_id},{profile_id}%"))
            ).first()
            if match_to_delete:
                db.session.delete(match_to_delete)
                db.session.commit()
            else:
                print("Match not found.")
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def get_all_likes(self, user_id):
        likes = Like.query.filter_by(profile_id=user_id).all()
        return [like.to_dict() for like in likes]

    def get_all_matches(self, user_id):
        matching_matches = Match.query.filter(Match.users_ids.like(f"%{user_id}%")).all()
        return [match.to_dict() for match in matching_matches]

    def get_all_users(self):
        all_users = User.query.all()
        return [user.to_dict() for user in all_users]

    def add_profile(self, profile):
        new_profile = Profile(
            user_id=profile["user_id"],
            name=profile["name"],
            age=profile["age"],
            location=profile["location"],
            hobbies=profile["hobbies"],
            about_me=profile["about_me"],
            gender=profile["gender"],
            interestedIn=profile["interestedIn"],
            profile_photo=profile["profile_photo"],
            normal_photos=profile["normal_photos"],
        )
        db.session.add(new_profile)
        db.session.commit()

    def get_all_profiles(self):
        all_profiles = Profile.query.all()
        return [p.to_dict() for p in all_profiles]

    def get_profile(self, profile_id):
        profile = Profile.query.get(profile_id)
        return profile.to_dict()

    def update_profile_distance(self, profile_id, distance):
        profile = Profile.query.get(profile_id)
        profile.maxDistance = distance
        db.session.commit()

    def update_profile_maxAge(self, profile_id, maxAge):
        profile = Profile.query.get(profile_id)
        profile.maxAge = maxAge
        db.session.commit()

    def get_profileObj(self, profile_id):
        profile = Profile.query.get(profile_id)
        return profile

    def get_gender_profiles(self, gender, user_id):
        liked_profile_ids = [like.profile_id for like in Like.query.filter_by(user_id=user_id).all()]
        disliked_profile_ids = [dislike.profile_id for dislike in DissLike.query.filter_by(user_id=user_id).all()]
        gender_profiles = Profile.query.filter_by(gender=gender) \
            .filter(Profile.id.notin_(liked_profile_ids)) \
            .filter(Profile.id.notin_(disliked_profile_ids)) \
            .all()
        return [p.to_dict() for p in gender_profiles]

    def save_message(self, user_id, profile_id, message, profile_name):
        chat_message = ChatMessage(user_id=user_id, profile_id=profile_id, message=message, profile_name=profile_name)
        db.session.add(chat_message)
        db.session.commit()

    def get_chat_messages(self, user_id, profile_id):
        chat_messages = ChatMessage.query.filter(
            or_(
                (ChatMessage.user_id == user_id) & (ChatMessage.profile_id == profile_id),
                (ChatMessage.user_id == profile_id) & (ChatMessage.profile_id == user_id)
            )
        ).all()
        messages = [{'user_id': message.user_id, 'profile_id': message.profile_id, 'message': message.message,
                     'profile_name': message.profile_name} for
                    message in chat_messages]
        return messages

    def edit_profile(self, profile_id, user_data):
        existing_user = Profile.query.get(profile_id)
        if existing_user:
            existing_user.name = user_data["name"]
            existing_user.age = user_data["age"]
            existing_user.location = user_data["location"]
            existing_user.hobbies = user_data["hobbies"]
            existing_user.about_me = user_data["about_me"]
            db.session.commit()
        else:
            raise ValueError("not found.")
