from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.films.serializers import FilmSerializer
from apps.users.models import ProfileFilmSignature, UserProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password2',
            'first_name', 'last_name', 'date_of_birth', 'city',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # Signal crée déjà le profil, get_or_create pour sécurité
        UserProfile.objects.get_or_create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    films_signature = FilmSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'profile_picture', 'mood',
            'genre_preferences', 'films_signature',
            'badges', 'stats',
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'date_of_birth', 'city', 'profile',
        ]
        read_only_fields = ['id', 'email']


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Modifier le profil cinématographique."""
    films_signature_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = UserProfile
        fields = ['bio', 'mood', 'genre_preferences', 'films_signature_ids']

    def validate_films_signature_ids(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("Maximum 5 films signature autorisés.")
        return value

    def update(self, instance, validated_data):
        films_ids = validated_data.pop('films_signature_ids', None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if films_ids is not None:
            from apps.films.models import Film
            instance.films_signature.clear()
            for order, film_id in enumerate(films_ids):
                film = Film.objects.filter(id=film_id).first()
                if film:
                    ProfileFilmSignature.objects.create(
                        profile=instance, film=film, order=order
                    )
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, validators=[validate_password]
    )
