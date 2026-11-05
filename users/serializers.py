from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        min_length=8,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'password',
            'first_name',
            'last_name',
            'telefono',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
        )
        read_only_fields = ('id', 'date_joined')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('password', None)
        return data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if password is None or not str(password).strip():
            raise serializers.ValidationError(
                {'password': 'La contraseña es obligatoria.'}
            )
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password is not None and str(password).strip():
            user.set_password(password)
            user.save(update_fields=['password'])
        return user


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'telefono',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
        )
        read_only_fields = fields
