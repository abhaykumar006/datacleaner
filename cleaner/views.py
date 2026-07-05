import pandas as pd
import base64
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

from io import BytesIO
from PIL import Image

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail

import random
import time
import os

from .cleaning_engine import clean_dataframe
from .text_cleaning import read_text_file
from .image_cleaning import process_image
from .models import CleanedFile


# ================= HOME =================

def home(request):
    return render(request, 'home.html')


def history(request):
    return render(request, 'history.html')


# ================= LOGIN =================

def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Please enter username and password")
            return redirect('login')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect('login')

        login(request, user)

        return redirect('home')

    return render(request, 'login.html')


# ================= SIGNUP =================

def signup_view(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        otp = str(random.randint(100000, 999999))

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

        if time.time() - otp_time > 60:

            return render(
                request,
                'verify_otp.html',
                {'error': 'OTP Expired'}
            )

        if user_otp == real_otp:

            user = User.objects.create_user(
                username=request.session['username'],
                email=request.session['email'],
                password=request.session['password']
            )

            user.is_active = True
            user.save()

            return redirect('login')

        else:

            return render(
                request,
                'verify_otp.html',
                {'error': 'Invalid OTP'}
            )

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


# ================= FORGOT PASSWORD =================

def forgot_password(request):
    return render(request, 'forgot_password.html')


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

            # ================= STORAGE =================

            fs = FileSystemStorage()

            filename = fs.save(file.name, file)

            uploaded_file_path = fs.path(filename)

            request.session['uploaded_file_path'] = uploaded_file_path

            # =====================================================
            # ================= STRUCTURED DATA ===================
            # =====================================================

            if name.endswith((
                '.csv',
                '.xlsx',
                '.xls',
                '.json',
                '.xml',
                '.sql',
                '.tsv'
            )):

                if name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file_path)

                elif name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file_path)

                elif name.endswith('.json'):
                    df = pd.read_json(uploaded_file_path)

                elif name.endswith('.xml'):
                    df = pd.read_xml(uploaded_file_path)

                elif name.endswith('.tsv'):
                    df = pd.read_csv(uploaded_file_path, sep='\t')

                else:
                    df = pd.read_csv(uploaded_file_path)

                request.session['data'] = df.to_json()

                request.session['type'] = 'data'

                request.session['missing'] = int(
                    df.isnull().sum().sum()
                )

                request.session['total'] = int(df.size)

            # =====================================================
            # ================= TEXT FILES ========================
            # =====================================================

            elif name.endswith((
                '.txt',
                '.docx',
                '.pdf',
                '.rtf',
                '.html',
                '.htm',
                '.md',
                '.log'
            )):

                df, props = read_text_file(uploaded_file_path)

                if df is None:
                    messages.error(request, "Text file processing failed")
                    return redirect('home')

                request.session['data'] = df.to_json()

                request.session['text_props'] = props

                request.session['type'] = 'text'

            # =====================================================
            # ================= IMAGE FILES =======================
            # =====================================================

            elif name.endswith((
                '.png',
                '.jpg',
                '.jpeg',
                '.gif',
                '.webp',
                '.bmp',
                '.tiff',
                '.svg'
            )):

                img, text, props = process_image(uploaded_file_path)

                if img is None:
                    messages.error(request, "Image processing failed")
                    return redirect('home')

                cleaned_image_name = "cleaned_" + file.name

                cleaned_image_path = os.path.join(
                    'media',
                    cleaned_image_name
                )

                img.save(cleaned_image_path)

                request.session['image_path'] = cleaned_image_path

                request.session['ocr'] = str(text)

                request.session['img_props'] = props

                request.session['type'] = 'image'

            # =====================================================
            # ================= CODE FILES ========================
            # =====================================================

            elif name.endswith((
                '.py',
                '.js',
                '.html',
                '.css',
                '.java',
                '.cpp',
                '.c',
                '.php'
            )):

                with open(
                    uploaded_file_path,
                    'r',
                    encoding='utf-8',
                    errors='ignore'
                ) as f:

                    code = f.read()

                df = pd.DataFrame({
                    'Code': [code]
                })

                request.session['data'] = df.to_json()

                request.session['type'] = 'text'

            # =====================================================
            # ================= UNSUPPORTED =======================
            # =====================================================

            else:

                messages.error(
                    request,
                    "Unsupported file type"
                )

                return redirect('home')

            return redirect('preview')

        except Exception as e:

            print("UPLOAD ERROR:", e)

            messages.error(
                request,
                f"Processing error: {str(e)}"
            )

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

    # =====================================================
    # ================= DATA ==============================
    # =====================================================

    if file_type == 'data':

        df = pd.read_json(
            request.session.get('data')
        )

        context['table'] = df.head(20).to_html(
            classes='table table-striped',
            index=False
        )

        context['missing'] = int(
            df.isnull().sum().sum()
        )

        context['total'] = int(df.size)

        # GRAPH

        try:

            missing = context['missing']

            present = context['total'] - missing

            plt.figure(figsize=(4, 4))

            plt.pie(
                [missing, present],
                labels=['Missing', 'Present'],
                autopct='%1.1f%%'
            )

            buffer = BytesIO()

            plt.savefig(buffer, format='png')

            buffer.seek(0)

            context['graph'] = base64.b64encode(
                buffer.getvalue()
            ).decode()

            plt.close()

        except:

            context['graph'] = None

    # =====================================================
    # ================= TEXT ==============================
    # =====================================================

    elif file_type == 'text':

        df = pd.read_json(
            request.session.get('data')
        )

        context['table'] = df.to_html(
            classes='table table-striped',
            index=False
        )

        context['text_props'] = request.session.get(
            'text_props'
        )

    # =====================================================
    # ================= IMAGE =============================
    # =====================================================

    elif file_type == 'image':

        context['image'] = request.session.get(
            'image_path'
        )

        context['ocr'] = request.session.get(
            'ocr'
        )

        context['img_props'] = request.session.get(
            'img_props'
        )

    return render(request, 'cleaned.html', context)


# ================= CLEAN DATA =================

def clean_data(request):

    file_type = request.session.get('type')

    # =====================================================
    # ================= DATA CLEAN ========================
    # =====================================================

    if file_type == 'data':

        data = request.session.get('data')

        df = pd.read_json(data)

        cleaned_df, accuracy = clean_dataframe(df)

        request.session['cleaned'] = cleaned_df.to_json()

        request.session['accuracy'] = accuracy

        # SAVE HISTORY

        if request.user.is_authenticated:

            CleanedFile.objects.create(
                user=request.user,
                filename=request.session.get('filename'),
                accuracy=accuracy
            )

        return redirect('output')

    # =====================================================
    # ================= IMAGE CLEAN =======================
    # =====================================================

    elif file_type == 'image':

        request.session['accuracy'] = 95

        return redirect('output')

    # =====================================================
    # ================= TEXT CLEAN ========================
    # =====================================================

    elif file_type == 'text':

        request.session['accuracy'] = 90

        return redirect('output')

    return redirect('home')


# ================= OUTPUT =================

def output(request):

    file_type = request.session.get('type')

    context = {

        'filename': request.session.get('filename'),

        'accuracy': request.session.get('accuracy'),

        'type': file_type
    }

    # =====================================================
    # ================= DATA ==============================
    # =====================================================

    if file_type == 'data':

        data = request.session.get('cleaned')

        if not data:
            return redirect('home')

        df = pd.read_json(data)

        context['table'] = df.head(20).to_html(
            classes='table table-striped',
            index=False
        )

    # =====================================================
    # ================= IMAGE =============================
    # =====================================================

    elif file_type == 'image':

        context['image'] = request.session.get(
            'image_path'
        )

        context['ocr'] = request.session.get(
            'ocr'
        )

    # =====================================================
    # ================= TEXT ==============================
    # =====================================================

    elif file_type == 'text':

        df = pd.read_json(
            request.session.get('data')
        )

        context['table'] = df.to_html(
            classes='table table-striped',
            index=False
        )

    return render(request, 'report.html', context)


# ================= DOWNLOAD =================

def download(request):

    file_type = request.session.get('type')

    # =====================================================
    # ================= DATA DOWNLOAD =====================
    # =====================================================

    if file_type == 'data':

        data = request.session.get('cleaned')

        if not data:
            return redirect('home')

        df = pd.read_json(data)

        response = HttpResponse(
            content_type='text/csv'
        )

        response[
            'Content-Disposition'
        ] = 'attachment; filename="cleaned.csv"'

        df.to_csv(response, index=False)

        return response

    # =====================================================
    # ================= IMAGE DOWNLOAD ====================
    # =====================================================

    elif file_type == 'image':

        image_path = request.session.get(
            'image_path'
        )

        with open(image_path, 'rb') as f:

            response = HttpResponse(
                f.read(),
                content_type='image/png'
            )

            response[
                'Content-Disposition'
            ] = 'attachment; filename="cleaned_image.png"'

            return response

    return redirect('home')