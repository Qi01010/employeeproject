from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User, auth

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        checkpassword = request.POST["checkpassword"]

        if username == "" or password == "" or checkpassword == "":
            messages.warning(request, "กรุณากรอกข้อมูลให้ครบ")
            return redirect(reverse('register'))
        else:
            if password == checkpassword:
                if User.objects.filter(username=username).exists():
                    messages.warning(request, "ชื่อผู้ใช้ มีคนใช้งานแล้ว")
                    return redirect(reverse('register'))
                else:
                    user = User.objects.create_user(
                        username=username,
                        password=password
                    )
                    user.save()
                    messages.success(request, "สร้างบัญชีผู้ใช้เรียบร้อย")
                    return redirect(reverse('login'))
            else:
                messages.warning(request, "รหัสผ่านไม่ตรงกัน")
                return redirect(reverse('register'))
    else:
        return render(request, "register.html")

def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        if username == "" or password == "":
            messages.warning(request, "กรุณากรอกข้อมูลให้ครบ")
            return redirect(reverse('login'))
        else:
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect('/')
            else:
                messages.warning(request, "ไม่มีบัญชีในระบบ หรือรหัสผ่านไม่ถูกต้อง")
                return redirect(reverse('login'))
    else:
        return render(request, "login.html")

def logout(request):
    auth.logout(request)
    return redirect(reverse('login'))