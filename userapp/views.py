from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User, auth

def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        checkpassword = request.POST.get("checkpassword", "")

        if not username or not password or not checkpassword:
            messages.warning(request, "กรุณากรอกข้อมูลให้ครบ")
            return redirect(reverse('register'))
        
        if password != checkpassword:
            messages.warning(request, "รหัสผ่านไม่ตรงกัน")
            return redirect(reverse('register'))

        if User.objects.filter(username=username).exists():
            messages.warning(request, "ชื่อผู้ใช้ มีคนใช้งานแล้ว")
            return redirect(reverse('register'))

        user = User.objects.create_user(username=username, password=password)
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
            messages.warning(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            return redirect(reverse('login'))
    else:
        return render(request, "login.html")

def logout(request):
    auth.logout(request)
    return redirect(reverse('login'))