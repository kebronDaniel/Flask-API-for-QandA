from flask import Flask, config, json, request, jsonify, make_response
from werkzeug.datastructures import WWWAuthenticate
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, abort, reqparse
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import uuid
import jwt
import datetime
from functools import total_ordering, wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'c15953b566a2e3bc15bb8923d623d036'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:aspire@localhost/QandAFinal'

db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)
CORS(app)

class User(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     public_id = db.Column(db.String, unique = True)
     name = db.Column(db.String, nullable = False)
     email = db.Column(db.String, unique = True)
     password = db.Column(db.String)
     admin = db.Column(db.Boolean, default = False)
     questions = db.relationship('Question', backref = 'author', lazy = True, uselist = False)
     answers = db.relationship('Answer', backref = 'author', lazy = True, uselist = False)

     def __repr__(self):
         return self.name


class Question(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     about = db.Column(db.String,nullable=False)
     content = db.Column(db.String,nullable=False)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
     answers = db.relationship('Answer', backref = 'question', lazy = True, uselist = False)
     date_posted = db.Column(db.DateTime, nullable = False, default = datetime.datetime.utcnow)

     def __repr__(self):
         return self.content

class Answer(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     content = db.Column(db.String,nullable=False)
     question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable = False)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
     date_posted = db.Column(db.DateTime, nullable = False, default = datetime.datetime.utcnow)

     def __repr__(self):
         return self.content



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

def token_required(f):
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

class QuestionSchema(ma.Schema):
    class Meta:
        fields = ("id","about","content", "user_id", "date_posted")
        model = Question

class AnswerSchema(ma.Schema):
    class Meta:
        fields = ("id", "content", "question_id","user_id","date_posted")
        model = Answer


user_Schema = UserSchema()
users_Schema = UserSchema(many=True)

question_Schema = QuestionSchema()
questions_schema = QuestionSchema(many=True)

answer_Schema = AnswerSchema()
answers_schema = AnswerSchema(many=True)

@app.route('/', methods = ['GET'])
def home():
    return jsonify({"Hello" : "World"})

# @app.route('/addUser', methods = ['POST'])
# def createUser():
#     data = request.get_json()
#     hashed_password = generate_password_hash(data['password'], method="sha256")
#     newUser = User(public_id=str(uuid.uuid4()), name = data['username'], email = data['email'], password = hashed_password, admin = False)     
#     db.session.add(newUser)
#     db.session.commit()

#     return user_Schema.jsonify(newUser)

class createUser(Resource):
    def post(self):
        hashed_password = generate_password_hash(request.json['password'], method="sha256")
        newUser = User(public_id=str(uuid.uuid4()), name = request.json['username'], email =request.json['email'], password = hashed_password, admin = False) 
        db.session.add(newUser)
        db.session.commit()
        return user_Schema.jsonify(newUser)

api.add_resource(createUser, '/addUser')


# @app.route('/allUsers', methods = ['GET'])
# def getAllUsers():
#     allUsers = User.query.all()
#     result = users_Schema.dump(allUsers)
#     return jsonify(result)

class getAllUsers(Resource):
    def get(self):
        allUsers = User.query.all()
        result = users_Schema.dump(allUsers)
        return jsonify(result)

api.add_resource(getAllUsers, '/allUsers')


# @app.route('/user/<int:uid>', methods = ['GET'])
# def getOneUser(uid):
#     user = User.query.filter_by(id = uid).first()
#     return user_Schema.jsonify(user)

class getOneUser(Resource):
    def get(self,pid):
        user = User.query.filter_by(public_id = pid).first()
        return user_Schema.jsonify(user)

api.add_resource(getOneUser, '/user/<int:pid>')


# @app.route('/deleteUser/<int:uid>', methods = ['DELETE'])
# def deleteUser(uid):
#     user = User.query.filter_by(id = uid).first()
#     db.session.delete(user)
#     db.session.commit()
#     return jsonify({"Message" : "The user has been deleted"})

class deleteUser(Resource):
    def get(self,p_id):
        user = User.query.filter_by(public_id = p_id).first()
        db.session.delete(user)
        db.session.commit()
        return jsonify({"Message" : "The user has been deleted"})

api.add_resource(deleteUser, '/deleteUser/<int:p_id>')


# @app.route('/addQuestion/<int:u_id>', methods= ['POST'])
# def createQuestion(u_id):
#     data = request.get_json()
#     question = Question(content = data['content'], about = data['about'], user_id = u_id)
#     db.session.add(question)
#     db.session.commit()
#     return question_Schema.jsonify(question)

class createQuestion(Resource):
    def post(self,u_id):
        about = request.json['about']
        content = request.json['content'] 
        question = Question(content = content, about = about, user_id = u_id)
        db.session.add(question)
        db.session.commit()
        return user_Schema.jsonify(question)

api.add_resource(createQuestion, '/addQuestion/<int:u_id>')
    

# @app.route('/questions', methods = ['GET'])
# def getAllQuestions():
#     allquestions = Question.query.all()
#     result = questions_schema.dump(allquestions)
#     return jsonify(result)

class getAllQuestions(Resource):
    def get(self):
        allquestions = Question.query.all()
        result = questions_schema.dump(allquestions)
        return jsonify(result)

api.add_resource(getAllQuestions, '/questions')

# @app.route('/question/<int:q_id>', methods = ['GET'])
# def getOneQuestion(q_id):
#     question = Question.query.filter_by(id = q_id).first()
#     return question_Schema.jsonify(question)

class getOneQuestion(Resource):
    def get(self,q_id):
        question = Question.query.filter_by(id = q_id).first()
        return question_Schema.jsonify(question)

api.add_resource(getOneQuestion, '/question/<int:q_id>')


# @app.route('/myQuestions/<int:u_id>', methods = ['GET'])
# def getMyQuestion(u_id):
#     questions = Question.query.filter_by(user_id = u_id).all()
#     result = questions_schema.dump(questions)
#     return jsonify(result)

class getMyQuestion(Resource):
    def get(self,u_id):
        questions = Question.query.filter_by(user_id = u_id).all()
        result = questions_schema.dump(questions)
        return jsonify(result)

api.add_resource(getMyQuestion, '/myQuestions/<int:u_id>')


# @app.route('/answers/<int:q_id>', methods = ['GET'])
# def getAllAnswers(q_id):
#     answers = Answer.query.filter_by(question_id = q_id).all()
#     result = answers_schema.dump(answers)
#     return jsonify(result)

class getAllAnswers(Resource):
    def get(self,q_id):
        answers = Answer.query.filter_by(question_id = q_id).all()
        result = answers_schema.dump(answers)
        return jsonify(result)

api.add_resource(getAllAnswers, '/answers/<int:q_id>')

# @app.route('/answers/<int:q_id>/<int:u_id>', methods = ['GET'])
# def getAllUserAnswers(q_id,u_id):
#     answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).all()
#     if answer:
#         return answer_Schema.jsonify(answer)
    
#     return jsonify("No Answer found")

class getAllUserAnswers(Resource):
    def get(self,q_id,u_id):
        answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).all()
        if answer:
            return answer_Schema.jsonify(answer)
        
        return jsonify("No Answer found")

api.add_resource(getAllUserAnswers, '/answers/<int:q_id>/<int:u_id>')

# @app.route('/checkAnswers/<int:q_id>/<int:u_id>', methods = ['GET'])
# def checkUserAnswers(q_id,u_id):
#     answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).all()
#     if answer:
#         return jsonify("True")
    
#     return jsonify("False")

class checkUserAnswers(Resource):
    def get(self,q_id,u_id):
        answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).all()
        if answer:
            return answers_schema.jsonify(answer)
        
        return jsonify("false")

api.add_resource(checkUserAnswers, '/checkAnswers/<int:q_id>/<int:u_id>')

# class getUserAnswers(Resource):
#     def get(self,q_id,u_id):
#         answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).all()
#         if answer:
#             result =  answers_schema.jsonify(answer)
#             return jsonify({'answer': result})
        
#         return jsonify({'Message': "No Answers found"})

# api.add_resource(getUserAnswers, '/getUserAnswer/<int:q_id>/<int:u_id>')

class getUserAnswers(Resource):
    def get(self,q_id,u_id):
        answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).first()
        return answer_Schema.jsonify(answer)
        

api.add_resource(getUserAnswers, '/getUserAnswer/<int:q_id>/<int:u_id>')

# @app.route('/addAnswer/<int:q_id>/<int:u_id>', methods= ['POST'])
# def createAnswer(q_id,u_id):
#     data = request.get_json()
#     oldAnswer = Answer.query.filter_by(question_id = q_id, user_id = u_id).first()
#     if oldAnswer:
#         db.session.delete(oldAnswer)
#         db.session.commit()
    
#     answer = Answer(content = data['content'], question_id = q_id ,user_id = u_id)
#     db.session.add(answer)
#     db.session.commit()
#     return answer_Schema.jsonify(answer)

class createAnswer(Resource):
    def post(self,q_id,u_id):
        oldAnswer = Answer.query.filter_by(question_id = q_id, user_id = u_id).first()
        if oldAnswer:
            db.session.delete(oldAnswer)
            db.session.commit()
        answer = Answer(content = request.json['content'], question_id = q_id ,user_id = u_id)
        db.session.add(answer)
        db.session.commit()
        return user_Schema.jsonify(answer)

api.add_resource(createAnswer, '/addAnswer/<int:q_id>/<int:u_id>')

# @app.route('/deleteAnswer/<int:q_id>/<int:u_id>', methods= ['DELETE'])
# def deleteAnswer(q_id,u_id):
#     data = request.get_json()
#     answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).first()
#     db.session.delete(answer)
#     db.session.commit() 
#     return jsonify({"Message" : "Successfully deleted the answer."})

class deleteAnswer(Resource):
    def delete(self,q_id,u_id):
        answer = Answer.query.filter_by(question_id = q_id, user_id = u_id).first()
        db.session.delete(answer)
        db.session.commit()
        return jsonify({"Message" : "Successfully deleted the answer."})

api.add_resource(deleteAnswer, '/deleteAnswer/<int:q_id>/<int:u_id>')

# @app.route('/login', methods = ['POST'])
# def login():
#     data = request.get_json()
#     username = data['username']
#     password = data['password']

#     if username:
#         user = User.query.filter_by(name = username).first()
#         if check_password_hash(user.password,data['password']):
#             token = jwt.encode({'public_id' : user.public_id, 'name' : user.name ,'user_id': user.id ,'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
#             return jsonify({'token' : token.decode('UTF-8')})
    
#     return jsonify({"Message" : "Can not login, Use valid credententials"})

class login(Resource):
    def post(self):
        username = request.json['username']
        password = request.json['password']
        if username:
            user = User.query.filter_by(name = username).first()
            if check_password_hash(user.password,password):
                token = jwt.encode({'public_id' : user.public_id, 'name' : user.name ,'user_id': user.id ,'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                return jsonify({'token' : token.decode('UTF-8')})
        
        return jsonify({"Message" : "Can not login, Use valid credententials"})

api.add_resource(login, '/login')


if __name__ == '__main__':
    app.run(debug=True)
