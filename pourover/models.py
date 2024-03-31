from django.db import models
from django.forms import ModelForm
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.utils.safestring import mark_safe
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
    total_water_weight = models.PositiveBigIntegerField(default=0)
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
    
    def __str__(self):
        return f'Name: {self.name}, Description: {self.description}, Rating: {self.rating}, Steps: {self.steps}'
    
class BrewProfileForm(ModelForm):
    class Meta:
        model = BrewProfile
        fields = ['name', 'description', 'grind_size', 'grind_weight', 
                  'total_water_weight', 'water_temp', 'brew_method', 'brew_device', 
                  'steps', 'rating']
        labels = {
            'name': 'Name',
            'description': 'Description',
            'grind_size': 'Grind Size',
            'grind_weight': 'Grind Weight',
            'total_water_weight': 'Total Water Weight',
            'water_temp': 'Water Temperature',
            'brew_method': 'Brew Method',
            'brew_device': 'Brew Device',
            'steps': 'Steps',
            'rating': 'Rating'
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(BrewProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'profile_form'
        label_class = "label_arrow"
        for field_name, field in self.fields.items():
            field.label = mark_safe(f'<span class="{label_class}">{field.label}</span>')
        
        # self.fields['name'].required = True
        # self.fields['description'].required = False
        # self.fields['grind_size'].required = True
        # self.fields['grind_weight'].required = True
        self.fields['total_water_weight'].widget.attrs['readonly'] = True
        self.fields['total_water_weight'].required = False
        # self.fields['water_temp'].required = True
        # self.fields['brew_method'].required = True
        self.fields['steps'].widget.attrs['readonly'] = True
        self.fields['steps'].required = False
        # self.fields['rating'].required = True