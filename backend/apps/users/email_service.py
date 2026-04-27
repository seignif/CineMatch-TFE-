"""US-065 : Service d'envoi d'emails de vérification via Resend SMTP."""
import logging
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    def send_verification_email(user):
        """
        Envoie un email de vérification.
        Dev  : EMAIL_BACKEND=console → affiche dans le terminal Django.
        Prod : EMAIL_BACKEND=smtp   → smtp.resend.com.
        """
        from apps.users.models import EmailVerificationToken

        token_obj, _ = EmailVerificationToken.objects.update_or_create(
            user=user,
            defaults={
                'token': uuid.uuid4(),
                'expires_at': timezone.now() + timedelta(hours=24),
            },
        )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verification_url = f"{frontend_url}/verify-email/{token_obj.token}"

        html_message = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <div style="background:#0A0A0F;padding:30px;text-align:center;">
            <h1 style="color:#E63946;font-size:28px;">CineMatch</h1>
          </div>
          <div style="padding:30px;background:#12121A;color:#F5F5F5;">
            <h2>Bienvenue {user.first_name} !</h2>
            <p>Confirmez votre adresse email pour accéder à toutes les fonctionnalités.</p>
            <div style="text-align:center;margin:30px 0;">
              <a href="{verification_url}"
                 style="background:#E63946;color:white;padding:15px 30px;
                        border-radius:8px;text-decoration:none;font-weight:bold;">
                Confirmer mon email
              </a>
            </div>
            <p style="color:#8892A4;font-size:12px;">
              Ce lien est valable 24 heures.<br>
              Si vous n'avez pas créé de compte, ignorez cet email.
            </p>
          </div>
        </div>
        """

        try:
            send_mail(
                subject="Confirmez votre compte CineMatch",
                message=(
                    f"Bonjour {user.first_name},\n\n"
                    f"Confirmez votre email : {verification_url}\n\n"
                    "Lien valable 24h."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email de vérification envoyé à {user.email}")
        except Exception as e:
            logger.error(f"Erreur envoi email à {user.email}: {e}")
            raise

    @staticmethod
    def verify_token(token_str: str):
        """Vérifie le token et active le compte. Retourne (success, message)."""
        from apps.users.models import EmailVerificationToken
        try:
            token_obj = EmailVerificationToken.objects.select_related('user').get(
                token=token_str
            )
            if not token_obj.is_valid():
                return False, "Lien expiré. Demandez un nouveau lien depuis votre profil."

            user = token_obj.user
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            token_obj.delete()
            return True, "Email vérifié avec succès ! Bienvenue sur CineMatch."

        except EmailVerificationToken.DoesNotExist:
            return False, "Lien invalide ou déjà utilisé."
