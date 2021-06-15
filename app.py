from flask import Flask, config, json, request, jsonify, make_response
from werkzeug.datastructures import WWWAuthenticate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import total_ordering, wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'c15953b566a2e3bc15bb8923d623d036'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:aspire@localhost/QandA'

db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     public_id = db.Column(db.String, unique = True)
     name = db.Column(db.String, nullable = False)
     email = db.Column(db.String, unique = True)
     password = db.Column(db.String)
     admin = db.Column(db.Boolean, default = False)
     posts = db.relationship('Posts', backref = 'author', lazy = True, uselist = False)

class Posts(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     title = db.Column(db.String, nullable = False)
     content = db.Column(db.String,nullable=False)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

def token_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):

        token = None

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'Valid token is missing'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'token is invalid'})

        return f(current_user, *args, **kwargs)
   return decorator

def token_Required(f):
   @wraps(f)
   def decorator(*args, **kwargs):

        token = None

        auth = request.headers.get('Authorization', None)
        if not auth:
            return jsonify({"Message" : "Valid token is missing"})

        parts = auth.split()
        token = parts[1]

        if not token:
            return jsonify({'message': 'Valid token is missing'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'token is invalid'})

        return f(current_user, *args, **kwargs)
   return decorator

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "public_id" ,"name", "email", "password", "admin")
        model = User

class PostsSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "content", "user_id")
        model = Posts


user_Schema = UserSchema()
users_Schema = UserSchema(many=True)
post_Schema = PostsSchema()
posts_schema = PostsSchema(many=True)

@app.route('/', methods = ['GET'])
def home():
    return jsonify({"Hello" : "World"})

@app.route('/addUser', methods = ['POST'])
def createUser():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method="sha256")
    newUser = User(public_id=str(uuid.uuid4()), name = data['name'], email = data['email'], password = hashed_password, admin = False)     
    db.session.add(newUser)
    db.session.commit()

    return user_Schema.jsonify(newUser)


@app.route('/allUsers', methods = ['GET'])
def getAllUsers():
    allUsers = User.query.all()
    result = users_Schema.dump(allUsers)
    return jsonify(result)

@app.route('/posts', methods = ['GET'])
def getAllPosts():
    allPosts = Posts.query.all()
    result = posts_schema.dump(allPosts)
    return jsonify(result)

@app.route('/user/<int:uid>', methods = ['GET'])
def getOneUser(uid):
    user = User.query.filter_by(id = uid).first()
    return user_Schema.jsonify(user)

@app.route('/promoteUser/<int:uid>', methods = ['PUT'])
def promoteUser(uid):
    user = User.query.filter_by(id = uid).first()
    user.admin = True
    db.session.commit()
    return user_Schema.jsonify(user)

@app.route('/deleteUser/<int:uid>', methods = ['DELETE'])
def deleteUser(uid):
    user = User.query.filter_by(id = uid).first()
    db.session.delete(user)
    db.session.commit()
    return jsonify({"Message" : "The user has been deleted"})

@app.route('/createPost', methods= ['POST'])
@token_required
def createPost(current_user):
    if current_user:
        data = request.json()
        post = Posts(title = data['title'], content = data['content'], user_id = current_user.id)
        db.session.add(post)
        db.session.commit()
        return post_Schema.jsonify(post)
    
    return jsonify({"Message" : "No user with valid token is found!"})


@app.route('/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not Verify', 401, {"WWWAuthenticate" : 'Basic realm="Login required"'})
    
    user = User.query.filter_by(name = auth.username).first()

    if not user:
        return make_response('Could not Verify', 401, {"WWWAuthenticate" : 'Basic realm="Login required"'})
    
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({'token' : token.decode('UTF-8')})
    
    return make_response('Could not Verify', 401, {"WWWAuthenticate" : 'Basic realm="Login required"'})



if __name__ == '__main__':
    app.run(debug=True)

# To do
    # 1, put a error message if the query is not found : return jsonify({"Message" : "Any message"})
