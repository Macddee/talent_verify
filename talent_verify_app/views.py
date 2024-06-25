from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from django.contrib.auth import login, logout,authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
from django.forms import model_to_dict
import secrets
import string
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.db.models import F



#HELPER FUNCTIONS
def check_user_type(user):
    print(f"Checking user type for user {user.username}")
    print(f"User has company attribute: {hasattr(user, 'company')}")
    print(f"User has employee attribute: {hasattr(user, 'employee')}")

    is_company = hasattr(user, 'company')
    is_employee = hasattr(user, 'employee')

    if is_company:
        return "Company"
    elif is_employee:
        return "Employee"
    else:
        return "User"

the_list  = []

def generate_user(name=None, surname=None, email=None, username=None, passw=None, batch_item=None):

    #check if user creation call is for creating an employee or a company user

    if username:
        # potential company users provide their own username so its not non
        uname = username
        password = passw

    elif name:
        # employee users have their usernames automatically gebnerated so username will be none
        
        uname = ".".join([name, surname]).lower()
        uname = "@".join([uname, "tv"])

        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(10))
    
    else:
        # we are batch processing  and will automatically generate an employee but eith data from a file

        uname = ".".join(batch_item["name"], batch_item["surname"]).lower()
        uname = "@".join([uname, "tv"])

        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(10))

    try:
        user = User(username=uname.strip(), email=email, first_name=name, last_name=surname)
        user.set_password(password)
        user.full_clean()
        user.save()

    except ValidationError as e:
        return e.message_dict
    
    except IntegrityError as e:
        if 'unique constraint' in str(e) and 'username' in str(e):
            return {"content": "A user with this username already exists."}
        else:
            return {"error": str(e)}
        
    else:
        return user
    
    

def create_or_change_role(current_role=None, new_role=None, batch_item=None, employee=None, company=None):

    #this we creating  a new employee with new roles assigned to em
    if current_role is not None:
        
        duties = current_role[0].split(",") #. #strip()
        processed_role = RoleHistory(
            role = current_role[1],
            date_started = current_role[2],
            date_left = current_role[3],
            employee = current_role[4],
            company = current_role[5],
        )

    #this means that we are its an employee that has beenassigned a role aleady and is changing within the company
    elif new_role:
        duties = new_role[0].split(",") #. #strip()
        processed_role = RoleHistory(
            role = new_role[1],
            date_started = new_role[2],
            date_left = new_role[3],
            employee = new_role[4],
            company = new_role[5],
        )
    # this means we are doing a bulk upload and we     
    else:
        duties = batch_item["duties_csv"].split(",") #. #strip()
        processed_role = RoleHistory(
            role = batch_item["role"],
            date_started = batch_item["date_started"],
            date_left = batch_item["date_left"],
            employee = employee,
            company = company,

        )



    try:
        
        processed_role.full_clean()
        processed_role.save()

    except ValidationError as e:
        return Response({"content": e.error_dict})

    except IntegrityError as e:
        return Response({"error": str(e)})

    # now to associate the duties in the duty table with the duties provided.
    # this will check if a duty is already there or add the new duty to the table if otherwise


    if duties:
        for duty in duties:
            role_duty, result = DutyRole.objects.get_or_create(duty_in_role=duty)

            processed_role.duties.add(role_duty)

        role_hist_serializer = RoleHistorySerializer(processed_role)
        role_hist_response_obj = (role_hist_serializer.data, {"saved employee has duties": "True"})
        return role_hist_response_obj

    else: 
        role_hist_serializer = RoleHistorySerializer(processed_role)
        role_hist_response_obj(role_hist_serializer.data, {"saved employee has duties": "False"})
        return role_hist_response_obj


def create_to_the_employee_table(id_number=None, company=None, generated_employee=None, departments_csv=None, batch_item=None):
    id_number = ""
    departments_csv = ""


 #write data to the Employee table

    if batch_item:
        #the case where the users are being created in bulk
        id_number = batch_item["id_number"]
        departments_csv = batch_item["departments_csv"]

  
    #if not provided then its the case where users are being created normaly, one at a time       

    try:
        proccesed_employee = Employee(
        id_number=id_number,
        company=company,
        user=generated_employee
        )
        proccesed_employee.full_clean()
        proccesed_employee.save()

    except ValidationError as e:
        return Response({"content": e.error_dict})
    
    except IntegrityError as e:
        return Response({"error": str(e)})
    
    # update the number of employees field in the company table with the addition of the extra 1 employee
    company_update = Company.objects.get(name=company)
    company_update.number_of_employees = F("number_of_employees") + 1
    company_update.save()


    #writing to the departments table
    departments = departments_csv.split(",")
    non_existing_departments = []
    existing_departments = []
    non_existing_departments_response = {}
    dpt_response_obj = []
   
    if departments:
        for dept in departments:
            try:
                employee_dept = Departments.objects.get(
                    department = dept
                )
            
                #associate the daprtmant with the current employee
                proccesed_employee.department.add(employee_dept)
                existing_departments.append(dept) 
        
            #capture all non existing deps to report to the company
            except Departments.DoesNotExist:
                non_existing_departments.append(dept)

        if non_existing_departments:
            non_existing_departments_response = {"non existing company departments": non_existing_departments}
            emp_serializer = EmployeeSerializer(proccesed_employee)
            dpt_response_obj = (emp_serializer.data, {"saved employee departments": existing_departments})
            
        else:
            emp_serializer = EmployeeSerializer(proccesed_employee)
            dpt_response_obj = (emp_serializer.data, {"saved employee has departments": "True"})
    else:
        emp_serializer = EmployeeSerializer(proccesed_employee)
        dpt_response_obj(emp_serializer.data, {"saved employee has departments": "False"})

    return[
            dpt_response_obj[0], #seperated so i dont work with lists in lists in the create_employee view
            dpt_response_obj[1],
            non_existing_departments_response,
            proccesed_employee,
        ]





# API METHODS

def home(request):
    pass


#create company USUER also the admin for the company in question
@api_view(["GET","POST"])
def create_user(request):
    if request.method == "GET":
        return Response([
            {"content": "only company users(admins) are allowed to explicitly create accounts here"},
            {"content": "to avoid emloyees from creting personal accounts, all accounts will be deleted within 5 days if they not associated to a company"},
            
    ])

    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")
    name = request.data.get("name")
    surname = request.data.get("surname")

    # user = User.objects.create_user(username=username, password=password, email=email, first_name=name, last_name=surname)
    # return Response("sucess")

    # check if the returned employee is an instance of user. or retturn the the exception  
    user = generate_user(name,surname,email,username, password)
   
    if not isinstance(user, User):
        return Response(user)
    
    #lohout any logged in user to avoid not mix companies if the user has been gen
    logout(request)

    user_data = {
        "username": user.username,
        "email": user.email
    }
    
    return Response(user_data, status=status.HTTP_201_CREATED,)



@api_view(["POST"])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)
    print(user)

    if user is not None:
        login(request, user)
        return Response({"message": "User logged in successfully"}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def logout_user(request):
    logout(request)
    return Response({"message": "User logged out successfully!"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def create_company(request): 
    user = request.user
    name = request.data.get("name")
    registration_date = request.data.get("registration_date")
    registration_number = request.data.get("registration_number")
    address = request.data.get("address")
    contact_person = request.data.get("contact_person")
    number_of_employees = request.data.get("number_of_employees")
    contact_phone = request.data.get("contact_phone")
    email_address = request.data.get("email_address")
    department_csv = request.data.get("department_csv")

    if request.user.is_authenticated:
        try: 
            processed_company = Company(
                user                = user,           
                name                = name,   
                registration_date   = registration_date,  
                registration_number = registration_number,    
                address             = address,    
                contact_person      = contact_person, 
                number_of_employees = number_of_employees,    
                contact_phone       = contact_phone,  
                email_address       = email_address,
            )
            processed_company.full_clean()
            processed_company.save()

        except ValidationError as e:
            return Response({"content": e.error_dict})
        
        except IntegrityError as e:
            return Response({"error": str(e)})

        # now to check if a department already exists and add if its not already there.
        departments = department_csv.split(",")
        
        if departments:
            for departnment_name in departments:
                departnment_name = departnment_name.strip()#.title()

                department, created = Departments.objects.get_or_create(department=departnment_name)

                processed_company.department.add(department)

            processed_company_serializer = CompanySerializer(processed_company)
            return Response({
                "data": processed_company_serializer.data,
                "saved company has departments": "True"
            },
            status=status.HTTP_201_CREATED
            )
        
        else:
            processed_company_serializer = CompanySerializer(processed_company)
            return Response({"saved company has departments": "False",
                             "data": processed_company_serializer.data
                            },
                            status=status.HTTP_201_CREATED
                            )

    return Response({"content": "Please login first before creacting a company"}, status=status.HTTP_401_UNAUTHORIZED)


#pre requesits for creating an employee. (associating an employee with the company of the admmin thats creating the eployeee)
#we cant just say user.company because the user can have many companies. so we have to store the company they login as
# endpoind to be called directly after login
@api_view(["GET", "POST"])
def check_company_user_wants_users_have_many_companies(request):
    if request.method == "GET":
        #check if the user is part of many companies and return the one with the name thats sent
        try:
            company_names = [company['name'] for company in request.user.company.values('name')]
            
            if len(company_names) > 1:
                return Response({"content": "choose the company you want to login as",
                                 "user": request.user.username,
                                "data": company_names},
                                status=status.HTTP_302_FOUND
                                )
            else:
                return Response({"content":"User only associated to one company."}, status=status.HTTP_204_NO_CONTENT)
        except:
                return Response({"content":"You are not associated to any company. Please create one"}, status=status.HTTP_204_NO_CONTENT)

    
    # return only the company that he selects.
    elif request.method == "POST":
        company_logged_in_as = Company.objects.filter(name=request.data.get("selected_company")).first()
        
        #put the chosen company in a session variable so that we can look for the compnay when creating an employee
        request.session['company_logged_in_as'] = company_logged_in_as.name
       
        company_logged_in_as_serializer = CompanySerializer(company_logged_in_as)
        return Response(company_logged_in_as_serializer.data)


@api_view(["POST"])
def create_employee(request):
    departments_csv = request.data.get("departments_csv")

    name = request.data.get("name")
    surname= request.data.get("surname")
    id_number = request.data.get("id_number")
    email = request.data.get("email")
    company = Company.objects.filter(name=request.session.get("company_logged_in_as")).first()

    #role information same employee
    duties_csv =  request.data.get("duties_csv")
    role = request.data.get("role")
    date_started = request.data.get("date_started")
    date_left = request.data.get("date_left")
    
    
    with transaction.atomic():
        # check if the returned employee is an instance of user. or retturn the the exception  
        generated_employee = generate_user(name, surname, email)

        if not isinstance(generated_employee, User):
            return Response(generated_employee)
            

        if request.user.is_authenticated:
            if check_user_type(request.user) == "Company" and company is not None:

                #create employee contains 4 items, the first 3 are strings the details of created deptatments, and not found departments 
                #the 4th items is the processed employee which is required in the role table by the create or update role function
                # this is an instance of the useer saved in the employee table. NOT THE GENERATED ONE
                create_employee_response_obj = create_to_the_employee_table(id_number,company,generated_employee,departments_csv)


                #pass the role creation or changing function a list of the new values
                current_role = [duties_csv,
                                role,
                                date_started,
                                date_left,
                                create_employee_response_obj[3], # the proccesed employee, is required to associate the role with the employee 
                                company,
                                ]


                #getting the response object from the create or update role seperated from create_employee
                #because this one can also update roles, which is not creating employees
                role_hist_response_obj = create_or_change_role(current_role)


                #extra if to remove the {} in case all dpartmns are present in a company
                if create_employee_response_obj[2]:
                    return Response([
                        {"employee created": "True"},
                        create_employee_response_obj[0],
                        create_employee_response_obj[1],
                        create_employee_response_obj[2],
                        role_hist_response_obj[1],
                        role_hist_response_obj[0],
                        ],
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response([
                        {"employee created": "True"},
                        create_employee_response_obj[0],
                        create_employee_response_obj[1],
                        role_hist_response_obj[1],
                        role_hist_response_obj[0],
                        ],
                        status=status.HTTP_200_OK
                    )
    
            else:
                return Response([
                    {"content": "User is not a company user"},
                    {"content": "you might want to visit the endpoind check company or create a company"}
                    ],
                    status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"content": "Please login to create an employee"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["GET"])
def create_bulk_employee_from_txt(request):
    from . import data_models as dm
    if request.user.is_authenticated:
        company = request.session.get("company_logged_in_as")
        if company:
            with transaction.atomic():
                log = dm.save_to_db(company)

                return Response(log, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def change_role(request):
    
    duties_csv =  request.data.get("duties_csv")
    role = request.data.get("role")
    date_started = request.data.get("date_started")
    date_left = request.data.get("date_left")
    username = request.data.get("username")

    if date_left is None:
        return Response({"content": "The date left field is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    new_company = Company.objects.filter(name=request.session.get("company_logged_in_as")).first()

    processed_employee = get_object_or_404(
        Employee,
        user__username = username
    )

    #pass the role creation or changing function a list of the new values
    new_role=[duties_csv,
              role,
              date_started,
              date_left,
              processed_employee,
              new_company.name,
              ]
    
    new_role_response_obj = create_or_change_role(new_role)

    return Response(new_role_response_obj)


@api_view(["POST"])
def onbord_exisitng_employee_to_new_company(request):
    new_company = request.session.get("company_logged_in_as")
    username = request.data.get("username")
    departments = request.data.get("departments_csv")
    departments_csv = departments.split(",")

    user_employee_to_update = get_object_or_404(
        Employee,
        user__username=username
    )

    print(user_employee_to_update)

    if check_user_type(user_employee_to_update.user) == "Employee":
        return Response({"content": "You are not a company use"}, status=status.HTTP_401_UNAUTHORIZED)

    new_company = Company.objects.get(name=new_company)

    #update the number of emloyees from the old company
    old_company= Company.objects.filter(name=user_employee_to_update.company.name).first()
    old_company.number_of_employees = int(old_company.number_of_employees) - 1
    old_company.save()

    user_employee_to_update = Employee.objects.filter(user__username=username).first()

    #write to the company history table
    EmployeeCompanyHistory.objects.create(
        company=new_company,
        employee=user_employee_to_update
    )

    #update the employee table to point to the new company
    user_employee_to_update.company=new_company
    
    #add new deps(if any) and associate the deps to the user being updated
    for dept in departments_csv:
        print(dept)
        procced_dpt, created = Departments.objects.get_or_create(department = dept)

        user_employee_to_update.department.add(procced_dpt)
    
    user_employee_to_update.save()

    user_employee_to_update_serializer = EmployeeSerializer(user_employee_to_update)

    return Response(user_employee_to_update_serializer.data, status=status.HTTP_200_OK)

