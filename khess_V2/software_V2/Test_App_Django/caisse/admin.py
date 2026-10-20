from django.contrib import admin

from .models import (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
    Affectation, JetonPaiement,
    ParticipantImporte, Adhesion, CodeSecuriteAdmin,
    DemandeSuppressionCompte, TarifAdhesion,
)

for modele in (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
    Affectation, JetonPaiement,
    ParticipantImporte, Adhesion, CodeSecuriteAdmin,
    DemandeSuppressionCompte, TarifAdhesion,
):
    admin.site.register(modele)
