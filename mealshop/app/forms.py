from django import forms
from .models import Menu
from .models import Order


class MenuForm(forms.Form):

    class Meta:
        model = Menu
        widgets = {'menu_options': forms.widgets.CheckboxSelectMultiple()}


class OrderMenu(forms.Form):

    class Meta:
        model = Order


class ChooseMenu(forms.Form):

    class Meta:
        model = Menu
