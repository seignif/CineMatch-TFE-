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

        html_message = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0A0A0F;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0F;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#12121A 0%,#1A1A2E 100%);border-radius:16px 16px 0 0;padding:40px;text-align:center;border-bottom:2px solid #E63946;">
            <p style="margin:0 0 8px 0;font-size:13px;letter-spacing:4px;color:#E63946;text-transform:uppercase;">Bienvenue sur</p>
            <h1 style="margin:0;font-size:42px;font-weight:900;letter-spacing:6px;color:#FFFFFF;">
              CINE<span style="color:#E63946;">MATCH</span>
            </h1>
            <p style="margin:12px 0 0 0;font-size:13px;color:#8892A4;letter-spacing:2px;">TROUVEZ VOS PARTENAIRES DE CINÉMA</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="background:#12121A;padding:48px 40px;">
            <p style="margin:0 0 8px 0;font-size:13px;color:#E63946;letter-spacing:2px;text-transform:uppercase;">Vérification de compte</p>
            <h2 style="margin:0 0 24px 0;font-size:26px;color:#FFFFFF;font-weight:700;">
              Bonjour {user.first_name}&nbsp;!
            </h2>
            <p style="margin:0 0 16px 0;font-size:16px;color:#B0B8C8;line-height:1.7;">
              Votre compte CineMatch a bien été créé. Il ne vous reste plus qu'une étape avant de rejoindre la communauté et de trouver vos partenaires de cinéma.
            </p>
            <p style="margin:0 0 36px 0;font-size:16px;color:#B0B8C8;line-height:1.7;">
              Cliquez sur le bouton ci-dessous pour confirmer votre adresse email et activer votre compte&nbsp;:
            </p>

            <!-- CTA Button -->
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="center" style="padding:0 0 36px 0;">
                  <a href="{verification_url}"
                     style="display:inline-block;background:#E63946;color:#FFFFFF;
                            font-size:16px;font-weight:700;letter-spacing:1px;
                            text-decoration:none;padding:18px 48px;
                            border-radius:50px;text-transform:uppercase;">
                    Confirmer mon email
                  </a>
                </td>
              </tr>
            </table>

            <!-- Divider -->
            <hr style="border:none;border-top:1px solid #1E1E2E;margin:0 0 28px 0;">

            <!-- Fallback link -->
            <p style="margin:0 0 8px 0;font-size:13px;color:#8892A4;">
              Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur&nbsp;:
            </p>
            <p style="margin:0 0 28px 0;word-break:break-all;">
              <a href="{verification_url}" style="color:#E63946;font-size:13px;text-decoration:none;">{verification_url}</a>
            </p>

            <p style="margin:0;font-size:13px;color:#8892A4;line-height:1.6;">
              Ce lien est valable <strong style="color:#F5F5F5;">24 heures</strong>.<br>
              Si vous n'avez pas créé de compte CineMatch, ignorez simplement cet email.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#0D0D14;border-radius:0 0 16px 16px;padding:24px 40px;text-align:center;">
            <p style="margin:0 0 4px 0;font-size:12px;color:#8892A4;">
              &copy; 2026 CineMatch &mdash; La plateforme cinéma belge
            </p>
            <p style="margin:0;font-size:12px;color:#4A5568;">
              Cet email a été envoyé depuis <a href="https://cinematch.be" style="color:#E63946;text-decoration:none;">cinematch.be</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

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
    def send_export_confirmation(user):
        """Email de confirmation après export RGPD."""
        from django.utils import timezone
        send_mail(
            subject="Vos données CineMatch ont été exportées",
            message=(
                f"Bonjour {user.first_name},\n\n"
                f"Vos données ont été exportées le {timezone.now().strftime('%d/%m/%Y à %H:%M')}.\n\n"
                "Si vous n'êtes pas à l'origine de cette action, contactez-nous immédiatement.\n\n"
                "L'équipe CineMatch"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    @staticmethod
    def send_deletion_confirmation(email, first_name):
        """Email de confirmation après suppression de compte."""
        send_mail(
            subject="Votre compte CineMatch a été supprimé",
            message=(
                f"Bonjour {first_name},\n\n"
                "Votre demande de suppression de compte a bien été prise en compte.\n"
                "Vos données personnelles seront définitivement supprimées dans 30 jours.\n\n"
                "L'équipe CineMatch"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )

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
