from django.shortcuts import render, redirect, render_to_response, HttpResponse
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.template.context_processors import csrf
from accounts.forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.conf import settings
from .models import User
import stripe
import datetime
import arrow
import json

stripe.api_key = settings.STRIPE_SECRET


# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                customer = stripe.Customer.create(
                    email=form.cleaned_data['email'],
                    card=form.cleaned_data['stripe_id'],
                    plan='1',
                )
            except stripe.error.CardError, e:
                messages.error(request, "Your card was declined!")

            if customer:
                user = form.save()
                user.stripe_id = customer.id
                user.subscription_end = arrow.now().replace(weeks=+4).datetime
                user.save()

                user = auth.authenticate(email=request.POST.get('email'),
                                         password=request.POST.get('password1'))

                if user:
                    auth.login(request, user)
                    messages.success(request, "You have successfully registered")
                    return redirect(reverse('profile'))

                else:
                    messages.error(request, "unable to log you in at this time!!!")
            else:
                messages.error(request, "We were unable to take a payment with that card!")

    else:
        today = datetime.date.today()
        form = UserRegistrationForm(initial={'expiry_month': today.month,
                                             'expiry_year': today.year})

    args = {'form': form, 'publishable': settings.STRIPE_PUBLISHABLE}
    args.update(csrf(request))

    return render(request, 'register.html', args)


# Subscrtiption Cancel
@login_required(login_url='/accounts/login/')
def cancel_subscription(request):
    try:
        customer = stripe.Customer.retrieve(request.user.stripe_id)

        customer.cancel_subscription(at_period_end=True)
    except Exception, e:
        messages.error(request, e)
    messages.success(request, "You have successfully cancelled your subscription")
    return redirect('profile')


# Renewing Subscription
@csrf_exempt
def subscriptions_webhook(request):
    event_json = json.loads(request.body)

    # Verify the event by fetching it from Stripe

    try:
        # firstly verify this is a real event generated by Stripe.com
        event = stripe.Event.retrieve(event_json['id'])

        user = User.objects.get(stripe_id=event_json['customer'])

        if user and event_json['type'] == 'invoice.payment_succeeded':
            user.subscription_end = arrow.now().replace(weeks=+4).datetime
            user.save()

    except InvalidRequestError, e:
        return HttpResponse(status=404)

    return HttpResponse(status=200)


def login(request, success_url=None):
    # if request.user.is_authenticated():
    #     return redirect(reverse('profile'))
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(email=request.POST.get('email'),
                                     password=request.POST.get('password'))

            if user is not None:
                auth.login(request, user)
                messages.success(request, "You have successfully logged in")
                return redirect(reverse('profile'))
            else:
                form.add_error(None, "Your email or password was not recognised")
                return render(request, 'login.html', {'form': form})
        else:
            return render(request, 'login.html', {'form': form})
    else:
        form = UserLoginForm

        args = {'form': form}
        args.update(csrf(request))
        return render(request, 'login.html', args)


@login_required(login_url='/accounts/login/')  # decorator means only allowed if logged in
def profile(request):
    # subscription_humanize = arrow.now(request.user.subscription_end).humanize()
    # joined_humanized = arrow.now(request.user.date_joined).humanize()
    # args = {'subscription_humanize': subscription_humanize, 'joined_humanized': joined_humanized}
    return render(request, 'profile.html')


def logout(request):
    auth.logout(request)
    messages.success(request, 'You have logged out')
    return render(request, 'index.html')


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Your profile has been updated')
            return HttpResponseRedirect('/profile')
        else:
            # form = ContactView()
            # messages.add_message(request, messages.ERROR, 'Your message not sent. Not enough data')
            return render(request, 'loggedin.html', {'form': form})

    else:
        form = UserProfileForm()
        return render(request, 'loggedin.html', {'form': form})


def search_profile(request):
    if request.method == "POST":
        search_text = request.POST["search_text"]
    else:
        search_text = ''

    profiles = User.objects.filter(first_name__contains=search_text)

    return render_to_response('ajax_search.html', {'results': profiles})


'''@login_required
def user_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.post)
        if form.is_valid():
            form.save()
            return render(request, 'index.html')
    else:
        user = request.user
        profile = user.profile
        form = UserProfileForm(instance=profile)

    args = {}
    args.update(csrf(request))

    args['form'] = form

    return render_to_response('loggedin.html', args)'''

'''def register(request, register_form=UserRegistrationForm):
    if request.method == 'POST':
        form = register_form(request.POST)
        if form.is_valid():
            form.save()
            user = auth.authenticate(email=request.POST.get('email'),
                                     password=request.POST.get('password1'))
            if user:

                messages.success(request, "You have successfully registered")
                email = EmailMessage('Confirmation', 'This is a confirmation email', to=[request.POST.get('email')])
                email.send()
                return redirect(reverse('login'))
            else:
                messages.error(request, 'unable to log you in at this point!')
    else:
        form = register_form()
    args = {'form': form}
    args.update(csrf(request))

    return render(request, 'register.html', args)'''
