"""
Formulaires Django : ModelForm construit automatiquement un formulaire
a partir d'un modele. On evite ainsi de re-taper a la main la liste des
champs, leurs types HTML et leur validation.
"""

from django import forms

from .models import Categorie, Evenement, Produit, ProfilUtilisateur
from .models import Pole

TAILLE_MAX_IMAGE_MO = 5


def _valider_taille_image(fichier):
    """Refuse une image de plus de TAILLE_MAX_IMAGE_MO : sans limite,
    n'importe qui pourrait televerser des fichiers enormes et remplir le
    disque du serveur. Ne s'applique qu'a un fichier fraichement
    televerse : le fichier deja enregistre (quand le champ n'est pas
    touche a l'edition) n'a pas cet attribut et n'est jamais re-verifie."""
    if fichier and hasattr(fichier, "content_type") and fichier.size > TAILLE_MAX_IMAGE_MO * 1024 * 1024:
        raise forms.ValidationError(
            f"Image trop lourde ({fichier.size / 1024 / 1024:.1f} Mo) : "
            f"{TAILLE_MAX_IMAGE_MO} Mo maximum."
        )
    return fichier


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ["nom", "categorie", "prix", "stock", "disponible", "photo"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "prix": forms.NumberInput(attrs={"class": "form-control", "step": "0.10"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, pole=None, **kwargs):
        super().__init__(*args, **kwargs)
        # On ne propose que les categories du pole concerne, jamais celles
        # d'un autre pole.
        if pole is not None:
            self.fields["categorie"].queryset = pole.categories.all()
        self.fields["categorie"].required = False

    def clean_photo(self):
        return _valider_taille_image(self.cleaned_data.get("photo"))


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ["nom"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
        }


class BilletForm(forms.ModelForm):
    """Comme ProduitForm, mais pour un produit rattache a un evenement :
    pas de categorie (les evenements n'ont pas de rayon), le pole et
    l'evenement sont fixes par la vue, jamais choisis dans le formulaire.
    Le champ est_billet distingue une vraie entree (compte comme une
    presence) d'un simple produit vendu ce soir-la (boisson, ecocup...)."""

    class Meta:
        model = Produit
        fields = ["nom", "prix", "stock", "disponible", "photo", "est_billet"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prix": forms.NumberInput(attrs={"class": "form-control", "step": "0.10"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "est_billet": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_photo(self):
        return _valider_taille_image(self.cleaned_data.get("photo"))


class EvenementForm(forms.ModelForm):
    # Champ texte au format francais (jj/mm/aaaa hh:mm), plutot que le
    # widget natif "datetime-local" dont l'affichage (ordre jour/mois,
    # 12h/24h) depend de la langue du navigateur, pas du site.
    date_evenement = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(
            format="%d/%m/%Y %H:%M",
            attrs={"class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa hh:mm"},
        ),
    )
    date_fin_vente = forms.DateTimeField(
        required=False,
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(
            format="%d/%m/%Y %H:%M",
            attrs={"class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa hh:mm"},
        ),
    )

    class Meta:
        model = Evenement
        fields = ["nom", "date_evenement", "lieu", "photo", "date_fin_vente", "actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "lieu": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex. Foyer des élèves"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_photo(self):
        return _valider_taille_image(self.cleaned_data.get("photo"))


class InfoPersonnelleForm(forms.ModelForm):
    """Formulaire des informations personnelles, avec un principe
    d'ancrage : un champ deja renseigne est retire du formulaire, donc il
    devient impossible a modifier par l'etudiant lui-meme. Seul un futur
    compte admin ecole pourra corriger une erreur apres coup.

    Tous les champs sont obligatoires : lors du tout premier enregistrement,
    rien ne peut etre laisse vide.

    Nom et prenom vivent sur le compte Django (User), pas sur le profil ;
    on les ajoute donc comme champs "libres" et on les enregistre nous-
    memes dans save(), en plus des champs normaux du profil."""

    nom = forms.CharField(
        max_length=150, required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    prenom = forms.CharField(
        max_length=150, required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    date_naissance = forms.DateField(
        required=True,
        input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa",
                "pattern": r"\d{2}/\d{2}/\d{4}", "maxlength": "10", "inputmode": "numeric",
            },
        ),
    )

    class Meta:
        model = ProfilUtilisateur
        fields = ["date_naissance"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(["nom", "prenom", "email", "date_naissance"])
        instance = kwargs.get("instance")
        if instance and instance.user.last_name:
            del self.fields["nom"]
        if instance and instance.user.first_name:
            del self.fields["prenom"]
        if instance and instance.user.email:
            del self.fields["email"]
        if instance and instance.date_naissance:
            del self.fields["date_naissance"]

    def save(self, commit=True):
        profil = super().save(commit=False)
        if self.cleaned_data.get("nom"):
            profil.user.last_name = self.cleaned_data["nom"]
        if self.cleaned_data.get("prenom"):
            profil.user.first_name = self.cleaned_data["prenom"]
        if self.cleaned_data.get("email"):
            profil.user.email = self.cleaned_data["email"]
        if commit:
            profil.user.save()
            profil.save()
        return profil


class PoleForm(forms.ModelForm):
    class Meta:
        model = Pole
        fields = ["logo"]
        widgets = {
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_logo(self):
        return _valider_taille_image(self.cleaned_data.get("logo"))
 

class CorrectionProfilForm(forms.ModelForm):
    """Reservee a l'admin ecole : contrairement a InfoPersonnelleForm, tous
    les champs restent toujours modifiables, y compris deja ancres, pour
    corriger une erreur de saisie signalee par un etudiant."""

    nom = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    prenom = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    date_naissance = forms.DateField(
        required=False,
        input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa",
                "pattern": r"\d{2}/\d{2}/\d{4}", "maxlength": "10", "inputmode": "numeric",
            },
        ),
    )

    class Meta:
        model = ProfilUtilisateur
        fields = ["date_naissance"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.fields["nom"].initial = instance.user.last_name
            self.fields["prenom"].initial = instance.user.first_name
            self.fields["email"].initial = instance.user.email

    def save(self, commit=True):
        profil = super().save(commit=False)
        profil.user.last_name = self.cleaned_data.get("nom", "")
        profil.user.first_name = self.cleaned_data.get("prenom", "")
        profil.user.email = self.cleaned_data.get("email", "")
        if commit:
            profil.user.save()
            profil.save()
        return profil
