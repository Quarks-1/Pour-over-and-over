from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator


# class BrewProfileForm(forms.Form):
    
#                         #### Basic Info ###
#     name = forms.CharField(max_length=50)
#     description = forms.CharField(max_length=200)
    
#                         #### Brew Parameters ###
#     # Grind Parameters
#     grind_size = forms.PositiveBigIntegerField(default=0)
#     grind_weight = forms.PositiveBigIntegerField(default=0)
#     # Water Parameters
#     water_weight = forms.PositiveBigIntegerField(default=0)
#     water_temp = forms.PositiveBigIntegerField(default=0)
#     # Method
#     brew_device = forms.CharField(max_length=100, default='None')
#     steps = forms.CharField(max_length=2000) # JSON string of steps
#                         #### Rating Parameters ###
#     rating = forms.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(10), MinValueValidator(0)])