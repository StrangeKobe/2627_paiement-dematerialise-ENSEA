"""
Integration avec la billetterie HelloAsso.

MODE TEMPORAIRE : en attendant les identifiants d'API HelloAsso (client_id
et client_secret, a demander sur https://dev.helloasso.com aupres du
compte de l'ADE), la fonction ci-dessous simule la creation d'une
inscription et renvoie une fausse reference. Tout le reste du code
(declenchement automatique a l'achat d'un billet, affichage du badge de
synchronisation dans la liste des participants) est deja branche : le
jour ou les vrais identifiants seront disponibles, il suffira de remplacer
le corps de cette seule fonction par un vrai appel a l'API HelloAsso, sans
toucher a aucune autre partie de l'application.
"""

import secrets


def inscrire_sur_helloasso(evenement, profil, quantite):
    """Tente d'inscrire l'achat sur HelloAsso, renvoie la reference
    obtenue (ou None si l'inscription echoue ou n'est pas applicable).

    Appelee automatiquement a chaque achat d'un billet d'evenement,
    depuis transactions.executer_achat. Ne doit jamais lever d'exception :
    un souci cote HelloAsso ne doit jamais faire echouer une vente reelle
    payee par l'etudiant.
    """
    try:
        # TODO : remplacer ce bloc par un vrai appel a l'API HelloAsso
        # (creation d'un "Order"/"Payer" sur le formulaire de l'evenement)
        # une fois les identifiants obtenus. Voir https://dev.helloasso.com
        return f"MOCK-{secrets.token_hex(4).upper()}"
    except Exception:
        # Une inscription HelloAsso manquee ne doit jamais bloquer la vente.
        return None
