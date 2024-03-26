from django.db import models
from django.forms import ModelForm
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
class BrewProfile(models.Model):
    brew_method = (
            ('', 'Select a brew method'),
            ('Pour over', 'Pour over'),
            ('Immersion', 'Immersion')
        )
    
                        #### Basic Info ###
    creation_date = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    
                        #### Brew Parameters ###
    # Grind Parameters
    grind_size = models.PositiveBigIntegerField(default=0)
    grind_weight = models.PositiveBigIntegerField(default=0)
    # Water Parameters
    water_weight = models.PositiveBigIntegerField(default=0)
    water_temp = models.PositiveBigIntegerField(default=0)
    # Method
    brew_method = models.CharField(max_length=10, choices=brew_method)
    brew_device = models.CharField(max_length=100, default='None')
    steps = models.CharField(max_length=2000) # JSON string of steps
    # Array of instructions. Example: 
    # (pour type, water weight, flow rate, agitation level (low, medium, high))
    # example: [(center pour, 60g, 12g/s, high), (center pour, 100g, 6g/s, low)]
    
                        #### Rating Parameters ###
    rating = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(10), MinValueValidator(0)])
    
class BrewProfileForm(ModelForm):
    class Meta:
        model = BrewProfile
        fields = ['name', 'description', 'grind_size', 'grind_weight', 
                  'water_weight', 'water_temp', 'brew_method', 'brew_device', 
                  'steps', 'rating']