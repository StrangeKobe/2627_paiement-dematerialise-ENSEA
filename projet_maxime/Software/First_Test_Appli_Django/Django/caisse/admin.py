from django.contrib import admin
from .models import (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
    Affectation, JetonPaiement,
)

admin.site.register(Pole)
admin.site.register(Evenement)
admin.site.register(Categorie)
admin.site.register(Produit)
admin.site.register(ProfilUtilisateur)
admin.site.register(Recharge)
admin.site.register(Transaction)
admin.site.register(LigneTransaction)
admin.site.register(Affectation)
admin.site.register(JetonPaiement)
