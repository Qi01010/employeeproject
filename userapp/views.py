from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        checkpassword = request.POST.get("checkpassword", "")

        if not fullname or not email or not password or not checkpassword:
            messages.warning(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
            return redirect(reverse('register'))
        
        if len(password) < 8:
            messages.warning(request, "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
            return redirect(reverse('register'))

        if password != checkpassword:
            messages.warning(request, "รหัสผ่านไม่ตรงกัน")
            return redirect(reverse('register'))

        if User.objects.filter(username=fullname).exists():
            messages.warning(request, "ชื่อ - นามสกุล นี้มีในระบบแล้ว")
            return redirect(reverse('register'))

        name_parts = fullname.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=fullname,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.save()
        messages.success(request, "สร้างบัญชีผู้ใช้เรียบร้อยแล้ว กรุณาเข้าสู่ระบบ")
        return redirect(reverse('login'))
    else:
        return render(request, "register.html")

def login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.warning(request, "กรุณากรอกข้อมูลให้ครบ")
            return redirect(reverse('login'))

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect(reverse('index'))
        else:
            messages.warning(request, "ชื่อ - นามสกุล หรือรหัสผ่านไม่ถูกต้อง")
            return redirect(reverse('login'))
    else:
        return render(request, "login.html")

def logout(request):
    auth.logout(request)
    return redirect(reverse('login'))

@login_required(login_url='login')
def profile(request):
    return render(request, 'profile.html')

@login_required(login_url='login')
def edit_profile(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        messages.success(request, "อัปเดตข้อมูลโปรไฟล์เรียบร้อยแล้ว")
        return redirect('profile')
    else:
        return render(request, 'edit_profile.html')