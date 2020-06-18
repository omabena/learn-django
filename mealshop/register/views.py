from django.shortcuts import render, redirect
from .forms import RegisterForm, ProfileForm


def register(response):
    if response.method == 'POST':
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save()

        else:
            return redirect('/login/')

        return redirect('/')
    else:
        form = RegisterForm()
        profile_form = ProfileForm()

    return render(response, 'register/register.html', {
        'form': form, 'profile_form': profile_form})
