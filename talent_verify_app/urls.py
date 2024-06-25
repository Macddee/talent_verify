from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home),
    path("signup/", views.create_user, name="create user"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="login"),
    path("create-company/", views.create_company, name="create company"),
    path("choose-company/", views.check_company_user_wants_users_have_many_companies, name="check companies"),
    path("create-employee/", views.create_employee, name="create employee"),
    path("change-role/", views.change_role, name="change role"),
    path("change-company/", views.onbord_exisitng_employee_to_new_company, name="change companies"),
    path("create-employee-txt/", views.create_bulk_employee_from_txt, name="create employees from txt")

]