from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.home),
    path("signup/", views.create_user, name="create user"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("create-company/", views.create_company, name="create company"),
    path("choose-company/", views.check_company_user_wants_users_have_many_companies, name="check companies"),
    path("create-employee/", views.create_employee, name="create employee"),
    path("change-role/", views.change_role, name="change role"),
    path("change-company/", views.onbord_exisitng_employee_to_new_company, name="change companies"),
    path("create-employees-txt/", views.create_bulk_employee_from_txt, name="create employees from txt"),
    path("create-employees-csv/", views.create_bulk_employee_from_csv, name="create employees from csv"),
    path("create-employees-excel/", views.create_bulk_employee_from_excel, name="create employees from exel"),
    path("create-companies-txt/", views.create_bulk_companies_from_txt, name="create companies from txt"),
    path("create-companies-csv/", views.create_bulk_companies_from_csv, name="create companies from csv"),
    path("create-companies-excel/", views.create_bulk_companies_from_excel, name="create companies from excel"),
    path("associate-user-with-company/", views.associate_bulk_created_companies_with_company_users, name="associate user with company"),
    path("search-employees/", views.search_employees, name="search employees"),
    path("change-password/", views.change_password, name="change password"),
    path("upload/", views.upload),

]