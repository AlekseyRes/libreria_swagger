from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserMeSerializer, UserSerializer


class UserApiViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={200: UserSerializer},
        operation_description=(
            'Actualización parcial de un usuario. La contraseña es opcional: '
            'si se omite o se envía vacía, se conserva la contraseña actual.'
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        password = data.get('password')

        # An absent or empty password must be ignored completely. Keeping it in
        # the payload when it is present lets the serializer validate min_length.
        if password is None or str(password).strip() == '':
            data.pop('password', None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.pop('password', None)

        # Hash the new password only when it was explicitly sent and non-empty.
        if password is not None and str(password).strip():
            instance.set_password(password)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: UserMeSerializer},
        operation_description='Devuelve los datos del usuario autenticado.',
    )
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)
