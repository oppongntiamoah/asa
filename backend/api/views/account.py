from accounts.forms import ProfileForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == "GET":
        u = request.user
        return Response({
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "phone_number": u.phone_number,
        })

    form = ProfileForm(request.data, instance=request.user)
    if not form.is_valid():
        return Response({"errors": form.errors}, status=400)
    form.save()
    u = request.user
    return Response({
        "username": u.username,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "phone_number": u.phone_number,
    })
