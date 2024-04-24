from django.shortcuts import render, redirect, get_object_or_404
from pourover.models import BrewProfile, BrewProfileForm
from django.utils import timezone
import serial

homed = True

# Create your views here.

class Step:
    def __init__(self, action, water_weight, flow_rate, agitation):
        self.action = action
        self.water_weight = water_weight
        self.flow_rate = flow_rate
        self.agitation = agitation

def home_page(request):
    global homed
    # Home printer
    if not homed:
        try:
            printer = serial.Serial("/dev/ttyUSB0", 115200)
            printer.write(str.encode("G28 X Y Z\r\n"))
            homed = True
        except serial.SerialException:
            print('WARNING: PRINTER NOT CONNECTED')
    return render(request, 'pourover/home_page.html', {'profiles': BrewProfile.objects.all()})

def home_page_sorted(request, sort_order, order):
    if order == 'asc':
        return render(request, 'pourover/home_page.html', {'profiles': BrewProfile.objects.order_by(sort_order)})
    else:
        return render(request, 'pourover/home_page.html', {'profiles': BrewProfile.objects.order_by(f'-{sort_order}')})    

def brew_page(request, id):
    profile = get_object_or_404(BrewProfile, id=id)
    # Format steps for display
    steps = parseSteps(profile.steps)
    return render(request, 'pourover/brew_page.html', {'profile': profile, 'id': id, 'steps': steps})

def create_profile(request):
    if request.method == 'GET':
        context = {'form': BrewProfileForm()}
        return render(request, 'pourover/create_profile.html', context)
    print(request.POST)
    form = BrewProfileForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_data()
        invalid_fields = []
        for field, error in errors.items():
            invalid_fields.append((field, error[0].message))
        print("Invalid fields:")
        for field, message in invalid_fields:
            print(f"{field}: {message}")
          
            
        context = {'form': form}
        return render(request, 'pourover/create_profile.html', context)

    brew_profile = form.save(commit=False)  
    brew_profile.creation_date = timezone.now()
    print(brew_profile)
    brew_profile.save()
    return redirect('home_page')


def parseSteps(steps):
    parsed = []
    for step in steps.strip('][').split(','):
        temp = step.strip("'").split('/')
        if ' ' in temp[0]:
            temp[0] = temp[0][2:]
        temp[1] = int(temp[1])
        temp[2] = int(temp[2])
        if temp[0] == 'pre_wet':
            temp[0] = 'Pre-Wet'
        elif temp[0] == 'delay':
            temp[0] = 'Draw down delay'
            temp[3] = 'N/A'
        final = Step(temp[0], temp[1], temp[2], temp[3])
        parsed.append(final)
    return parsed