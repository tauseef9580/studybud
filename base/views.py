from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required # for restrict pages
from django.db.models import Q
from django.contrib.auth.models import User #to store data about user like sessionId and all
from django.contrib.auth import authenticate, login, logout #for login and logout pages
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm



# Create your views here.
# added by me

# rooms = [
#     {'id': 1, 'name': 'Lets Learn Python!'},
#     {'id': 2, 'name': 'Tryhackme Walkthrough'},
#     {'id': 3, 'name': 'Learn Web application Security'},

# ]

def loginPage(request):

    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        # try:
        #     user = User.objects.get(username=username)
        # except:
        #     messages.error(request, 'User does not exist.')

        # above line of code can use to brute-force the username, So, i commented out

        # if user exist
        user = authenticate(request, email=email, password=password)

        #if credintials are correct
        if user is not None:
            login(request, user)
            return redirect('home')
        
        else: # if user is not logged in
            messages.error(request, 'Username or Password does not exist.')


    context = {'page': page}
    return render(request, 'base/login_register.html', context)

    


def logoutUser(request):

    logout(request) # will delete the sessionId of the user
    return redirect('home') # redirect to home after getting logged out

def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            #process the user
            user = form.save(commit=False)

            #sanitizing the user data
            user.username = user.username.lower()
            user.save() # now register the user

            #log in the user automatically
            login(request, user)
            return redirect('home')
              
        else:
            messages.error(request, 'An error occured during registeration')

    return render(request, 'base/login_register.html', {'form': form})


def home(request):

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    # implementing Search bar
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()

    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))


    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count, 'room_messages': room_messages} # a dictionary for rooms
    # render takes two para, one is request and other is template file name
    return render(request,'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    # show comments
    #                           _set.all() will show all msgs, and order by most recent on top            
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')

        )

        room.participants.add(request.user)
        return redirect('room', pk=room.id)




    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request,pk):

    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {'user': user, 'rooms':rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)



@login_required(login_url='login') # to get access to below functions, user need to be logged in, otherwise, we will redirect to login page
def createRoom(request):
    form = RoomForm()

    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):

    topics = Topic.objects.all()

    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room) # instance is added so that we update instead of create

    if request.user != room.host: # if you are a host, then only you can edit and delete the room
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room.name=request.POST.get('name')
        room.topic=topic
        room.description=request.POST.get('description')
        room.save()
        
        return redirect('home')

    context = {'form':form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Message.objects.get(id=pk)

    if request.user != room.host: # if you are a host, then only you can edit and delete the room
        return HttpResponse('You are not allowed here!!')

    if request.method == "POST":
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj':room})


login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user: # if you are a host, then only you can edit and delete the room
        return HttpResponse('You are not allowed here!!')

    if request.method == "POST":
        message.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': message})

@login_required(login_url='login')
def updateUser(request):

    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)


    #context = {'form': form}
    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})