from django.shortcuts import render, get_object_or_404
from pourover.models import BrewProfile
from pourover.models import BrewProfileForm
from django.utils import timezone


# Create your views here.


def home_page(request):
    # if request.method == 'GET':
    return render(request, 'pourover/home_page.html', {'profiles': BrewProfile.objects.all()})

def brew_page(request, id):
    profile = get_object_or_404(BrewProfile, id=id)
    return render(request, 'pourover/brew_page.html', {'profile': profile})

def create_profile(request):
    if request.method == 'GET':
        context = {'form': BrewProfileForm()}
        return render(request, 'pourover/create_profile.html', context)
    form = BrewProfileForm(request.POST)
    if not form.is_valid():
        context = {'form': form}
        return render(request, 'pourover/create_profile.html', context)
    brew_profile = form.save(commit=False)  
    brew_profile.creation_date = timezone.now()
    brew_profile.save()
    return render(request, 'pourover/home_page.html', {})