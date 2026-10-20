from email.mime.image import MIMEImage

from django.core.mail import EmailMultiAlternatives, send_mail


def envoyer_email_code(code_admin, code_clair):
    """Previent la personne qu'un code de securite vient de lui etre
    attribue, avec le code en clair (jamais ni stocke ni reaffiche apres
    coup) et le contact de l'admin ecole qui l'a defini."""
    from .models import Affectation

    utilisateur = code_admin.user
    destinataire = utilisateur.email
    if not destinataire:
        return
    civilite = utilisateur.first_name or utilisateur.username
    roles = Affectation.objects.filter(user=utilisateur, pole=code_admin.pole)
    noms_roles = ", ".join(r.get_role_display() for r in roles) or "un rôle à pouvoir"
    cible = code_admin.pole.nom if code_admin.pole else "l'ADE"
    admin = code_admin.definie_par
    if admin.first_name or admin.last_name:
        nom_admin = f"{admin.first_name} {admin.last_name}".strip()
    else:
        nom_admin = admin.username
    corps = (
        f"Bonjour {civilite},\n\n"
        f"Un code de sécurité vient de t'être attribué sur ton compte ENSEA "
        f"Cashless, pour ton rôle de {noms_roles} ({cible}).\n\n"
        f"Ce code te sera demandé à chaque connexion, en plus de ton identifiant "
        f"habituel :\n\n"
        f"    {code_clair}\n\n"
        f"Garde-le précieusement et ne le communique à personne.\n\n"
        f"Pour toute question, contacte {nom_admin}, qui te l'a attribué.\n\n"
        f"Bien cordialement,\n"
        f"{nom_admin}\n"
        f"Administration ENSEA Cashless"
    )
    try:
        send_mail(
            subject="Ton code de sécurité ENSEA Cashless",
            message=corps, from_email=None, recipient_list=[destinataire],
            fail_silently=True,
        )
    except Exception:
        pass


def envoyer_email_suppression(demande):
    """Previent l'etudiant que son compte va etre supprime (anonymise)
    dans 3 mois, et l'invite a demander le remboursement de son solde
    aupres de l'admin ecole avant cette echeance."""
    profil = demande.profil
    destinataire = profil.user.email
    if not destinataire:
        return
    civilite = profil.user.first_name or profil.user.username
    admin = demande.demande_par
    if admin.first_name or admin.last_name:
        nom_admin = f"{admin.first_name} {admin.last_name}".strip()
    else:
        nom_admin = admin.username
    corps = (
        f"Bonjour {civilite},\n\n"
        f"Nous vous informons que votre compte sur le portefeuille ENSEA Cashless "
        f"a été signalé pour suppression par {nom_admin}, de l'administration de "
        f"l'école.\n\n"
        f"Conformément à ce délai, votre compte sera définitivement supprimé "
        f"(anonymisé) le {demande.date_suppression_prevue:%d/%m/%Y}, soit dans "
        f"{demande.jours_restants} jours.\n\n"
        f"Si votre portefeuille dispose encore d'un solde, nous vous invitons à "
        f"vous rapprocher au plus vite de {nom_admin} pour en demander le "
        f"remboursement. Passé ce délai, tout solde restant sera considéré comme "
        f"reversé à l'association.\n\n"
        f"Si vous pensez qu'il s'agit d'une erreur, contactez sans attendre "
        f"{nom_admin}, qui pourra annuler cette suppression avant l'échéance.\n\n"
        f"Nous vous remercions pour votre confiance et vous souhaitons une "
        f"excellente continuation.\n\n"
        f"Bien cordialement,\n"
        f"{nom_admin}\n"
        f"Administration ENSEA Cashless"
    )
    try:
        send_mail(
            subject="Suppression prochaine de votre compte ENSEA Cashless",
            message=corps, from_email=None, recipient_list=[destinataire],
            fail_silently=True,
        )
    except Exception:
        pass


def envoyer_recu(transaction):
    """Envoie le recu d'achat : un email HTML avec la photo de chaque
    produit a cote de sa ligne, plus une version texte simple en repli
    pour les clients mail qui n'affichent pas le HTML."""
    destinataire = transaction.profil.user.email
    if not destinataire:
        return
    lignes = list(transaction.lignes.all())

    corps_texte = (
        f"Recu d'achat - {transaction.pole.nom}\n\n"
        f"Date : {transaction.date_operation.strftime('%d/%m/%Y %H:%M')}\n\n"
        + "\n".join(
            f"  {ligne.quantite} x {ligne.libelle} .... {ligne.prix_unitaire} EUR"
            for ligne in lignes
        )
        + f"\n\nTotal paye : {transaction.montant_total} EUR\n"
    )

    images_a_joindre = []
    lignes_html = ""
    for i, ligne in enumerate(lignes):
        cid = f"produit{i}"
        photo_disponible = bool(ligne.produit.photo) and ligne.produit.photo.storage.exists(ligne.produit.photo.name)
        if photo_disponible:
            vignette = (
                f'<img src="cid:{cid}" width="48" height="48" alt="" '
                f'style="border-radius:8px;object-fit:cover;vertical-align:middle;'
                f'margin-right:10px;display:inline-block;">'
            )
            images_a_joindre.append((cid, ligne.produit.photo))
        else:
            vignette = (
                '<span style="width:48px;height:48px;border-radius:8px;background:#FFF0F4;'
                'display:inline-block;vertical-align:middle;margin-right:10px;"></span>'
            )
        sous_total = ligne.prix_unitaire * ligne.quantite
        lignes_html += (
            '<tr>'
            f'<td style="padding:8px 0;border-bottom:1px solid #F1F5F9;">{vignette}'
            f'<span style="vertical-align:middle;color:#0F172A;">{ligne.quantite} x {ligne.libelle}</span></td>'
            f'<td style="padding:8px 0;border-bottom:1px solid #F1F5F9;text-align:right;'
            f'vertical-align:middle;color:#0F172A;">{sous_total:.2f} EUR</td>'
            '</tr>'
        )

    corps_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;">
        <h2 style="color:#C8004B;margin-bottom:4px;">Reçu d'achat</h2>
        <p style="color:#64748B;font-size:13px;margin-top:0;">
            {transaction.pole.nom} — {transaction.date_operation.strftime('%d/%m/%Y à %H:%M')}
        </p>
        <table style="width:100%;border-collapse:collapse;">
            {lignes_html}
        </table>
        <p style="font-size:18px;font-weight:bold;text-align:right;margin-top:12px;color:#0F172A;">
            Total payé : {transaction.montant_total:.2f} EUR
        </p>
        <p style="color:#94A3B8;font-size:12px;">Merci pour ton achat !</p>
    </div>
    """

    try:
        message = EmailMultiAlternatives(
            subject=f"Reçu d'achat - {transaction.pole.nom}",
            body=corps_texte, from_email=None, to=[destinataire],
        )
        message.attach_alternative(corps_html, "text/html")
        for cid, photo in images_a_joindre:
            try:
                with photo.open("rb") as fichier:
                    image = MIMEImage(fichier.read())
                image.add_header("Content-ID", f"<{cid}>")
                image.add_header("Content-Disposition", "inline", filename=cid)
                message.attach(image)
            except Exception:
                continue
        message.send(fail_silently=True)
    except Exception:
        pass
