import re

from django import forms 


class CityForm(forms.Form):
    city = forms.CharField(label="", max_length=30, widget=forms.TextInput(attrs={'class': 'enter_city', 'placeholder': 'Введите название города'}))

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not re.match(r'^[а-яА-Яa-zA-Z\s-]+$', city):
            # Если вводить любые три цифры, API возвращает города
            return ''
        return city