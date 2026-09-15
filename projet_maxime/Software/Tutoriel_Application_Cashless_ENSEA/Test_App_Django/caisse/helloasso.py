def inscrire_sur_helloasso(evenement, profil, quantite):
    """Pousse l'inscription vers HelloAsso. Isole entierement l'appel API
    reel (a implementer selon les identifiants HelloAsso du pole) pour que
    l'appel de vente ne puisse jamais echouer a cause d'un probleme reseau
    ou d'API : toute erreur ici est absorbee silencieusement."""
    try:
        # TODO : appel reel a l'API HelloAsso, retourne une reference si succes
        return None
    except Exception:
        return None
