import uuid
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

# Lưu job tạm trong memory
jobs = {}


# =====================
# ANALYSIS
# =====================

@api_view(['POST'])
def upload_video(request):
    """
    FE gửi video_url đã upload sẵn lên R2
    Body: { "video_url": "...", "exercise": "squat", "type": "video", "user_id": 5 }
    """
    video_url = request.data.get("video_url")
    exercise = request.data.get("exercise")
    video_type = request.data.get("type")
    user_id = request.data.get("user_id")

    if not video_url or not exercise or not user_id:
        return Response({"error": "Missing video_url, exercise or user_id"}, status=400)

    try:
        job_id = str(uuid.uuid4())

        jobs[job_id] = {
            "status": "processing",
            "result_url": None,
            "exercise": exercise,
            "type": video_type,
            "user_id": user_id,
            "video_url": video_url,
        }

        # Gọi AI service
        try:
            requests.post(
                f"{settings.AI_SERVICE_URL}/analyze/",
                json={
                    "job_id": job_id,
                    "video_url": video_url,
                    "exercise": exercise,
                    "type": video_type,
                    "user_id": user_id,
                    "callback_url": f"{settings.DJANGO_BASE_URL}/api/analysis/{job_id}/result/",
                },
                timeout=5
            )
        except Exception:
            pass

        return Response({
            "job_id": job_id,
            "status": "processing",
            "message": "Analysis in progress"
        }, status=202)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def check_status(request, job_id):
    """
    FE query kết quả theo job_id
    """
    job = jobs.get(job_id)

    if not job:
        return Response({"error": "Job not found"}, status=404)

    return Response({
        "job_id": job_id,
        "status": job["status"],
        "result_url": job["result_url"],
    })


@api_view(['POST'])
def receive_result(request, job_id):
    """
    AI callback gửi result_url về Django
    Body: { "result_url": "https://..." }
    """
    job = jobs.get(job_id)

    if not job:
        return Response({"error": "Job not found"}, status=404)

    result_url = request.data.get("result_url")

    if not result_url:
        return Response({"error": "Missing result_url"}, status=400)

    jobs[job_id]["status"] = "done"
    jobs[job_id]["result_url"] = result_url

    return Response({"message": "Result received"})