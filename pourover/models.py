from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
class BrewProfile(models.Model):
    class BrewType(models.TextChoices):
        POUR_OVER = 'PO', 'Pour Over'
        IMMERSION = 'IM', 'Immersion'
        ESPRESSO = 'ES', 'Espresso',        
        OTHER = 'OT', 'Other'
    
                        #### Basic Info ###
    creation_date = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    
                        #### Brew Parameters ###
    # Grind Parameters
    burr_seaoned = models.BooleanField(default=False)
    steps = models.CharField(max_length=2000) # JSON string of steps
    grind_size = models.PositiveBigIntegerField(default=0)
    grind_weight = models.PositiveBigIntegerField(default=0)
    # Water Parameters
    water_weight = models.PositiveBigIntegerField(default=0)
    water_temp = models.PositiveBigIntegerField(default=0)
    # Method
    brew_method = models.CharField(max_length=2, choices=BrewType.choices, default=BrewType.OTHER)
    brew_machine = models.CharField(max_length=100, default='None')
    
                        #### Rating Parameters ###
    personal_rating = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(10), MinValueValidator(0)])