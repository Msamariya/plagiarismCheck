from collections import UserString
from itertools import count
from pdb import post_mortem
from xmlrpc.client import ResponseError
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy


app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.plagiarismDb

# creting mongodb collection
users = db["Users"]

def UserExist(username):
    if users.find({ "username": username}).count() == 0:
        return False
    else:
        return True


def varifyPw(username, password):
    hashed_pw = users.find({
        "username": Username
    })[0]["password"]

    if bcrypt.hashpw(password.encode("utf-8"), hashed_pw) == hashed_pw:
        return True
    else:
        return False



def countTokens(username):
    return users.find({
        "username": username
    })[0]["Tokens"]


class Register(Resource):
    def post():
        # get data from the request
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        # check if user already exist
        if UserExist(username):
            retJson = {
                "status": 301,
                "msg": "User {0} already exist.".format(username)
            }
            return jsonify(retJson)

        # Adding data to the database
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.getsalt())

        users.insert_one({
            "username": username,
            "password": hashed_pw,
            "Tokens": 10
        })

        retJson = {
            "status": 200,
            "msg": "User {0} registered successfully".format(username)
        }
        return jsonify(retJson)

class Compare(Resource):
    def post():
        # get data from request
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        # check if user exist
        if not UserExist(username):
            retjson = {
                "status": 301,
                "msg": "User {0} does not exist".format(username)
            }
            return jsonify(retjson)
        
        # varify the password given
        correct_pw = varifyPw(username, password)

        if not correct_pw:
            retJson = {
                "status": 301,
                "msg": "Password is not correct."
            }
            return jsonify(retJson)

        # Check if enough tokens are there
        currentTokens = countTokens(username)
        if not currentTokens > 0:
            retJson = {
                "ststus": 301,
                "msg": "Not enough tokens available."
            }
            return jsonify(retJson)

        # Compare the two texts
        nlp = spacy.load("en_core_web_sm")
        text1 = nlp(text1)
        text2 = nlp(text2)

        ratio = text1.similarity(text2)
        retJson = {
            "status": 200,
            "similarity": ratio,
            "msg": "Similarity score calculated successfully."
        }

        # Remove one Token from the User
        users.update({
            "username": username
        },
        {
            "$set": {
                "tokens": currentTokens - 1 
            }
        })
        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["admin_pw "]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "state": 301,
                "msg": "Invalis Username"
            }
            return jsonify(retJson)
        
        # We are hardcoding it for the sake of simplicity, we should actually save it by encoding like normal password.
        correct_pw = "abc123"

        if password != correct_pw:
            retJson = {
                "state": 301,
                "msg": "Invalid admin password"\
            }
            return jsonify(retJson)
        
        # Update the tokens
        users.update({
            "username": username
        },
        {
            "$set":{
                "Tokens": 10
            }
        })

        retJson = {
            "state": 200,
            "msg": "Tokens Updated successfully"
        }

        return jsonify(retJson)

api.add_resources(Register, "/register")
api.add_resources(Compare, "/detect")
api.add_resources(Refill, "/refill")

if __name__ == "__main__":
    app.run(host="0.0.0.0")


