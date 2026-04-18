import pandas as pd
import base64
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from io import BytesIO

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

from .cleaning_engine import clean_dataframe
from .text_cleaning import read_text_file
from .image_cleaning import process_image

import random
import time
from django.core.mail import send_mail
from django.contrib.auth.models import User

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

# ================= HOME =================
def home(request):
    return render(request, 'home.html')

def history(request):
    return render(request, 'history.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Please enter username and password")
            return redirect('login')

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect('login')

        if not user.is_active:
            messages.error(request, "Account not verified. Please verify OTP first")
            return redirect('login')

        login(request, user)
        return redirect('home')

    return render(request, 'login.html')


def signup_view(request):
    return render(request, 'signup.html')

def forgot_password(request):
    return render(request, 'forgot_password.html')

# ================= SIGNUP =================
def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        otp = str(random.randint(100000, 999999))

        # session store
        request.session['otp'] = otp
        request.session['otp_time'] = time.time()
        request.session['email'] = email
        request.session['username'] = username
        request.session['password'] = password

        send_otp(email, otp)

        return redirect('verify_otp')

    return render(request, 'signup.html')


# ================= SEND OTP =================
def send_otp(email, otp):
    send_mail(
        'OTP Verification',
        f'Your OTP is {otp}',
        'your_email@gmail.com',
        [email],
        fail_silently=False,
    )


# ================= VERIFY OTP =================
def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        real_otp = request.session.get('otp')
        otp_time = request.session.get('otp_time')

        # ⏱️ Expiry check (60 sec)
        if time.time() - otp_time > 60:
            return render(request, 'verify_otp.html', {'error': 'OTP Expired'})

        if user_otp == real_otp:
            # create verified user
            user = User.objects.create_user(
                username=request.session['username'],
                email=request.session['email'],
                password=request.session['password']
            )

            user.is_active = True
            user.save()

            return redirect('login')

        else:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})

    return render(request, 'verify_otp.html')


# ================= RESEND OTP =================
def resend_otp(request):
    email = request.session.get('email')

    if not email:
        return redirect('signup')

    otp = str(random.randint(100000, 999999))

    request.session['otp'] = otp
    request.session['otp_time'] = time.time()

    send_otp(email, otp)

    return redirect('verify_otp')

# ================= UPLOAD =================
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')

        if not file:
            messages.error(request, "No file selected")
            return redirect('home')

        name = file.name.lower()
        request.session['filename'] = file.name

        try:
            # ================= DATA =================
            if name.endswith(('.csv', '.xlsx')):
                df = pd.read_csv(file) if name.endswith('.csv') else pd.read_excel(file)

                request.session['data'] = df.to_json()
                request.session['type'] = 'data'

                request.session['missing'] = int(df.isnull().sum().sum())
                request.session['total'] = int(df.size)

            # ================= TEXT =================
            elif name.endswith(('.txt', '.docx', '.pdf', '.rtf')):
                df, props = read_text_file(file)

                if df is None:
                    messages.error(request, "Text file error")
                    return redirect('home')

                request.session['data'] = df.to_json()
                request.session['text_props'] = props
                request.session['type'] = 'text'

            # ================= IMAGE =================
            elif name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img, text, props = process_image(file)

                if img is None:
                    messages.error(request, "Image error")
                    return redirect('home')

                buffer = BytesIO()
                img.save(buffer, format="PNG")

                request.session['image'] = buffer.getvalue()
                request.session['ocr'] = text
                request.session['img_props'] = props
                request.session['type'] = 'image'

            else:
                messages.error(request, "Unsupported file type")
                return redirect('home')

            # 🔥 IMPORTANT: PREVIEW पर भेजो (NOT OUTPUT)
            return redirect('preview')

        except Exception as e:
            print("UPLOAD ERROR:", e)
            messages.error(request, "Processing error")
            return redirect('home')

    return redirect('home')


# ================= PREVIEW =================
def preview(request):
    file_type = request.session.get('type')

    if not file_type:
        return redirect('home')

    context = {
        'filename': request.session.get('filename'),
        'type': file_type
    }

    # ================= DATA =================
    if file_type == 'data':
        df = pd.read_json(request.session.get('data'))

        # 🔥 IMPORTANT: table show
        context['table'] = df.head(20).to_html(classes='table table-striped', index=False)

        context['missing'] = int(df.isnull().sum().sum())
        context['total'] = int(df.size)

    return render(request, 'cleaned.html', context)


def preview(request):
    file_type = request.session.get('type')

    if not file_type:
        return redirect('home')

    context = {
        'filename': request.session.get('filename'),
        'type': file_type
    }

    # ================= DATA =================
    if file_type == 'data':
        df = pd.read_json(request.session.get('data'))

        context['table'] = df.head().to_html(classes='table')
        context['missing'] = request.session.get('missing')
        context['total'] = request.session.get('total')

        # GRAPH
        try:
            missing = context['missing']
            present = context['total'] - missing

            plt.figure()
            plt.pie([missing, present], labels=['Missing', 'Present'], autopct='%1.1f%%')

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)

            context['graph'] = base64.b64encode(buffer.getvalue()).decode()
        except:
            context['graph'] = None

    # ================= TEXT =================
    elif file_type == 'text':
        df = pd.read_json(request.session.get('data'))
        context['table'] = df.to_html()
        context['text_props'] = request.session.get('text_props')

    # ================= IMAGE =================
    elif file_type == 'image':
        image_data = request.session.get('image')
        context['image'] = base64.b64encode(image_data).decode()
        context['ocr'] = request.session.get('ocr')
        context['img_props'] = request.session.get('img_props')

    return render(request, 'cleaned.html', context)


# ================= CLEAN =================

from .models import CleanedFile

def clean_data(request):
    data = request.session.get('data')
    df = pd.read_json(data)

    cleaned_df, accuracy = clean_dataframe(df)

    request.session['cleaned'] = cleaned_df.to_json()
    request.session['accuracy'] = accuracy

    # 🔥 SAVE USER HISTORY
    if request.user.is_authenticated:
        CleanedFile.objects.create(
            user=request.user,
            filename=request.session.get('filename'),
            accuracy=accuracy
        )

    return redirect('output')

def clean_data(request):
    file_type = request.session.get('type')

    # ❌ DATA नहीं है तो home भेज
    if file_type != 'data':
        return redirect('home')

    data = request.session.get('data')
    df = pd.read_json(data)

    cleaned_df, accuracy = clean_dataframe(df)

    request.session['cleaned'] = cleaned_df.to_json()
    request.session['accuracy'] = accuracy

    return redirect('output')


# ================= OUTPUT =================
def output(request):
    data = request.session.get('cleaned')

    if not data:
        return redirect('home')

    df = pd.read_json(data)

    context = {
        'filename': request.session.get('filename'),
        'accuracy': request.session.get('accuracy'),
        'table': df.head().to_html(classes='table')
    }

    return render(request, 'report.html', context)


# ================= DOWNLOAD =================
def download(request):
    data = request.session.get('cleaned')

    if not data:
        return redirect('home')

    df = pd.read_json(data)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cleaned.csv"'

    df.to_csv(response, index=False)

    return response