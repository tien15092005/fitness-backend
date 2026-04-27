import jwt
import datetime
import hashlib
from functools import wraps

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from db import db


# =====================
# UTILITIES
# =====================

def hash_password(password):
    """MD5 hash - matching existing DB format"""
    return hashlib.md5(password.encode()).hexdigest()


def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXPIRY_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        request = args[0]
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return Response({"error": "Missing or invalid token"}, status=401)

        token = auth_header.split(" ")[1]

        try:
            payload = decode_token(token)
            request.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=401)

        return f(*args, **kwargs)
    return decorated


def check_db():
    if db is None:
        return Response({"error": "Database connection failed"}, status=503)
    return None


# =====================
# AUTH
# =====================

@api_view(['POST'])
def signup(request):
    user_name = request.data.get("user_name")
    email = request.data.get("email")
    password = request.data.get("password")
    gender = request.data.get("gender", "")

    if not user_name or not email or not password:
        return Response({"error": "Missing user_name, email or password"}, status=400)

    err = check_db()
    if err:
        return err

    try:
        # Check username đã tồn tại chưa
        check_query = """
        FOR u IN Users
            FILTER u.user_name == @user_name OR u.email == @email
            RETURN u
        """
        cursor = db.aql.execute(check_query, bind_vars={
            "user_name": user_name,
            "email": email
        })
        if list(cursor):
            return Response({"error": "Username or email already exists"}, status=409)

        # Tạo user mới
        hashed = hash_password(password)
        insert_query = """
        INSERT {
            user_name: @user_name,
            email: @email,
            hashed_password: @hashed_password,
            gender: @gender
        } INTO Users
        RETURN NEW
        """
        cursor = db.aql.execute(insert_query, bind_vars={
            "user_name": user_name,
            "email": email,
            "hashed_password": hashed,
            "gender": gender
        })
        new_user = list(cursor)[0]
        token = generate_token(new_user["_key"])

        return Response({
            "message": "Signup successful",
            "user_id": new_user["_key"],
            "token": token
        }, status=201)

    except Exception as e:
        error_msg = str(e)

        if "user_name" in error_msg:
            return Response({"error": "Username must be at least 3 characters"}, status=400)
        elif "email" in error_msg:
            return Response({"error": "Invalid email format"}, status=400)
        elif "gender" in error_msg:
            return Response({"error": "Gender must be 'male' or 'female'"}, status=400)
        elif "thiếu trường" in error_msg or "missing" in error_msg.lower():
            return Response({"error": "Please fill in all required fields"}, status=400)
        else:
            return Response({"error": "Signup failed, please try again"}, status=500)


@api_view(['POST'])
def login(request):
    email = request.data.get("email")        # đổi user_name → email
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Missing email or password"}, status=400)

    err = check_db()
    if err:
        return err

    try:
        hashed = hash_password(password)
        query = """
        FOR u IN Users
            FILTER u.email == @email AND u.hashed_password == @hashed_password
            RETURN u
        """
        cursor = db.aql.execute(query, bind_vars={
            "email": email,                  # đổi user_name → email
            "hashed_password": hashed
        })
        result = list(cursor)

        if not result:
            return Response({"error": "Invalid credentials"}, status=401)

        user = result[0]
        token = generate_token(user["_key"])

        return Response({
            "message": "Login successful",
            "token": token,
            "expires_in": f"{settings.JWT_EXPIRY_HOURS} hours",
            "user": {
                "user_id": user["_key"],
                "user_name": user.get("user_name"),
                "email": user.get("email"),
                "gender": user.get("gender"),
                "avatar": user.get("avatar"),
            }
        })

    except Exception as e:
        return Response({"error": f"Login failed: {str(e)}"}, status=500)


# =====================
# EXERCISES
# =====================

@api_view(['GET'])
def get_all_exercises(request):
    err = check_db()
    if err:
        return err

    try:
        query = "FOR e IN Exercises RETURN e"
        cursor = db.aql.execute(query)
        return Response(list(cursor))
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_exercise_detail(request, exercise_id):
    err = check_db()
    if err:
        return err

    try:
        query = """
        FOR e IN Exercises
            FILTER e._key == @id
            RETURN e
        """
        cursor = db.aql.execute(query, bind_vars={"id": exercise_id})
        result = list(cursor)

        if not result:
            return Response({"error": "Exercise not found"}, status=404)

        return Response(result[0])
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def search_exercise(request):
    name = request.GET.get("name")

    if not name:
        return Response({"error": "Missing name parameter"}, status=400)

    err = check_db()
    if err:
        return err

    try:
        query = """
        FOR e IN Exercises
            FILTER CONTAINS(LOWER(e.title), LOWER(@name))
            RETURN e
        """
        cursor = db.aql.execute(query, bind_vars={"name": name})
        return Response(list(cursor))
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# =====================
# USERS
# =====================

@api_view(['GET', 'POST'])
@jwt_required
def user_settings(request, user_id):
    err = check_db()
    if err:
        return err

    if request.method == 'GET':
        try:
            query = """
            FOR u IN Users
                FILTER u._key == @id
                RETURN u.settings
            """
            cursor = db.aql.execute(query, bind_vars={"id": user_id})
            result = list(cursor)

            if not result:
                return Response({"error": "User not found"}, status=404)

            return Response(result[0])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    if request.method == 'POST':
        settings_data = request.data.get("settings")

        if not settings_data:
            return Response({"error": "Missing settings"}, status=400)

        try:
            query = """
            FOR u IN Users
                FILTER u._key == @id
                UPDATE u WITH { settings: @settings } IN Users
                RETURN NEW
            """
            cursor = db.aql.execute(query, bind_vars={
                "id": user_id,
                "settings": settings_data
            })
            result = list(cursor)

            if not result:
                return Response({"error": "User not found"}, status=404)

            return Response(result[0])
        except Exception as e:
            return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@jwt_required
def get_user_history(request, user_id):
    err = check_db()
    if err:
        return err

    try:
        query = """
        FOR v, e IN 1..1 OUTBOUND @user performs
            RETURN v
        """
        cursor = db.aql.execute(query, bind_vars={"user": f"Users/{user_id}"})
        return Response(list(cursor))
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# =====================
# COURSES
# =====================

@api_view(['GET'])
def get_all_courses(request):
    err = check_db()
    if err:
        return err

    try:
        query = "FOR c IN Courses RETURN c"
        cursor = db.aql.execute(query)

        result = []
        for c in cursor:
            result.append({
                "id": c.get("_key"),
                "title": c.get("title"),
                "description": c.get("description"),
                "difficulty": c.get("difficulty"),
                "duration": c.get("duration"),
                "goal": c.get("goal"),
            })

        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_course_detail(request, course_id):
    err = check_db()
    if err:
        return err

    try:
        query = """
        FOR c IN Courses
            FILTER c._key == @id
            RETURN c
        """
        cursor = db.aql.execute(query, bind_vars={"id": course_id})
        result = list(cursor)

        if not result:
            return Response({"error": "Course not found"}, status=404)

        return Response(result[0])
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_courses_by_goal(request):
    goal = request.GET.get("goal")

    if not goal:
        return Response({"error": "Missing goal parameter"}, status=400)

    err = check_db()
    if err:
        return err

    try:
        query = """
        FOR c IN Courses
            FILTER LOWER(c.goal) == LOWER(@goal)
            RETURN c
        """
        cursor = db.aql.execute(query, bind_vars={"goal": goal})
        return Response(list(cursor))
    except Exception as e:
        return Response({"error": str(e)}, status=500)