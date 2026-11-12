from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

User = get_user_model()


class RegisterView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        password = str(request.data.get("password", ""))
        full_name = str(request.data.get("full_name", "")).strip()[:160]
        if not email or "@" not in email:
            raise ValidationError({"email": "Adresse e-mail valide obligatoire."})
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError({"email": "Un compte existe déjà avec cette adresse."})
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise ValidationError({"password": list(exc.messages)}) from exc
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name[:150],
            display_name=full_name,
        )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": self.user_data(user)}, status=status.HTTP_201_CREATED)

    @staticmethod
    def user_data(user):
        return {"id": user.pk, "email": user.email, "full_name": user.display_name or user.get_full_name()}


class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        password = str(request.data.get("password", ""))
        user = authenticate(request, username=email, password=password)
        if not user or not user.is_active:
            raise ValidationError({"detail": "Identifiants incorrects."})
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": RegisterView.user_data(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(RegisterView.user_data(request.user))
