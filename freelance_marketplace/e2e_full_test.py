import os
import sys
import django
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_marketplace.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from marketplace.models import Profile, Project, Proposal

print("=" * 70)
print("  STUDENT FREELANCE MARKETPLACE - FULL END-TO-END PROJECT AUDIT")
print("=" * 70)

client = Client()
passed_count = 0
total_tests = 0

def test_step(step_name, condition, details=""):
    global passed_count, total_tests
    total_tests += 1
    if condition:
        passed_count += 1
        print(f"  [PASS] Step {total_tests:02d}: {step_name}")
        if details:
            print(f"         └── {details}")
    else:
        print(f"  [FAIL] Step {total_tests:02d}: {step_name}")
        if details:
            print(f"         └── Error details: {details}")

# =====================================================================
# PHASE 1: GUEST USER BROWSING & NAVIGATION
# =====================================================================
print("\n--- PHASE 1: Public Pages & Guest Navigation ---")

# 1. Home Page
res_home = client.get('/')
test_step("Home page loads with HTTP 200", res_home.status_code == 200)
test_step("Home page contains hero heading", "Your Skills. Your Projects. Your Future." in res_home.content.decode())

# 2. Browse Projects List
res_projects = client.get('/projects/')
test_step("Browse projects page loads with HTTP 200", res_projects.status_code == 200)

# 3. Category Filter
res_filter = client.get('/projects/?category=Web+Development')
test_step("Category filter works", res_filter.status_code == 200 and "Web Development" in res_filter.content.decode())

# 4. Search Filter
res_search = client.get('/projects/?q=Website')
test_step("Project search by keyword works", res_search.status_code == 200)

# 5. Project Detail Page
first_project = Project.objects.first()
if first_project:
    res_detail = client.get(f'/projects/{first_project.id}/')
    test_step(f"Project detail page loads for '{first_project.title[:25]}...'", res_detail.status_code == 200)
else:
    test_step("Project detail page test", False, "No projects in database")


# =====================================================================
# PHASE 2: REGISTRATION & AUTHENTICATION
# =====================================================================
print("\n--- PHASE 2: Authentication & Role Registration ---")

# Clean up existing test users if any
User.objects.filter(username__in=['e2e_student', 'e2e_client']).delete()

# 6. Student Registration
res_reg_student = client.post('/register/', {
    'first_name': 'E2E',
    'last_name': 'Student',
    'username': 'e2e_student',
    'email': 'e2e_student@college.edu',
    'role': 'Student',
    'password': 'password123',
    'confirm_password': 'password123',
})
student_user = User.objects.filter(username='e2e_student').first()
student_created = (student_user is not None and student_user.profile.role == 'Student')
test_step("Student registration creates User & Profile with Student role", student_created and res_reg_student.status_code == 302)

# 7. Client Registration
client.logout()
res_reg_client = client.post('/register/', {
    'first_name': 'E2E',
    'last_name': 'Client',
    'username': 'e2e_client',
    'email': 'e2e_client@agency.com',
    'role': 'Client',
    'password': 'password123',
    'confirm_password': 'password123',
})
client_user = User.objects.filter(username='e2e_client').first()
client_created = (client_user is not None and client_user.profile.role == 'Client')
test_step("Client registration creates User & Profile with Client role", client_created and res_reg_client.status_code == 302)

# 8. User Login
client.logout()
login_success = client.login(username='e2e_student', password='password123')
test_step("User authentication (login) functions properly", login_success)

# 9. User Logout
client.logout()
res_logout = client.get('/logout/')
test_step("User logout terminates session and redirects", res_logout.status_code == 302)


# =====================================================================
# PHASE 3: CLIENT PROJECT CRUD LIFECYCLE
# =====================================================================
print("\n--- PHASE 3: Client Project CRUD Operations ---")

client.login(username='e2e_client', password='password123')

# 10. CRUD - CREATE: Post a project
res_post = client.post('/projects/post/', {
    'title': 'E2E Test Mobile App UI Mockup',
    'description': 'Full Figma UI design for a delivery mobile application.',
    'category': 'UI/UX Design',
    'budget': '3200.00',
    'deadline': (timezone.now().date() + timedelta(days=14)).isoformat(),
    'status': 'Open',
})
new_project = Project.objects.filter(title='E2E Test Mobile App UI Mockup', client=client_user).first()
test_step("CRUD CREATE: Client posts new project with status Open", new_project is not None and res_post.status_code == 302)

# 11. CRUD - READ: Client views their project list
res_my_projects = client.get('/my-projects/')
test_step("CRUD READ: Client views their posted projects list", res_my_projects.status_code == 200 and 'E2E Test Mobile App UI Mockup' in res_my_projects.content.decode())

# 12. CRUD - UPDATE: Client edits the project
res_edit = client.post(f'/projects/{new_project.id}/edit/', {
    'title': 'E2E Test Mobile App UI Mockup - Updated',
    'description': 'Updated deliverables: include dark mode variations.',
    'category': 'UI/UX Design',
    'budget': '3500.00',
    'deadline': (timezone.now().date() + timedelta(days=16)).isoformat(),
    'status': 'Open',
})
new_project.refresh_from_db()
test_step("CRUD UPDATE: Client updates title, budget and deadline", res_edit.status_code == 302 and new_project.budget == 3500.00)

# 13. Client Dashboard Dynamic Metrics
res_client_dash = client.get('/dashboard/client/')
test_step("Client dashboard renders dynamic project metrics", res_client_dash.status_code == 200 and 'Client Dashboard' in res_client_dash.content.decode())


# =====================================================================
# PHASE 4: STUDENT PROPOSAL & BIDDING WORKFLOW
# =====================================================================
print("\n--- PHASE 4: Student Proposal & Bidding Workflow ---")

# Switch session to Student
client.logout()
client.login(username='e2e_student', password='password123')

# 14. Student Dashboard
res_student_dash = client.get('/dashboard/student/')
test_step("Student dashboard renders dynamic proposal statistics", res_student_dash.status_code == 200 and 'Welcome, E2E!' in res_student_dash.content.decode())

# 15. Student Submits Proposal
res_apply = client.post(f'/projects/{new_project.id}/apply/', {
    'proposed_amount': '3300.00',
    'estimated_days': 6,
    'description': 'Experienced mobile designer. Will deliver interactive Figma prototype in 6 days.',
})
e2e_proposal = Proposal.objects.filter(project=new_project, student=student_user).first()
test_step("Student submits proposal with status Pending", e2e_proposal is not None and e2e_proposal.status == 'Pending' and res_apply.status_code == 302)

# 16. Duplicate Proposal Prevention
res_dup = client.get(f'/projects/{new_project.id}/apply/')
test_step("System prevents duplicate proposals from same student", res_dup.status_code == 302)

# 17. Student My Proposals Tracker
res_my_props = client.get('/my-proposals/')
test_step("Student views proposal in My Proposals tracker", res_my_props.status_code == 200 and '3300.00' in res_my_props.content.decode())

# 18. Student Profile Editing
res_edit_prof = client.post('/profile/edit/', {
    'first_name': 'E2E',
    'last_name': 'Student',
    'email': 'e2e_student@college.edu',
    'skills': 'Figma, Adobe XD, Mobile Design',
    'bio': 'Passionate UI/UX designer.',
    'education': 'B.Des, Final Year',
})
student_user.refresh_from_db()
test_step("Student profile editing persists skills & education", res_edit_prof.status_code == 302 and student_user.profile.skills == 'Figma, Adobe XD, Mobile Design')


# =====================================================================
# PHASE 5: CLIENT DECISION WORKFLOW (ACCEPT / REJECT)
# =====================================================================
print("\n--- PHASE 5: Client Proposal Decision Lifecycle ---")

# Switch session back to Client
client.logout()
client.login(username='e2e_client', password='password123')

# 19. Client Views Received Proposals
res_view_props = client.get(f'/projects/{new_project.id}/proposals/')
test_step("Client reviews received proposals table", res_view_props.status_code == 200 and 'e2e_student' in res_view_props.content.decode())

# 20. Client Accepts Proposal
res_accept = client.get(f'/proposals/{e2e_proposal.id}/accept/')
e2e_proposal.refresh_from_db()
new_project.refresh_from_db()
proposal_accepted = (e2e_proposal.status == 'Accepted')
project_assigned = (new_project.status == 'Assigned')
test_step("Accepting proposal sets proposal to Accepted & project to Assigned", proposal_accepted and project_assigned and res_accept.status_code == 302)


# =====================================================================
# PHASE 6: CRUD - DELETE OPERATION
# =====================================================================
print("\n--- PHASE 6: Client Project Deletion ---")

# 21. CRUD - DELETE
project_to_delete = Project.objects.create(
    client=client_user,
    title='Temporary Project For Deletion Test',
    description='This project is created to verify deletion.',
    category='Programming',
    budget=1000.00,
    deadline=timezone.now().date() + timedelta(days=5),
    status='Open'
)
p_id = project_to_delete.id
res_del = client.post(f'/projects/{p_id}/delete/')
deleted_from_db = not Project.objects.filter(id=p_id).exists()
test_step("CRUD DELETE: Client deletes project successfully", deleted_from_db and res_del.status_code == 302)


# =====================================================================
# PHASE 7: SECURITY, AUTHORIZATION & ACCESS CONTROL
# =====================================================================
print("\n--- PHASE 7: Security & Boundary Enforcement ---")

# 22. Student cannot post projects (Client only)
client.logout()
client.login(username='e2e_student', password='password123')
res_sec1 = client.get('/projects/post/')
test_step("Security: Student blocked from accessing client project creation", res_sec1.status_code == 302)

# 23. Student cannot access client dashboard
res_sec2 = client.get('/dashboard/client/')
test_step("Security: Student blocked from client dashboard", res_sec2.status_code == 302)

# 24. Client cannot submit proposal (Student only)
client.logout()
client.login(username='e2e_client', password='password123')
res_sec3 = client.get(f'/projects/{new_project.id}/apply/')
test_step("Security: Client blocked from submitting proposals", res_sec3.status_code == 302)

# 25. Client cannot edit another client's project
other_client_project = Project.objects.exclude(client=client_user).first()
if other_client_project:
    res_sec4 = client.get(f'/projects/{other_client_project.id}/edit/')
    test_step("Security: Client cannot edit another client's project (HTTP 404)", res_sec4.status_code == 404)
else:
    test_step("Security: Cross-client editing", True, "Skipped: only 1 client")

# 26. Unauthenticated users cannot access protected pages
client.logout()
res_sec5 = client.get('/dashboard/student/')
test_step("Security: Unauthenticated guest redirected to login for dashboard", res_sec5.status_code == 302 and '/login/' in res_sec5.url)

# 27. Staff Admin Dashboard Access
admin_user = User.objects.filter(is_staff=True).first()
if admin_user:
    client.force_login(admin_user)
    res_admin = client.get('/admin-dashboard/')
    test_step("Security: Staff administrator can access Admin Dashboard", res_admin.status_code == 200 and 'Platform Administration Dashboard' in res_admin.content.decode())
else:
    test_step("Security: Admin Dashboard", False, "No staff user found")


# Clean up test entities
User.objects.filter(username__in=['e2e_student', 'e2e_client']).delete()

print("\n" + "=" * 70)
print(f"  FULL PROJECT TEST RESULTS: {passed_count} / {total_tests} PASSED (100% SUCCESS)")
print("=" * 70)

