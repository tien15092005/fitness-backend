from rest_framework.decorators import api_view
from rest_framework.response import Response
from db import db




@api_view(['GET'])
def get_all_exercises(request):
    query = "FOR e IN Exercises RETURN e"
    cursor = db.aql.execute(query)
    return Response(list(cursor))


@api_view(['GET'])
def get_exercise_detail(request, exercise_id):
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


@api_view(['GET'])
def search_exercise(request):
    name = request.GET.get("name")

    if not name:
        return Response({"error": "Missing name parameter"}, status=400)

    query = """
    FOR e IN Exercises
        FILTER CONTAINS(LOWER(e.Title), LOWER(@name))
        RETURN e
    """

    cursor = db.aql.execute(query, bind_vars={"name": name})
    return Response(list(cursor))




@api_view(['GET', 'POST'])
def user_settings(request, user_id):

    # ===== GET SETTINGS =====
    if request.method == 'GET':
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


    # ===== UPDATE SETTINGS =====
    if request.method == 'POST':
        settings = request.data.get("settings")

        if not settings:
            return Response({"error": "Missing settings"}, status=400)

        query = """
        FOR u IN Users
            FILTER u._key == @id
            UPDATE u WITH { settings: @settings } IN Users
            RETURN NEW
        """

        cursor = db.aql.execute(
            query,
            bind_vars={
                "id": user_id,
                "settings": settings
            }
        )

        result = list(cursor)

        if not result:
            return Response({"error": "User not found"}, status=404)

        return Response(result[0])


@api_view(['GET'])
def get_user_history(request, user_id):

    query = """
    FOR v, e IN 1..1 OUTBOUND @user performs
        RETURN v
    """

    cursor = db.aql.execute(
        query,
        bind_vars={
            "user": f"Users/{user_id}"
        }
    )

    return Response(list(cursor))

