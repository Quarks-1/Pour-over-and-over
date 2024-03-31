from django.shortcuts import render, redirect, get_object_or_404
from pourover.models import BrewProfile, BrewProfileForm
from django.utils import timezone


# Create your views here.


def home_page(request):
    return render(request, 'pourover/home_page.html', {'profiles': BrewProfile.objects.all()})

def brew_page(request, id):
    profile = get_object_or_404(BrewProfile, id=id)
    return render(request, 'pourover/brew_page.html', {'profile': profile, 'id': id})

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